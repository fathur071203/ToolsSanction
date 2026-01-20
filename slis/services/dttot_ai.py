from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


DTTOT_SOURCE = "DTTOT/NYDA RI KEPOLISIAN"


@dataclass(frozen=True)
class DttotAiResult:
    token: str
    pdf_path: Path
    raw_text_path: Path
    result_json_path: Path
    created_at: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _private_upload_dir() -> Path:
    return (_repo_root() / "data" / "private_uploads" / "dttot").resolve()


def _ai_jobs_dir() -> Path:
    return (_repo_root() / "data" / "ai_jobs" / "dttot").resolve()


def _ensure_dirs() -> None:
    _private_upload_dir().mkdir(parents=True, exist_ok=True)
    _ai_jobs_dir().mkdir(parents=True, exist_ok=True)


def extract_pdf_text(pdf_path: Path, max_pages: int | None = None) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PDF parser belum tersedia. Install dependency: pip install pypdf"
        ) from e

    reader = PdfReader(str(pdf_path))
    texts: List[str] = []
    pages = reader.pages
    if max_pages is not None:
        pages = pages[:max_pages]

    for i, page in enumerate(pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            texts.append(f"\n\n--- PAGE {i+1} ---\n" + t)

    return "\n".join(texts).strip()


def _chunk_text(text: str, max_chars: int = 12000) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0

    # split by page markers / blank lines to keep coherence
    parts = re.split(r"\n\s*\n", text)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        add_len = len(p) + 2
        if cur and cur_len + add_len > max_chars:
            chunks.append("\n\n".join(cur))
            cur = [p]
            cur_len = len(p)
        else:
            cur.append(p)
            cur_len += add_len

    if cur:
        chunks.append("\n\n".join(cur))

    return chunks


def _openai_request_json(system_prompt: str, user_prompt: str) -> tuple[str, dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY belum diset")
    if not model:
        raise RuntimeError("OPENAI_MODEL belum diset")

    # Use Responses API (preferred)
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"OpenAI API error {r.status_code}: {r.text[:4000]}")

    data = r.json()

    # Extract text from Responses API output
    # Many variants exist; handle common one.
    output_text = ""
    for item in data.get("output", []) or []:
        for c in item.get("content", []) or []:
            if c.get("type") in {"output_text", "text"}:
                output_text += c.get("text", "")

    output_text = output_text.strip()
    if not output_text:
        # fallback: sometimes API returns `output_text` top-level
        output_text = (data.get("output_text") or "").strip()

    if not output_text:
        raise RuntimeError("OpenAI output kosong")

    return output_text, data


def _extract_json_array(text: str) -> str:
    """Best-effort extraction of a JSON array from free-form text."""
    t = (text or "").strip()
    if not t:
        raise RuntimeError("Model output kosong")

    # Remove ```json fences
    if "```" in t:
        t = re.sub(r"^```(?:json)?\s*", "", t.strip(), flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t.strip())

    # If already starts with [ assume it's the array
    if t.lstrip().startswith("["):
        return t

    # Try to find first JSON array block
    start = t.find("[")
    end = t.rfind("]")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1].strip()

    # Some models may wrap in {"sanctions": [...]}
    obj_start = t.find("{")
    obj_end = t.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        return t[obj_start : obj_end + 1].strip()

    raise RuntimeError("Tidak menemukan JSON array pada output model")


def normalize_dttot_text_to_rows(raw_text: str) -> List[Dict[str, Any]]:
    system_prompt = (
        "Kamu adalah sistem normalisasi data sanction list.\n\n"
        "ATURAN KERAS:\n"
        "- Jangan menghapus informasi\n"
        "- Jangan menambahkan data baru\n"
        "- Jangan mengubah nama atau isi teks\n"
        "- Jangan meringkas secara bebas\n"
        "- Jika tanggal lahir tidak ada, isi null\n"
        "- Gunakan kode negara ISO (Indonesia = ID)\n"
        "- Output HARUS berupa JSON array\n"
        "- Output HANYA JSON (tanpa penjelasan, tanpa markdown, tanpa ``` )\n"
        "- Struktur HARUS sesuai contoh yang diberikan\n"
    )

    user_prompt = (
        "Ubah data DTTOT berikut ke format sanction list di bawah ini.\n\n"
        "FORMAT TARGET:\n"
        "{\n"
        f"  \"id\": \"\",\n  \"source\": \"{DTTOT_SOURCE}\",\n  \"name\": \"\",\n  \"dob\": null,\n  \"citizenship\": \"\",\n  \"remarks\": \"\"\n"
        "}\n\n"
        "DATA DTTOT:\n<<<\n"
        f"{raw_text}\n"
        ">>>\n"
    )

    out_text, _raw_resp = _openai_request_json(system_prompt, user_prompt)

    extracted = _extract_json_array(out_text)

    try:
        parsed = json.loads(extracted)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model output bukan JSON valid: {e}")

    if isinstance(parsed, dict) and isinstance(parsed.get("sanctions"), list):
        parsed = parsed["sanctions"]

    if not isinstance(parsed, list):
        raise RuntimeError("Model output harus berupa JSON array")

    rows: List[Dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        # Force source to DTTOT (safety)
        item["source"] = DTTOT_SOURCE
        rows.append(item)

    return rows


def normalize_dttot_text_to_rows_with_output(raw_text: str) -> tuple[List[Dict[str, Any]], str]:
    """Same as normalize_dttot_text_to_rows, but also returns raw model output text."""

    system_prompt = (
        "Kamu adalah sistem normalisasi data sanction list.\n\n"
        "ATURAN KERAS:\n"
        "- Jangan menghapus informasi\n"
        "- Jangan menambahkan data baru\n"
        "- Jangan mengubah nama atau isi teks\n"
        "- Jangan meringkas secara bebas\n"
        "- Jika tanggal lahir tidak ada, isi null\n"
        "- Gunakan kode negara ISO (Indonesia = ID)\n"
        "- Output HARUS berupa JSON array\n"
        "- Output HANYA JSON (tanpa penjelasan, tanpa markdown, tanpa ``` )\n"
        "- Struktur HARUS sesuai contoh yang diberikan\n"
    )

    user_prompt = (
        "Ubah data DTTOT berikut ke format sanction list di bawah ini.\n\n"
        "FORMAT TARGET:\n"
        "{\n"
        f"  \"id\": \"\",\n  \"source\": \"{DTTOT_SOURCE}\",\n  \"name\": \"\",\n  \"dob\": null,\n  \"citizenship\": \"\",\n  \"remarks\": \"\"\n"
        "}\n\n"
        "DATA DTTOT:\n<<<\n"
        f"{raw_text}\n"
        ">>>\n"
    )

    out_text, _raw_resp = _openai_request_json(system_prompt, user_prompt)
    extracted = _extract_json_array(out_text)

    try:
        parsed = json.loads(extracted)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model output bukan JSON valid: {e}")

    if isinstance(parsed, dict) and isinstance(parsed.get("sanctions"), list):
        parsed = parsed["sanctions"]

    if not isinstance(parsed, list):
        raise RuntimeError("Model output harus berupa JSON array")

    rows: List[Dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        item["source"] = DTTOT_SOURCE
        rows.append(item)

    return rows, out_text


def run_dttot_ai_job(pdf_bytes: bytes, original_filename: str) -> Tuple[DttotAiResult, List[Dict[str, Any]]]:
    _ensure_dirs()

    token = uuid.uuid4().hex
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    pdf_path = _private_upload_dir() / f"{ts}-{token}-{_safe_name(original_filename)}"
    raw_text_path = _ai_jobs_dir() / f"{ts}-{token}-raw.txt"
    result_json_path = _ai_jobs_dir() / f"{ts}-{token}-result.json"

    pdf_path.write_bytes(pdf_bytes)

    text = extract_pdf_text(pdf_path)
    raw_text_path.write_text(text, encoding="utf-8")

    if not text.strip():
        raise RuntimeError("PDF tidak menghasilkan teks. Coba PDF yang searchable (bukan scan gambar).")

    chunks = _chunk_text(text)
    all_rows: List[Dict[str, Any]] = []

    # Persist raw model outputs per chunk for debugging/audit
    openai_log_path = _ai_jobs_dir() / f"{ts}-{token}-openai_outputs.txt"
    openai_log_parts: List[str] = []

    for idx, ch in enumerate(chunks):
        try:
            rows, out_text = normalize_dttot_text_to_rows_with_output(ch)
            all_rows.extend(rows)
            openai_log_parts.append(f"\n\n=== CHUNK {idx+1} OK ({len(rows)} rows) ===\n")
            openai_log_parts.append(out_text)
        except Exception as e:
            openai_log_parts.append(f"\n\n=== CHUNK {idx+1} ERROR: {type(e).__name__}: {e} ===\n")
            # Continue to next chunk to salvage partial results
            continue

    if openai_log_parts:
        openai_log_path.write_text("".join(openai_log_parts), encoding="utf-8")

    if not all_rows:
        raise RuntimeError("AI tidak menghasilkan record. Coba PDF lain atau periksa format PDF.")

    # basic cleanup/dedupe by (id,name)
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in all_rows:
        rid = str(r.get("id") or "").strip()
        nm = str(r.get("name") or "").strip()
        key = (rid, nm)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    result_json_path.write_text(json.dumps(deduped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    meta = DttotAiResult(
        token=token,
        pdf_path=pdf_path,
        raw_text_path=raw_text_path,
        result_json_path=result_json_path,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return meta, deduped


def load_dttot_ai_result(token: str) -> Tuple[Path, List[Dict[str, Any]]]:
    _ensure_dirs()

    # Find latest matching result file
    matches = sorted(_ai_jobs_dir().glob(f"*-{token}-result.json"))
    if not matches:
        raise FileNotFoundError("Hasil AI tidak ditemukan atau sudah dibersihkan.")

    p = matches[-1]
    rows = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise RuntimeError("Format hasil AI tidak valid")
    return p, rows


def _safe_name(filename: str) -> str:
    filename = (filename or "upload.pdf").strip().replace("/", "_")
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
    return filename[:120] or "upload.pdf"
