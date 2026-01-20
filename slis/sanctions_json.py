from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from slis.matching.names import normalize_name as _normalize_name


@dataclass(frozen=True)
class SanctionRecord:
    external_id: str
    source: str
    name: str
    name_norm: str
    dob_raw: Optional[str]
    citizenship_raw: Optional[str]
    citizenship_norm: str
    extra: Dict[str, Any]


_CACHE: Tuple[float, List[SanctionRecord], Path] | None = None


def _repo_root() -> Path:
    # slis/ -> repo root
    return Path(__file__).resolve().parents[1]


def get_sanctions_json_path() -> Path:
    configured = os.getenv("SLIS_SANCTIONS_JSON_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (_repo_root() / "data" / "sanctions.json").resolve()


def get_sanction_sources_json_path() -> Path:
    configured = os.getenv("SLIS_SANCTION_SOURCES_JSON_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return (_repo_root() / "data" / "sanction_sources.json").resolve()


def read_sanction_sources_json() -> List[str]:
    """Return a sorted list of known sanction sources (optional registry).

    This file is optional; if missing, returns an empty list.
    """
    path = get_sanction_sources_json_path()
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []

    cleaned = []
    seen = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        s = item.strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
    return sorted(cleaned)


def write_sanction_sources_json(sources: List[str]) -> None:
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")

    cleaned = []
    seen = set()
    for item in sources:
        if not isinstance(item, str):
            continue
        s = item.strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)

    path = get_sanction_sources_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(sorted(cleaned), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def load_tabular_sanctions_file(file_obj, filename: str, source: str) -> List[Dict[str, Any]]:
    """Parse CSV/XLSX into sanctions.json row dicts (per-source import).

    Expected columns (case-insensitive; any one alias works):
    - name: name/full_name/nama
    - id: id/external_id/record_id (optional)
    - dob: dob/date_of_birth/tanggal_lahir (optional)
    - citizenship: citizenship/cit/nationality/kewarganegaraan (optional)
    - remarks: remarks/remark/note/catatan (optional)

    Returns list of dicts ready to be merged into sanctions.json.
    """

    if not filename:
        raise ValueError("filename is required")

    name_lower = filename.lower()
    file_obj.seek(0)

    if name_lower.endswith(".csv"):
        df = pd.read_csv(file_obj, dtype=str).fillna("")
    elif name_lower.endswith(".xlsx") or name_lower.endswith(".xls"):
        df = pd.read_excel(file_obj, dtype=str).fillna("")
    else:
        raise ValueError("Unsupported format. Use .csv or .xlsx")

    # map columns by normalized names
    def norm_col(c: str) -> str:
        return "".join(ch.lower() for ch in str(c).strip() if ch.isalnum() or ch in {"_"})

    col_map = {norm_col(c): c for c in df.columns}

    def pick(*aliases: str) -> str | None:
        for a in aliases:
            key = norm_col(a)
            if key in col_map:
                return col_map[key]
        return None

    col_name = pick("name", "full_name", "fullname", "nama", "nama_lengkap", "primary_name")
    if not col_name:
        raise ValueError(
            "Kolom nama tidak ditemukan. Gunakan salah satu: name/full_name/nama"
        )

    col_id = pick("id", "external_id", "record_id")
    col_dob = pick("dob", "date_of_birth", "tanggal_lahir", "tgl_lahir")
    col_cit = pick("citizenship", "cit", "nationality", "kewarganegaraan")
    col_remarks = pick("remarks", "remark", "note", "catatan")

    rows: List[Dict[str, Any]] = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    for i, r in df.iterrows():
        name = str(r.get(col_name, "")).strip()
        if not name:
            continue

        record_id = str(r.get(col_id, "")).strip() if col_id else ""
        if not record_id:
            record_id = f"IMP-{source}-{ts}-{i+1}"

        out: Dict[str, Any] = {
            "id": record_id,
            "source": source,
            "name": name,
        }

        if col_dob:
            dob = str(r.get(col_dob, "")).strip()
            if dob:
                out["dob"] = dob

        if col_cit:
            cit = str(r.get(col_cit, "")).strip()
            if cit:
                out["citizenship"] = cit

        if col_remarks:
            rem = str(r.get(col_remarks, "")).strip()
            if rem:
                out["remarks"] = rem

        rows.append(out)

    return rows


def _as_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        out: List[str] = []
        for v in value:
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out.append(s)
            elif v is not None:
                s = str(v).strip()
                if s:
                    out.append(s)
        return out
    s = str(value).strip()
    return [s] if s else []


def load_json_sanctions_file(file_obj, filename: str, source: str) -> List[Dict[str, Any]]:
    """Parse .json input into sanctions.json rows.

    Supports:
    - JSON array
    - JSON object with key `sanctions` (list)
    - NDJSON (one JSON object per line) like the EU FSF dataset export

    For EU-style objects, maps fields into our minimal schema:
    - id: object.id
    - name: caption OR properties.name[0]
    - dob: properties.birthDate[0] (Person)
    - citizenship: properties.nationality[0] OR properties.country[0]
    - remarks: join(properties.notes)
    Extra fields are preserved under their original keys when useful.
    """

    if not filename:
        raise ValueError("filename is required")

    name_lower = filename.lower()
    if not name_lower.endswith(".json"):
        raise ValueError("Unsupported format. Use .json")

    file_obj.seek(0)
    raw_bytes = file_obj.read()
    if isinstance(raw_bytes, str):
        raw_text = raw_bytes
    else:
        raw_text = raw_bytes.decode("utf-8", errors="replace")

    raw_text = raw_text.strip()
    if not raw_text:
        return []

    items: List[Dict[str, Any]] = []

    # First try normal JSON
    try:
        payload = json.loads(raw_text)
        if isinstance(payload, list):
            items = [x for x in payload if isinstance(x, dict)]
        elif isinstance(payload, dict) and isinstance(payload.get("sanctions"), list):
            items = [x for x in payload["sanctions"] if isinstance(x, dict)]
        elif isinstance(payload, dict):
            items = [payload]
        else:
            items = []
    except json.JSONDecodeError:
        # NDJSON fallback
        for line in raw_text.splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                items.append(obj)

    rows: List[Dict[str, Any]] = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    def _compact_join(parts: List[str], max_len: int = 900) -> str:
        cleaned: List[str] = []
        seen = set()
        for p in parts:
            s = str(p or "").strip()
            if not s:
                continue
            if s in seen:
                continue
            seen.add(s)
            cleaned.append(s)
        out = " | ".join(cleaned)
        if len(out) > max_len:
            out = out[: max_len - 3].rstrip() + "..."
        return out

    for i, obj in enumerate(items):
        # Filter out non-target EU objects (eg Address target=false)
        if "target" in obj and obj.get("target") is False:
            continue

        external_id = str(obj.get("id") or "").strip()
        caption = str(obj.get("caption") or "").strip()
        schema = str(obj.get("schema") or "").strip()

        props = obj.get("properties") if isinstance(obj.get("properties"), dict) else {}
        names = _as_str_list(props.get("name"))
        name = caption or (names[0] if names else "")
        name = name.strip()
        if not name:
            continue

        if not external_id:
            external_id = f"IMPJSON-{source}-{ts}-{i+1}"

        dob = ""
        if isinstance(props, dict):
            birth_dates = _as_str_list(props.get("birthDate"))
            if birth_dates:
                # UNSC often has multiple years; keep them all for matching.
                dob = "; ".join(birth_dates[:5])

        citizenship = ""
        if isinstance(props, dict):
            nat = _as_str_list(props.get("nationality"))
            ctry = _as_str_list(props.get("country"))
            citizenship = (nat[0] if nat else (ctry[0] if ctry else ""))

        notes = _as_str_list(props.get("notes")) if isinstance(props, dict) else []
        aliases = _as_str_list(props.get("alias")) if isinstance(props, dict) else []
        positions = _as_str_list(props.get("position")) if isinstance(props, dict) else []
        addresses = _as_str_list(props.get("address")) if isinstance(props, dict) else []
        birth_places = _as_str_list(props.get("birthPlace")) if isinstance(props, dict) else []
        extra_remarks = _as_str_list(props.get("remarks")) if isinstance(props, dict) else []
        program_ids = _as_str_list(props.get("programId")) if isinstance(props, dict) else []
        source_urls = _as_str_list(props.get("sourceUrl")) if isinstance(props, dict) else []

        remarks_parts: List[str] = []
        remarks_parts.extend(notes[:3])
        remarks_parts.extend(extra_remarks[:2])
        if positions:
            remarks_parts.append(f"position: {positions[0]}")
        if birth_places:
            remarks_parts.append(f"birthPlace: {birth_places[0]}")
        if addresses:
            remarks_parts.append(f"address: {', '.join(addresses[:2])}")
        if aliases:
            remarks_parts.append(f"alias: {', '.join(aliases[:5])}")
        if program_ids:
            remarks_parts.append(f"programId: {program_ids[0]}")
        if source_urls:
            remarks_parts.append(f"sourceUrl: {source_urls[0]}")
        remarks = _compact_join(remarks_parts)

        out: Dict[str, Any] = {
            "id": external_id,
            "source": source,
            "name": name,
        }

        if dob:
            out["dob"] = dob
        if citizenship:
            out["citizenship"] = citizenship
        if remarks:
            out["remarks"] = remarks

        # Preserve extra metadata (useful for audit/debug)
        for k in ("caption", "schema", "referents", "datasets", "first_seen", "last_seen", "last_change", "properties"):
            if k in obj and k not in out:
                out[k] = obj.get(k)

        rows.append(out)

    return rows


def _as_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("sanctions"), list):
        return payload["sanctions"]
    raise ValueError("Sanctions JSON must be a list or an object with key 'sanctions' (list).")


def read_raw_sanctions_json() -> List[Dict[str, Any]]:
    """Read the raw JSON content as list of dicts.

    Accepts either:
    - a JSON list
    - an object with key `sanctions` containing a list
    """
    path = get_sanctions_json_path()
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = _as_list(raw)
    # Normalize to dict-only entries
    out: List[Dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict):
            out.append(item)
    return out


def write_raw_sanctions_json(rows: List[Dict[str, Any]]) -> None:
    """Write sanctions JSON as a list (pretty-printed) with an atomic replace."""
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for i, item in enumerate(rows):
        if not isinstance(item, dict):
            raise ValueError(f"Sanctions entry at index {i} must be an object")

    path = get_sanctions_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def validate_raw_sanctions_json(payload: Any) -> List[Dict[str, Any]]:
    """Validate incoming JSON payload for sanctions editor.

    Returns a normalized list[dict]. Requires each entry to have at least `name` (or `full_name`).
    """
    rows = _as_list(payload)
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(rows):
        if not isinstance(item, dict):
            raise ValueError(f"Entry #{idx+1} must be an object")
        name = (item.get("name") or item.get("full_name") or "").strip()
        if not name:
            raise ValueError(f"Entry #{idx+1} is missing required field 'name'")
        normalized.append(item)
    return normalized


def _norm_country(value: Optional[str]) -> str:
    if not value:
        return ""
    s = str(value).lower().strip()
    # keep alnum only
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
    return "".join(out)


def load_sanctions_json(force_reload: bool = False) -> List[SanctionRecord]:
    """Load sanction records from JSON.

    Source of truth is the JSON file (no DB). Default path is `data/sanctions.json`
    and can be overridden by env var `SLIS_SANCTIONS_JSON_PATH`.

    Cache is based on file mtime to make edits easy without restart.
    """

    global _CACHE

    path = get_sanctions_json_path()
    if not path.exists():
        raise RuntimeError(
            f"Sanctions JSON not found at {path}. "
            "Create it (see data/sanctions.json) or set SLIS_SANCTIONS_JSON_PATH."
        )

    mtime = path.stat().st_mtime
    if not force_reload and _CACHE is not None:
        cached_mtime, cached_records, cached_path = _CACHE
        if cached_path == path and cached_mtime == mtime:
            return cached_records

    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = _as_list(raw)

    records: List[SanctionRecord] = []
    for idx, item in enumerate(rows):
        if not isinstance(item, dict):
            continue

        name = (item.get("name") or item.get("full_name") or "").strip()
        if not name:
            continue

        source = (item.get("source") or item.get("source_code") or "UNKNOWN").strip()
        dob_raw = item.get("dob") or item.get("dob_raw") or item.get("date_of_birth") or item.get("date_of_birth_raw")
        citizenship_raw = item.get("citizenship") or item.get("citizenship_raw")

        external_id = str(item.get("id") or item.get("external_id") or f"ROW-{idx+1}")

        name_norm = _normalize_name(name) or ""
        if not name_norm:
            continue

        extra = {k: v for k, v in item.items() if k not in {
            "id",
            "external_id",
            "source",
            "source_code",
            "name",
            "full_name",
            "dob",
            "dob_raw",
            "date_of_birth",
            "date_of_birth_raw",
            "citizenship",
            "citizenship_raw",
        }}

        records.append(
            SanctionRecord(
                external_id=external_id,
                source=source,
                name=name,
                name_norm=name_norm,
                dob_raw=str(dob_raw).strip() if dob_raw not in (None, "") else None,
                citizenship_raw=str(citizenship_raw).strip() if citizenship_raw not in (None, "") else None,
                citizenship_norm=_norm_country(str(citizenship_raw)) if citizenship_raw not in (None, "") else "",
                extra=extra,
            )
        )

    return_records = records
    _CACHE = (mtime, return_records, path)
    return return_records


def list_sanction_sources() -> List[str]:
    """List distinct sanction sources from sanctions.json (cached)."""
    sanctions = load_sanctions_json()
    seen = set()
    out: List[str] = []
    for s in sanctions:
        src = (s.source or "").strip()
        if not src or src in seen:
            continue
        seen.add(src)
        out.append(src)
    return sorted(out)


def sanctions_for_matcher(sources: Any = None) -> List[Dict[str, Any]]:
    """Return list of dicts with keys expected by the matching engine.

    Optionally filter by sanction source code(s).
    - sources=None/"ALL"/[] => all
    - sources="OFAC" => only OFAC
    - sources=["OFAC","UN"] => only those
    """
    sanctions = load_sanctions_json()

    src_set = set()
    for s in _as_str_list(sources):
        up = s.strip()
        if up and up.upper() != "ALL":
            src_set.add(up)
    # Dedupe by normalized name (keeps first occurrence)
    unique: Dict[str, Dict[str, Any]] = {}
    for s in sanctions:
        if src_set and (s.source or "").strip() not in src_set:
            continue
        if s.name_norm not in unique:
            unique[s.name_norm] = {
                "external_id": s.external_id,
                "id": s.external_id,  # kept for compatibility with existing match dicts
                "source_id": None,
                "snapshot_id": None,
                "source": s.source,
                "name": s.name,
                "name_norm": s.name_norm,
                "dob_raw": s.dob_raw,
                "cit_raw": s.citizenship_raw,
                "cit_norm": s.citizenship_norm,
                "extra": s.extra,
            }
    return list(unique.values())
