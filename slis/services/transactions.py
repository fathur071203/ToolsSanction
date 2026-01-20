from __future__ import annotations

from datetime import datetime, timezone
from typing import IO, Any
from pathlib import Path
import hashlib
import json
import re

import pandas as pd

from slis.models import UploadBatch, Transaction
from slis.matching import normalize_name

import io


# ---------- Transaction form detection ----------


FORM_CATEGORY_MAP: dict[str, dict[str, str]] = {
    "G0001": {
        "label": "FORMG0001",
        "description": "TRANSAKSI PENGIRIMAN UANG DARI INDONESIA KE LUAR NEGERI",
    },
    "G0002": {
        "label": "FORMG0002",
        "description": "TRANSAKSI PENGIRIMAN UANG DARI LUAR NEGERI KE INDONESIA",
    },
    "G0003": {
        "label": "FORMG0003",
        "description": "TRANSAKSI PENGIRIMAN UANG DI DALAM WILAYAH REPUBLIK INDONESIA",
    },
}


def _normalize_col_name(name: Any) -> str:
    s = _clean_str(name) or ""
    # strip wrapping quotes if present
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1].strip()
    return s


def detect_form_category(form_no: str | None, columns: list[str]) -> str | None:
    """Return category code like 'G0001'/'G0002'/'G0003' if detectable."""
    fn = (form_no or "").strip().upper()
    if "G0001" in fn:
        return "G0001"
    if "G0002" in fn:
        return "G0002"
    if "G0003" in fn:
        return "G0003"

    cols = {c.strip().upper() for c in columns if c}
    # Heuristics by column signatures
    if {"KOTA_ASAL", "NEGARA_TUJUAN"}.issubset(cols):
        return "G0001"
    if {"NEGARA_ASAL", "KOTA_TUJUAN"}.issubset(cols):
        return "G0002"
    if {"KOTA_ASAL", "KOTA_TUJUAN"}.issubset(cols) and ("TUJUAN_TRX" in cols or "FREKUENSI_PENGIRIMAN" in cols):
        return "G0003"

    return None


def _clean_str(val: Any) -> str | None:

    if val is None:
        return None

    
    if isinstance(val, float) and pd.isna(val):
        return None

    s = str(val).strip()
    if not s:
        return None

    
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1].strip()

    return s or None


def _parse_int_safe(val: Any) -> int | None:
    """
    Mencoba parsing integer dari string seperti "000000014600000".
    Return None kalau gagal.
    """
    s = _clean_str(val)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_datetime_safe(val: Any, fmt: str = "%d-%m-%Y %H:%M:%S") -> datetime | None:
    """
    Mencoba parsing datetime dari string, misal:
    "02-09-2025 11:04:18"
    (SAAT INI hasil parse ini belum disimpan ke kolom apa pun,
    karena nama kolom model belum kita pakai.)
    """
    s = _clean_str(val)
    if not s:
        return None
    try:
        return datetime.strptime(s, fmt)
    except Exception:
        return None


def _repo_root() -> Path:
    # slis/ -> repo root
    return Path(__file__).resolve().parents[1]


def _tx_uploads_root() -> Path:
    return (_repo_root() / "data" / "uploads" / "transactions").resolve()


def _safe_filename(filename: str) -> str:
    name = (filename or "upload.txt").strip()
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return (name[:160] or "upload.txt")


def get_saved_transaction_file_path(batch_id: int) -> Path:
    """Return the stored original upload file path for a transaction batch."""
    batch_dir = _tx_uploads_root() / f"batch_{batch_id}"
    meta_path = batch_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            stored = str(meta.get("stored_filename") or "").strip()
            if stored:
                p = (batch_dir / stored)
                if p.exists():
                    return p
        except Exception:
            pass

    if batch_dir.exists():
        # Fallback: pick first non-meta file
        for p in sorted(batch_dir.iterdir()):
            if p.is_file() and p.name != "meta.json":
                return p

    raise FileNotFoundError(f"Saved upload file not found for batch_id={batch_id}")


def save_transaction_upload_file(batch_id: int, original_filename: str, raw_bytes: bytes) -> Path:
    """Persist original transaction upload bytes to disk and write meta.json."""
    uploads_root = _tx_uploads_root()
    batch_dir = uploads_root / f"batch_{batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = _safe_filename(original_filename)
    file_path = batch_dir / stored_filename

    # Write the raw file
    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    meta = {
        "batch_id": batch_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "size_bytes": int(len(raw_bytes)),
        "sha256": sha256,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    (batch_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return file_path


def create_transaction_batch(
    db,
    file_obj: IO[bytes] | IO[str],
    filename: str,
    created_by: str | None = None,
) -> UploadBatch:
    """
    Import file TXT nasabah (delimiter '|') ke tabel upload_batch + transaction.

    Menerima beberapa variasi struktur (G0001/G0002/G0003) dan akan:
    - Auto-detect kategori form (G0001/G0002/G0003) dari FORM_NO atau signature kolom
    - Menyimpan kategori ke UploadBatch.source_type
    - Menyimpan field kunci (names, reporter_code, amount, dst) ke tabel transactions

    - Menggunakan pandas.read_csv untuk parsing cepat dan tahan terhadap bytes.
    - Menyimpan data mentah + beberapa field yang sudah dinormalisasi.
    """

    
    batch = UploadBatch(
        filename=filename,
        type="TXT",
        created_at=datetime.now(timezone.utc),
        created_by=created_by,
        row_count=0,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    raw = file_obj.read()
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8", errors="replace")
    else:
        raw_bytes = raw
    
    if not raw_bytes:
        batch.row_count = 0
        db.commit()
        return batch
    
    # Persist original upload to disk for later re-download / re-import.
    try:
        save_transaction_upload_file(batch_id=batch.id, original_filename=filename, raw_bytes=raw_bytes)
    except Exception:
        # Do not block screening if file persistence fails.
        pass

    content_str = ""
    encodings = ["utf-8", "utf-16", "latin-1"]

    for enc in encodings:
        try:
            content_str = raw_bytes.decode(enc)
            break
        except UnicodeError:
            continue
    
    if not content_str:
        raise ValueError("File encoding tidak didukung. Harap gunakan format UTF-8 atau UTF-16.")

    
    # raw_stream = getattr(file_obj, "stream", file_obj)

    
    try:
        df = pd.read_csv(
            io.StringIO(content_str),
            sep="|",
            dtype=str,
            engine="python",
        )
        df = df.fillna("")
    except Exception as e:
        raise ValueError(f"Gagal memproses struktur file: {str(e)}")

    # Normalize column names (some files have quoted headers like "FORM_NO")
    df.columns = [_normalize_col_name(c) for c in df.columns]

    # Detect form/category using first non-empty FORM_NO if available
    detected_form_no = None
    if "FORM_NO" in df.columns and len(df) > 0:
        try:
            detected_form_no = _clean_str(df.iloc[0].get("FORM_NO"))
        except Exception:
            detected_form_no = None

    category = detect_form_category(detected_form_no, list(df.columns))
    if category:
        batch.source_type = category
        db.add(batch)
        db.commit()

    rows_to_insert: list[Transaction] = []
    row_count = 0

    
    for _, row in df.iterrows():
        # Common fields
        form_no = _clean_str(row.get("FORM_NO"))
        sandi_pelapor = _clean_str(row.get("SANDI_PELAPOR"))
        form_period_raw = _clean_str(row.get("FORM_PERIOD"))
        record_no = _clean_str(row.get("RECORD_NO"))
        nama_penerima = _clean_str(row.get("NAMA_PENERIMA"))
        nama_pengirim = _clean_str(row.get("NAMA_PENGIRIM"))
        nominal_trx_raw = _clean_str(row.get("NOMINAL_TRX"))
        created_date_raw = _clean_str(row.get("CREATED_DATE"))

        # Variant fields
        kota_asal = _clean_str(row.get("KOTA_ASAL"))
        kota_tujuan = _clean_str(row.get("KOTA_TUJUAN"))
        negara_asal = _clean_str(row.get("NEGARA_ASAL"))
        negara_tujuan = _clean_str(row.get("NEGARA_TUJUAN"))

        frekuensi_raw = _clean_str(row.get("FREKUENSI")) or _clean_str(row.get("FREKUENSI_PENGIRIMAN"))
        tujuan = _clean_str(row.get("TUJUAN")) or _clean_str(row.get("TUJUAN_TRX"))

        amount = _parse_int_safe(nominal_trx_raw)

        sender_norm = normalize_name(nama_pengirim)
        receiver_norm = normalize_name(nama_penerima)

        # Best-effort destination country inference when not present in file
        inferred_dest_country = negara_tujuan
        if not inferred_dest_country and category in {"G0002", "G0003"}:
            inferred_dest_country = "ID"

        tx = Transaction(
            batch_id=batch.id,
            form_no=form_no,
            reporter_code=sandi_pelapor,
            form_period_raw=form_period_raw,
            record_no=record_no,
            origin_city_code=kota_asal or kota_tujuan,
            destination_country=inferred_dest_country,
            sender_name=nama_pengirim,
            sender_name_normalized=sender_norm,
            sender_country=negara_asal,
            receiver_name=nama_penerima,
            receiver_name_normalized=receiver_norm,
            frequency_raw=frekuensi_raw,
            amount_raw=nominal_trx_raw,
            amount=amount,
            purpose_code=tujuan,
            created_at_raw=created_date_raw,
        )

        rows_to_insert.append(tx)
        row_count += 1

        if len(rows_to_insert) >= 1000:
            db.bulk_save_objects(rows_to_insert)
            db.commit()
            rows_to_insert.clear()

    
    if rows_to_insert:
        db.bulk_save_objects(rows_to_insert)
        db.commit()

    
    batch.row_count = row_count
    db.add(batch)
    db.commit()
    db.refresh(batch)

    return batch
