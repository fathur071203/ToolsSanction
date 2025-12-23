from __future__ import annotations

from datetime import datetime, timezone
from typing import IO, Any

import pandas as pd

from slis.models import UploadBatch, Transaction
from slis.matching import normalize_name

import io


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


def create_transaction_batch(
    db,
    file_obj: IO[bytes] | IO[str],
    filename: str,
    created_by: str | None = None,
) -> UploadBatch:
    """
    Import file TXT nasabah (delimiter '|') ke tabel upload_batch + transaction.

    Ekspektasi header (sesuai contoh):
    FORM_NO|SANDI_PELAPOR|FORM_PERIOD|RECORD_NO|
    KOTA_ASAL|NEGARA_TUJUAN|NAMA_PENERIMA|NAMA_PENGIRIM|
    FREKUENSI|NOMINAL_TRX|TUJUAN|CREATED_DATE

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

    raw_bytes = file_obj.read()
    
    if not raw_bytes:
        batch.row_count = 0
        db.commit()
        return batch
    
    content_str = ""
    encodings = ['utf-8', 'utf-16', 'latin-1']
    
    for enc in encodings:
        try:
            content_str = raw_bytes.decode(enc)
            break 
        except ( UnicodeError):
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

    rows_to_insert: list[Transaction] = []
    row_count = 0

    
    for _, row in df.iterrows():
        form_no = _clean_str(row.get("FORM_NO"))
        sandi_pelapor = _clean_str(row.get("SANDI_PELAPOR"))
        form_period_raw = _clean_str(row.get("FORM_PERIOD"))
        record_no = _clean_str(row.get("RECORD_NO"))
        kota_asal = _clean_str(row.get("KOTA_ASAL"))
        negara_tujuan = _clean_str(row.get("NEGARA_TUJUAN"))
        nama_penerima = _clean_str(row.get("NAMA_PENERIMA"))
        nama_pengirim = _clean_str(row.get("NAMA_PENGIRIM"))
        frekuensi_raw = _clean_str(row.get("FREKUENSI"))
        nominal_trx_raw = _clean_str(row.get("NOMINAL_TRX"))
        tujuan = _clean_str(row.get("TUJUAN"))
        created_date_raw = _clean_str(row.get("CREATED_DATE"))

        amount = _parse_int_safe(nominal_trx_raw)

        sender_norm = normalize_name(nama_pengirim)
        receiver_norm = normalize_name(nama_penerima)

        tx = Transaction(
            batch_id=batch.id,
            form_no=form_no,
            reporter_code=sandi_pelapor,
            form_period_raw=form_period_raw,
            record_no=record_no,
            origin_city_code=kota_asal,
            destination_country=negara_tujuan,
            sender_name=nama_pengirim,
            sender_name_normalized=sender_norm,
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
