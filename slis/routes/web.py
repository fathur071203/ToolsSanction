from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
)
from datetime import datetime, timezone
import json

from sqlalchemy import func

from slis.db import SessionLocal
from slis.models import (
    UploadBatch,
    SanctionSource,
    SanctionSnapshot,
    ScreeningJob,
    ScreeningResult,
    Transaction,
)
from slis.services.transactions import create_transaction_batch
from slis.services.transactions import get_saved_transaction_file_path
from slis.services.sanctions import import_sanction_file
from slis.celery_app import celery_app
from slis.celery_utils import enqueue_screening_job
from slis.db import SessionLocal
from slis.services.screening import search_single_entity
from slis.services.screening import run_screening_for_job
from slis.services.reporters import load_reporters_map, format_reporter_label
from slis.services.transactions import FORM_CATEGORY_MAP, detect_form_category
from slis.sanctions_json import (
    get_sanctions_json_path,
    load_json_sanctions_file,
    load_tabular_sanctions_file,
    read_sanction_sources_json,
    list_sanction_sources,
    read_raw_sanctions_json,
    write_sanction_sources_json,
    validate_raw_sanctions_json,
    write_raw_sanctions_json,
)
from slis.services.dttot_ai import DTTOT_SOURCE, load_dttot_ai_result, run_dttot_ai_job

web_bp = Blueprint("web", __name__)


def _start_screening_in_background(job_id: int) -> None:
    """Fallback runner when Celery/Redis broker isn't available."""
    import threading

    def _runner() -> None:
        db = SessionLocal()
        try:
            run_screening_for_job(db=db, job_id=job_id)
        finally:
            db.close()

    t = threading.Thread(target=_runner, name=f"slis-screening-{job_id}", daemon=True)
    t.start()


@web_bp.route("/transactions/batches/<int:batch_id>/download", methods=["GET"])
def transaction_batch_download(batch_id: int):
    db = SessionLocal()
    try:
        batch = db.get(UploadBatch, batch_id)
        if batch is None:
            flash(f"Batch transaksi #{batch_id} tidak ditemukan.", "warning")
            return redirect(url_for("web.sanctions_upload"))

        try:
            path = get_saved_transaction_file_path(batch_id)
        except Exception as e:
            flash(f"File batch belum tersimpan / tidak ditemukan: {e}", "warning")
            return redirect(url_for("web.sanctions_upload", batch_id=batch_id))

        return send_file(
            path,
            as_attachment=True,
            download_name=batch.filename or path.name,
            mimetype="application/octet-stream",
        )
    finally:
        db.close()


@web_bp.route("/transactions/batches/<int:batch_id>/reimport", methods=["POST"])
def transaction_batch_reimport(batch_id: int):
    """Re-import a previously uploaded batch file into a new batch."""
    from io import BytesIO

    db = SessionLocal()
    try:
        batch = db.get(UploadBatch, batch_id)
        if batch is None:
            flash(f"Batch transaksi #{batch_id} tidak ditemukan.", "warning")
            return redirect(url_for("web.sanctions_upload"))

        try:
            path = get_saved_transaction_file_path(batch_id)
            raw_bytes = path.read_bytes()
        except Exception as e:
            flash(f"Gagal load file batch untuk re-import: {e}", "danger")
            return redirect(url_for("web.sanctions_upload", batch_id=batch_id))

        created_by = (request.form.get("created_by") or "").strip() or None
        try:
            new_batch = create_transaction_batch(
                db=db,
                file_obj=BytesIO(raw_bytes),
                filename=batch.filename,
                created_by=created_by,
            )
        except Exception as e:
            db.rollback()
            flash(f"Re-import gagal: {e}", "danger")
            return redirect(url_for("web.sanctions_upload", batch_id=batch_id))

        flash(f"Re-import OK: batch baru #{new_batch.id} dibuat dari file batch #{batch_id}.", "success")
        return redirect(url_for("web.sanctions_upload", batch_id=new_batch.id))
    finally:
        db.close()


@web_bp.route("/transactions/batches/upload", methods=["POST"])
def transaction_batch_upload():
    """Upload a new transaction file and create a batch, without starting screening."""
    file = request.files.get("transaction_file")
    if not file or file.filename == "":
        return jsonify({"error": "transaction_file is required"}), 400

    created_by = (request.form.get("created_by") or "").strip() or None

    db = SessionLocal()
    try:
        batch = create_transaction_batch(
            db=db,
            file_obj=file,
            filename=file.filename,
            created_by=created_by,
        )

        return (
            jsonify(
                {
                    "batch_id": batch.id,
                    "filename": batch.filename,
                    "row_count": batch.row_count,
                    "download_url": url_for("web.transaction_batch_download", batch_id=batch.id),
                    "reimport_url": url_for("web.transaction_batch_reimport", batch_id=batch.id),
                }
            ),
            201,
        )
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@web_bp.route("/sanctions/manage", methods=["GET", "POST"])
def sanctions_manage():
    """Frontend view for sanctions.json (source of truth)."""
    json_path = str(get_sanctions_json_path())

    if request.method == "POST":
        action = request.form.get("action") or "save_text"
        try:
            if action == "update_record_name":
                source = (request.form.get("source") or "UNKNOWN").strip() or "UNKNOWN"
                record_id = (request.form.get("record_id") or "").strip()
                new_name = (request.form.get("new_name") or "").strip()

                if not record_id:
                    flash("Record ID tidak valid.", "warning")
                    return redirect(request.url)

                if not new_name:
                    flash("Nama baru tidak boleh kosong.", "warning")
                    return redirect(request.url)

                current = read_raw_sanctions_json()
                updated = False
                for r in current:
                    if not isinstance(r, dict):
                        continue
                    r_source = str(r.get("source") or r.get("source_code") or "UNKNOWN")
                    r_id = str(r.get("id") or r.get("external_id") or "")
                    if r_source == source and r_id == record_id:
                        # Normalize to always store in `name`
                        r["name"] = new_name
                        # If the row used full_name historically, keep it in sync too
                        if "full_name" in r and isinstance(r.get("full_name"), str):
                            r["full_name"] = new_name
                        updated = True
                        break

                if not updated:
                    flash("Record tidak ditemukan untuk diupdate.", "warning")
                    return redirect(request.url)

                rows = validate_raw_sanctions_json(current)
                write_raw_sanctions_json(rows)
                flash("Nama berhasil diupdate.", "success")
                return redirect(request.referrer or request.url)

            if action == "delete_record":
                source = (request.form.get("source") or "UNKNOWN").strip() or "UNKNOWN"
                record_id = (request.form.get("record_id") or "").strip()

                if not record_id:
                    flash("Record ID tidak valid.", "warning")
                    return redirect(request.referrer or request.url)

                current = read_raw_sanctions_json()
                before = len(current)
                kept = []
                removed = 0
                for r in current:
                    if not isinstance(r, dict):
                        kept.append(r)
                        continue
                    r_source = str(r.get("source") or r.get("source_code") or "UNKNOWN")
                    r_id = str(r.get("id") or r.get("external_id") or "")
                    if r_source == source and r_id == record_id:
                        removed += 1
                        continue
                    kept.append(r)

                if removed == 0:
                    flash("Record tidak ditemukan untuk dihapus.", "warning")
                    return redirect(request.referrer or request.url)

                rows = validate_raw_sanctions_json(kept)
                write_raw_sanctions_json(rows)
                flash(f"Berhasil menghapus {removed} record dari source {source}.", "success")
                return redirect(request.referrer or request.url)

            if action == "dttot_ai_parse":
                source = (request.form.get("source") or DTTOT_SOURCE).strip() or DTTOT_SOURCE
                if source != DTTOT_SOURCE:
                    flash("Fitur AI ini khusus untuk DTTOT.", "warning")
                    return redirect(request.url)

                f = request.files.get("pdf")
                if not f or not getattr(f, "filename", ""):
                    flash("Pilih file PDF DTTOT terlebih dahulu.", "warning")
                    return redirect(request.url)

                if not f.filename.lower().endswith(".pdf"):
                    flash("File harus PDF.", "warning")
                    return redirect(request.url)

                pdf_bytes = f.read()
                if not pdf_bytes:
                    flash("File PDF kosong.", "warning")
                    return redirect(request.url)

                meta, rows = run_dttot_ai_job(pdf_bytes=pdf_bytes, original_filename=f.filename)
                flash(f"AI selesai: {len(rows)} record terdeteksi. Silakan preview & approve.", "success")
                return redirect(url_for("web.sanctions_manage", dttot_token=meta.token))

            if action == "dttot_ai_approve":
                token = (request.form.get("token") or "").strip()
                if not token:
                    flash("Token hasil AI tidak valid.", "warning")
                    return redirect(request.url)

                _, rows = load_dttot_ai_result(token)
                if not rows:
                    flash("Hasil AI kosong.", "warning")
                    return redirect(request.url)

                mode = (request.form.get("mode") or "append").strip().lower()
                current = read_raw_sanctions_json()
                if mode in {"replace_source", "replace-source", "replace"}:
                    current = [
                        r
                        for r in current
                        if str(r.get("source") or r.get("source_code") or "UNKNOWN") != DTTOT_SOURCE
                    ]

                # Always force source to DTTOT for safety
                for r in rows:
                    if isinstance(r, dict):
                        r["source"] = DTTOT_SOURCE
                current.extend([r for r in rows if isinstance(r, dict)])

                validated = validate_raw_sanctions_json(current)
                write_raw_sanctions_json(validated)

                existing_sources = read_sanction_sources_json()
                if DTTOT_SOURCE not in existing_sources:
                    existing_sources.append(DTTOT_SOURCE)
                    write_sanction_sources_json(existing_sources)

                verb = "replace" if mode in {"replace_source", "replace-source", "replace"} else "append"
                flash(f"Approve OK: {verb} {len(rows)} record ke sanctions.json (source DTTOT).", "success")
                return redirect(url_for("web.sanctions_manage"))

            if action == "add_record":
                name = (request.form.get("name") or "").strip()
                source = (request.form.get("source") or "UNKNOWN").strip() or "UNKNOWN"
                record_id = (request.form.get("record_id") or "").strip()
                dob = (request.form.get("dob") or "").strip()
                citizenship = (request.form.get("citizenship") or "").strip()
                remarks = (request.form.get("remarks") or "").strip()

                if not name:
                    flash("Field 'Nama' wajib diisi.", "warning")
                    return redirect(request.url)

                if not record_id:
                    record_id = datetime.now(timezone.utc).strftime("MANUAL-%Y%m%d%H%M%S%f")

                new_row = {
                    "id": record_id,
                    "source": source,
                    "name": name,
                }
                if dob:
                    new_row["dob"] = dob
                if citizenship:
                    new_row["citizenship"] = citizenship
                if remarks:
                    new_row["remarks"] = remarks

                current = read_raw_sanctions_json()
                current.append(new_row)
                rows = validate_raw_sanctions_json(current)
                write_raw_sanctions_json(rows)

                existing_sources = read_sanction_sources_json()
                if source not in existing_sources:
                    existing_sources.append(source)
                    write_sanction_sources_json(existing_sources)

                flash(f"Berhasil menambah 1 sanction ke source {source}.", "success")
                return redirect(request.referrer or request.url)

            if action == "upload_source_file":
                source = (request.form.get("source") or "UNKNOWN").strip() or "UNKNOWN"
                mode = (request.form.get("mode") or "append").strip().lower()
                f = request.files.get("file")
                if not f or not getattr(f, "filename", ""):
                    flash("Pilih file terlebih dahulu (.csv / .xlsx).", "warning")
                    return redirect(request.url)

                filename_lower = f.filename.lower()
                if filename_lower.endswith(".json"):
                    imported_rows = load_json_sanctions_file(file_obj=f, filename=f.filename, source=source)
                else:
                    imported_rows = load_tabular_sanctions_file(file_obj=f, filename=f.filename, source=source)
                if not imported_rows:
                    flash("Tidak ada baris valid yang bisa diimport (pastikan kolom nama ada).", "warning")
                    return redirect(request.url)

                current = read_raw_sanctions_json()
                if mode in {"replace", "replace_source", "replace-source"}:
                    current = [r for r in current if str(r.get("source") or r.get("source_code") or "UNKNOWN") != source]

                current.extend(imported_rows)
                rows = validate_raw_sanctions_json(current)
                write_raw_sanctions_json(rows)

                existing_sources = read_sanction_sources_json()
                if source not in existing_sources:
                    existing_sources.append(source)
                    write_sanction_sources_json(existing_sources)

                verb = "replace" if mode in {"replace", "replace_source", "replace-source"} else "append"
                flash(f"Berhasil {verb} {len(imported_rows)} record untuk source {source}.", "success")
                return redirect(request.referrer or request.url)

            if action == "add_source":
                source = (request.form.get("source") or "").strip()
                if not source:
                    flash("Field 'Source' wajib diisi.", "warning")
                    return redirect(request.url)

                existing = read_sanction_sources_json()
                if source in existing:
                    flash(f"Source '{source}' sudah ada.", "info")
                    return redirect(request.url)

                existing.append(source)
                write_sanction_sources_json(existing)
                flash(f"Berhasil menambah source '{source}'.", "success")
                return redirect(request.referrer or request.url)

            flash("Aksi tidak dikenal.", "warning")
            return redirect(request.url)

        except json.JSONDecodeError as e:
            flash(f"JSON tidak valid: {e}", "danger")
        except Exception as e:
            if action in {"dttot_ai_parse", "dttot_ai_approve"}:
                flash(f"Gagal proses AI DTTOT: {e}", "danger")
            else:
                flash(f"Gagal menyimpan sanctions.json: {e}", "danger")

    # GET (and also fallback render after error)
    try:
        raw_rows = read_raw_sanctions_json()
    except Exception:
        raw_rows = []

    q = (request.args.get("q") or "").strip()
    q_lower = q.lower()

    active_source = (request.args.get("source") or "").strip()

    sort = (request.args.get("sort") or "order").strip().lower()
    sort_dir = (request.args.get("dir") or "asc").strip().lower()
    if sort_dir not in {"asc", "desc"}:
        sort_dir = "asc"
    allowed_sorts = {"order", "name", "id", "dob", "citizenship", "remarks"}
    if sort not in allowed_sorts:
        sort = "order"

    per_page_options = [10, 50, 100, 1000]
    per_page_raw = (request.args.get("per_page") or "").strip()
    try:
        per_page = int(per_page_raw) if per_page_raw else 50
    except Exception:
        per_page = 50
    if per_page not in per_page_options:
        # keep it predictable; clamp oversized values
        per_page = 1000 if per_page > 1000 else 50

    page_raw = (request.args.get("page") or "").strip()
    try:
        page = int(page_raw) if page_raw else 1
    except Exception:
        page = 1
    if page < 1:
        page = 1

    # Build counts without materializing per-source tables (performance)
    totals_by_source: dict[str, int] = {}
    filtered_counts_by_source: dict[str, int] = {}

    for r in raw_rows:
        if not isinstance(r, dict):
            continue

        nm = (r.get("name") or r.get("full_name") or "").strip()
        if not nm:
            continue

        src = str(r.get("source") or r.get("source_code") or "UNKNOWN")
        totals_by_source[src] = totals_by_source.get(src, 0) + 1
        if q_lower and q_lower in nm.lower():
            filtered_counts_by_source[src] = filtered_counts_by_source.get(src, 0) + 1

    registered_sources = read_sanction_sources_json()
    known_sources = sorted(set(registered_sources) | set(totals_by_source.keys()) | ({active_source} if active_source else set()))
    if q_lower and not active_source:
        # In overview, only show sources that have matches.
        sources_for_list = sorted(set(filtered_counts_by_source.keys()) | ({active_source} if active_source else set()))
    else:
        sources_for_list = known_sources

    sources_summary = []
    for src in sources_for_list:
        total = int(totals_by_source.get(src, 0))
        if q_lower:
            shown = int(filtered_counts_by_source.get(src, 0))
        else:
            shown = total
        sources_summary.append({"source": src, "total_count": total, "shown_count": shown})

    # Single-source records (paginated) - do not materialize all rows
    total_in_source = int(totals_by_source.get(active_source, 0)) if active_source else 0
    if active_source:
        if q_lower:
            filtered_in_source = int(filtered_counts_by_source.get(active_source, 0))
        else:
            filtered_in_source = total_in_source
    else:
        filtered_in_source = 0

    total_pages = 1
    if active_source:
        total_pages = max(1, (filtered_in_source + per_page - 1) // per_page)
        if page > total_pages:
            page = total_pages

    start = (page - 1) * per_page
    end = start + per_page

    def _row_min(idx: int, r: dict, src: str, name: str) -> dict:
        return {
            "id": str(r.get("id") or r.get("external_id") or f"ROW-{idx+1}"),
            "source": src,
            "name": name,
            "dob": r.get("dob")
            or r.get("dob_raw")
            or r.get("date_of_birth")
            or r.get("date_of_birth_raw"),
            "citizenship": r.get("citizenship") or r.get("citizenship_raw"),
            "remarks": r.get("remarks") or r.get("remark") or r.get("note") or r.get("catatan"),
        }

    source_records_page = []
    if active_source and filtered_in_source > 0:
        if sort == "order":
            seen = 0
            for idx, r in enumerate(raw_rows):
                if not isinstance(r, dict):
                    continue
                src = str(r.get("source") or r.get("source_code") or "UNKNOWN")
                if src != active_source:
                    continue

                name = (r.get("name") or r.get("full_name") or "").strip()
                if not name:
                    continue

                if q_lower and q_lower not in name.lower():
                    continue

                if seen >= end:
                    break
                if seen >= start:
                    source_records_page.append(_row_min(idx, r, src, name))
                seen += 1
        else:
            # Sorting requires materializing the filtered list.
            all_rows = []
            for idx, r in enumerate(raw_rows):
                if not isinstance(r, dict):
                    continue
                src = str(r.get("source") or r.get("source_code") or "UNKNOWN")
                if src != active_source:
                    continue

                name = (r.get("name") or r.get("full_name") or "").strip()
                if not name:
                    continue
                if q_lower and q_lower not in name.lower():
                    continue

                all_rows.append(_row_min(idx, r, src, name))

            # Recompute counts for accuracy when sorting path is used.
            filtered_in_source = len(all_rows)
            total_pages = max(1, (filtered_in_source + per_page - 1) // per_page)
            if page > total_pages:
                page = total_pages
            start = (page - 1) * per_page
            end = start + per_page

            def keyfunc(item: dict):
                v = item.get(sort)
                if v is None:
                    v = ""
                s = str(v)
                return s.lower() if sort in {"name", "citizenship", "remarks"} else s

            reverse = sort_dir == "desc"
            all_rows.sort(key=keyfunc, reverse=reverse)
            source_records_page = all_rows[start:end]

    dttot_preview = None
    dttot_token = (request.args.get("dttot_token") or "").strip()
    if dttot_token:
        try:
            _, dttot_preview = load_dttot_ai_result(dttot_token)
        except Exception as e:
            flash(f"Gagal load preview AI: {e}", "warning")
            dttot_preview = None

    return render_template(
        "sanctions_manage.html",
        json_path=json_path,
        sanctions_count=len(raw_rows),
        sources_summary=sources_summary,
        active_source=active_source,
        per_page=per_page,
        per_page_options=per_page_options,
        page=page,
        total_pages=total_pages,
        total_in_source=total_in_source,
        filtered_in_source=filtered_in_source,
        source_records=source_records_page,
        sort=sort,
        sort_dir=sort_dir,
        dttot_source=DTTOT_SOURCE,
        dttot_token=dttot_token,
        dttot_preview=dttot_preview,
        q=q,
    )


@web_bp.route("/sanctions/download", methods=["GET"])
def sanctions_download():
    path = get_sanctions_json_path()
    return send_file(
        path,
        as_attachment=True,
        download_name="sanctions.json",
        mimetype="application/json",
    )

@web_bp.route("/")
def index():
    db = SessionLocal()
    try:
        latest_batches = (
            db.query(UploadBatch)
            .order_by(UploadBatch.created_at.desc())
            .limit(5)
            .all()
        )
        latest_snapshots = (
            db.query(SanctionSnapshot)
            .order_by(SanctionSnapshot.created_at.desc())
            .limit(5)
            .all()
        )
        latest_jobs = (
            db.query(ScreeningJob)
            .order_by(ScreeningJob.created_at.desc())
            .limit(5)
            .all()
        )
        sources = (
            db.query(SanctionSource)
            .order_by(SanctionSource.code)
            .all()
        )
        return render_template(
            "index.html",
            batches=latest_batches,
            snapshots=latest_snapshots,
            jobs=latest_jobs,
            sources=sources,
        )
    finally:
        db.close()



@web_bp.route("/sanctions/upload", methods=["GET", "POST"])
def sanctions_upload():
   
    db = SessionLocal()
    try:
        sources = db.query(SanctionSource).order_by(SanctionSource.code).all()
        
        batches = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).limit(50).all()

        print("Available Batches:")
        for b in batches:
            print(f" - Batch {b.id}: {b.filename}")
        
        preselected_batch_id = request.args.get("batch_id", type=int)

        if request.method == "POST" and "sanction_file" in request.files:
            file = request.files["sanction_file"]
            source_code = request.form.get("source_code")
            
            if file and file.filename != "":
                try:
                    _, count = import_sanction_file(
                        db=db,
                        source_code=source_code,
                        file_obj=file,
                        filename=file.filename,
                        version_label=request.form.get("version_label"),
                        effective_date=None
                    )
                    flash(f"Sukses import {count} data sanction.", "success")
                    return redirect(url_for("web.index"))
                except Exception as e:
                    db.rollback()
                    flash(f"Error import sanction: {e}", "danger")
                    return redirect(request.url)

        return render_template(
            "sanctions_upload.html",
            sources=sources,
            batches=batches,
            preselected_batch_id=preselected_batch_id
        )
    finally:
        db.close()


@web_bp.route("/screening/start", methods=["GET", "POST"])
def screening_start():
    db = SessionLocal()
    try:
        # Pre-load data untuk dropdown
        batches = db.query(UploadBatch).order_by(UploadBatch.created_at.desc()).limit(50).all()

        print("Available Batches:")
        for b in batches:
            print(f" - Batch {b.id}: {b.filename}")
        
        preselected_batch_id = request.args.get("batch_id", type=int)

        if request.method == "POST":
            tx_source = (request.form.get("transaction_source") or "batch").strip() or "batch"
            batch_id = None

            # Batch Lama
            if tx_source == "batch":
                batch_id = request.form.get("batch_id", type=int)
                if not batch_id:
                    flash("Pilih batch transaksi yang valid.", "danger")
                    return redirect(request.url)
            
            elif tx_source == "upload":
                file = request.files.get("transaction_file")
                if not file or file.filename == "":
                    flash("File transaksi wajib diisi untuk upload baru.", "danger")
                    return redirect(request.url)
                
                try:
                    # Buat Batch Baru
                    new_batch = create_transaction_batch(
                        db=db,
                        file_obj=file,
                        filename=file.filename,
                        created_by=request.form.get("created_by")
                    )
                    batch_id = new_batch.id
                    flash(f"Berhasil mengupload batch baru #{batch_id}", "success")
                except Exception as e:
                    db.rollback()
                    flash(f"Gagal memproses file transaksi: {e}", "danger")
                    return redirect(request.url)

            # Validasi Final Batch ID
            batch = db.get(UploadBatch, batch_id)
            if batch is None:
                flash(f"Batch ID {batch_id} tidak ditemukan.", "danger")
                return redirect(request.url)

            try:
                threshold_name = float(request.form.get("threshold_name_score") or 70.0)
            except Exception:
                threshold_name = 70.0
            try:
                threshold_final = float(request.form.get("threshold_score") or 60.0)
            except Exception:
                threshold_final = 60.0

            threshold_name = max(0.0, min(100.0, threshold_name))
            threshold_final = max(0.0, min(100.0, threshold_final))
            created_by = request.form.get("created_by") or None

            sanction_source = (request.form.get("sanction_source") or "ALL").strip() or "ALL"
            if sanction_source.upper() == "ALL":
                sanction_source = "ALL"
            sanction_source_filter = None if sanction_source == "ALL" else sanction_source

            job = ScreeningJob(
                batch_id=batch_id,
                status="PENDING",
                threshold_name_score=threshold_name,
                threshold_score=threshold_final,
                sanction_source_filter=sanction_source_filter,
                created_at=datetime.now(timezone.utc),
                created_by=created_by,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Trigger Celery Task (fallback to background thread if broker not available)
            task_id = enqueue_screening_job(job.id)
            if task_id:
                job.celery_task_id = task_id
                db.commit()
            else:
                job.celery_task_id = None
                db.commit()
                _start_screening_in_background(job.id)
                flash(
                    "Redis/Celery broker tidak aktif. Screening dijalankan via background thread; progress tetap diambil dari database.",
                    "warning",
                )

            flash(f"Screening Job #{job.id} sedang berjalan...", "success")
            return redirect(url_for("web.screening_jobs"))
       
        sources = read_sanction_sources_json()
        if not sources:
            sources = list_sanction_sources()

        return render_template(
            "screening_start.html",
            batches=batches,
            preselected_batch_id=preselected_batch_id,
            sanction_sources=sources,
        )
    finally:
        db.close()


@web_bp.route("/sanctions/upload", methods=["GET", "POST"])
def sanctions_upload_reference():
    db = SessionLocal()
    try:
        sources = db.query(SanctionSource).order_by(SanctionSource.code).all()

        match_sources = read_sanction_sources_json()
        if not match_sources:
            match_sources = list_sanction_sources()

        if request.method == "POST":
            source_code = request.form.get("source_code")
            file = request.files.get("sanction_file")

            if not file or file.filename == "":
                flash("File sanction list wajib diisi.", "danger")
                return redirect(request.url)

            try:
                _, count = import_sanction_file(
                    db=db,
                    source_code=source_code,
                    file_obj=file,
                    filename=file.filename,
                    version_label=request.form.get("version_label"),
                    effective_date=None
                )
                flash(f"Sukses import {count} data sanction.", "success")
                return redirect(url_for("web.index"))
            except Exception as e:
                db.rollback()
                flash(f"Error import sanction: {e}", "danger")
                return redirect(request.url)

        return render_template("sanctions_upload.html", sources=sources, match_sanction_sources=match_sources)
    finally:
        db.close()



@web_bp.route("/screening/jobs")
def screening_jobs():
    db = SessionLocal()
    try:
        jobs = (
            db.query(ScreeningJob)
            .order_by(ScreeningJob.created_at.desc())
            .limit(100)
            .all()
        )
        return render_template("screening_jobs.html", jobs=jobs)
    finally:
        db.close()


@web_bp.route("/screening/jobs/<int:job_id>")
def screening_job_detail(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(ScreeningJob, job_id)
        if job is None:
            flash(f"Job {job_id} tidak ditemukan.", "danger")
            return redirect(url_for("web.screening_jobs"))

        batch = db.get(UploadBatch, int(job.batch_id)) if job.batch_id is not None else None

        # Pagination for vertical results view (paginate by transaction).
        try:
            page = int(request.args.get("page", 1))
        except Exception:
            page = 1
        try:
            per_page = int(request.args.get("per_page", 10))
        except Exception:
            per_page = 10
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 50:
            per_page = 50

        # Threshold filter (final_score >= min_score)
        min_score_raw = (request.args.get("min_score") or request.args.get("threshold") or "").strip()
        if min_score_raw:
            try:
                min_score = float(min_score_raw)
            except Exception:
                min_score = float(job.threshold_score or 0)
        else:
            min_score = float(job.threshold_score or 0)
        if min_score < 0:
            min_score = 0.0
        if min_score > 100:
            min_score = 100.0

        # Reporter filter (SANDI_PELAPOR)
        reporter_code_selected = (request.args.get("reporter_code") or "").strip() or "ALL"
        if reporter_code_selected.upper() == "ALL":
            reporter_code_selected = "ALL"

        # Sanction source filter (sanction_source_code)
        sanction_source_selected = (request.args.get("sanction_source") or "").strip() or "ALL"
        if sanction_source_selected.upper() == "ALL":
            sanction_source_selected = "ALL"

        # KPI counts should follow filtering (reporter_code + sanction_source + min_score)
        kpi_base_q = (
            db.query(ScreeningResult)
            .join(Transaction, ScreeningResult.transaction_id == Transaction.id)
            .filter(ScreeningResult.job_id == job_id)
            .filter(Transaction.batch_id == job.batch_id)
        )
        if reporter_code_selected != "ALL":
            kpi_base_q = kpi_base_q.filter(Transaction.reporter_code == reporter_code_selected)
        if sanction_source_selected != "ALL":
            kpi_base_q = kpi_base_q.filter(ScreeningResult.sanction_source_code == sanction_source_selected)
        if min_score > 0:
            kpi_base_q = kpi_base_q.filter(ScreeningResult.final_score >= min_score)

        kpi_total_matches = int(kpi_base_q.with_entities(func.count(ScreeningResult.id)).scalar() or 0)

        distinct_sanction_rows = (
            kpi_base_q.with_entities(
                ScreeningResult.sanction_source_code,
                ScreeningResult.sanction_external_id,
                ScreeningResult.sanction_name,
            )
            .distinct()
            .all()
        )
        sanction_keys: set[str] = set()
        for src, ext_id, name in distinct_sanction_rows:
            src_s = (src or "UNKNOWN").strip() or "UNKNOWN"
            ident = (ext_id or "").strip() or (name or "").strip()
            if not ident:
                continue
            sanction_keys.add(f"{src_s}|{ident}")
        kpi_sanctions_detected = len(sanction_keys)

        tx_scores_q = (
            db.query(
                ScreeningResult.transaction_id.label("tx_id"),
                func.max(ScreeningResult.final_score).label("max_score"),
            )
            .join(Transaction, ScreeningResult.transaction_id == Transaction.id)
            .filter(ScreeningResult.job_id == job_id)
            .filter(Transaction.batch_id == job.batch_id)
            .group_by(ScreeningResult.transaction_id)
        )
        if reporter_code_selected != "ALL":
            tx_scores_q = tx_scores_q.filter(Transaction.reporter_code == reporter_code_selected)
        if sanction_source_selected != "ALL":
            tx_scores_q = tx_scores_q.filter(ScreeningResult.sanction_source_code == sanction_source_selected)
        if min_score > 0:
            tx_scores_q = tx_scores_q.filter(ScreeningResult.final_score >= min_score)
        total_tx_with_matches = tx_scores_q.count()
        total_pages = max(1, (total_tx_with_matches + per_page - 1) // per_page)
        if page > total_pages:
            page = total_pages

        tx_page = (
            tx_scores_q.order_by(func.max(ScreeningResult.final_score).desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        tx_ids = [int(r.tx_id) for r in tx_page if getattr(r, "tx_id", None) is not None]

        rows = []
        if tx_ids:
            rows = (
                db.query(ScreeningResult, Transaction)
                .outerjoin(Transaction, ScreeningResult.transaction_id == Transaction.id)
                .filter(ScreeningResult.job_id == job_id)
                .filter(ScreeningResult.transaction_id.in_(tx_ids))
                .filter(ScreeningResult.final_score >= min_score)
                .filter(Transaction.batch_id == job.batch_id)
                .filter(
                    ScreeningResult.sanction_source_code == sanction_source_selected
                    if sanction_source_selected != "ALL"
                    else True
                )
                .order_by(ScreeningResult.transaction_id.asc(), ScreeningResult.final_score.desc())
                .all()
            )
        
        results = []
        for sr, tx in rows:
            results.append({
                "id": sr.id,
                "target_role": sr.target_role,
                "transaction_id": getattr(sr, "transaction_id", None) or getattr(tx, "id", None),
                "sender_name": getattr(tx, "sender_name", "") or getattr(tx, "nama_pengirim", "") or "-",
                "receiver_name": getattr(tx, "receiver_name", "") or getattr(tx, "nama_penerima", "") or "-",
                "reporter_code": getattr(tx, "reporter_code", None),
                "target_name": getattr(sr, "target_name", None),
                "sanction_name": sr.sanction_name or "-",
                "sanction_source_id": sr.sanction_source_id,
                "sanction_source_code": getattr(sr, "sanction_source_code", None),
                "target_country": sr.target_country,
                "sanction_citizenship": sr.sanction_citizenship,
                "geographic_insights": sr.geographic_insights,
                "name_score": sr.name_score,
                "dob_score": sr.dob_score,
                "citizenship_score": sr.citizenship_score,
                "final_score": sr.final_score,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
            })

        # Group results for a more insight-focused UI (no horizontal slider).
        tx_groups: list[dict] = []
        tx_map: dict[int, dict] = {}
        for r in results:
            tx_id = int(r.get("transaction_id") or 0)
            if tx_id not in tx_map:
                tx_map[tx_id] = {
                    "transaction_id": tx_id,
                    "sender_name": r.get("sender_name") or "-",
                    "receiver_name": r.get("receiver_name") or "-",
                    "reporter_code": (r.get("reporter_code") or "").strip() or None,
                    "targets": {},  # (role|target_name) -> {role, target_name, sources:set, matches:[]}
                }
            role = (r.get("target_role") or "unknown").strip() or "unknown"
            target_name = (r.get("target_name") or "").strip() or "(unknown)"
            key = f"{role}|{target_name}"
            targets = tx_map[tx_id]["targets"]
            if key not in targets:
                targets[key] = {
                    "target_role": role,
                    "target_name": target_name,
                    "sources": set(),
                    "matches": [],
                }
            src = (r.get("sanction_source_code") or "UNKNOWN").strip() or "UNKNOWN"
            targets[key]["sources"].add(src)
            targets[key]["matches"].append(r)

        # Convert sets to sorted lists and sort matches by final_score desc
        # Preserve transaction order from the paginated tx_ids list.
        ordered_tx_ids = tx_ids or sorted(tx_map.keys())
        for tx_id in ordered_tx_ids:
            if tx_id not in tx_map:
                continue
            txg = tx_map[tx_id]
            target_list = []
            for t in txg["targets"].values():
                t["sources"] = sorted(list(t["sources"]))
                t["matches"].sort(key=lambda m: float(m.get("final_score") or 0), reverse=True)
                # Useful summary metrics
                t["match_count"] = len(t["matches"])
                t["max_final_score"] = float(t["matches"][0].get("final_score") or 0) if t["matches"] else 0.0
                target_list.append(t)
            target_list.sort(key=lambda t: float(t.get("max_final_score") or 0), reverse=True)
            txg["targets"] = target_list
            tx_groups.append(txg)

        page_start = (page - 1) * per_page + 1 if total_tx_with_matches > 0 else 0
        page_end = min(page * per_page, total_tx_with_matches) if total_tx_with_matches > 0 else 0

        reporters_map = load_reporters_map()
        reporter_codes = (
            db.query(Transaction.reporter_code)
            .filter(Transaction.batch_id == job.batch_id)
            .filter(Transaction.reporter_code.isnot(None))
            .distinct()
            .order_by(Transaction.reporter_code.asc())
            .all()
        )
        reporter_options = []
        for (code,) in reporter_codes:
            c = (code or "").strip()
            if not c:
                continue
            nm = reporters_map.get(c)
            reporter_options.append({"code": c, "name": nm, "label": format_reporter_label(c, nm)})

        sanction_source_codes = (
            db.query(ScreeningResult.sanction_source_code)
            .filter(ScreeningResult.job_id == job_id)
            .filter(ScreeningResult.sanction_source_code.isnot(None))
            .distinct()
            .order_by(ScreeningResult.sanction_source_code.asc())
            .all()
        )
        sanction_source_code_list = []
        for (code,) in sanction_source_codes:
            c = (code or "").strip()
            if c:
                sanction_source_code_list.append(c)

        sources_by_code: dict[str, str] = {}
        if sanction_source_code_list:
            for code, name in (
                db.query(SanctionSource.code, SanctionSource.name)
                .filter(SanctionSource.code.in_(sanction_source_code_list))
                .all()
            ):
                c = (code or "").strip()
                n = (name or "").strip()
                if c and n:
                    sources_by_code[c] = n

        sanction_source_options = []
        for c in sanction_source_code_list:
            name = sources_by_code.get(c)
            label = f"{c} — {name}" if name else c
            sanction_source_options.append({"code": c, "label": label})

        category_code = (getattr(batch, "source_type", None) or "").strip() or None
        # Fallback for older batches that didn't persist source_type at import time.
        if not category_code and job.batch_id is not None:
            form_candidates = (
                db.query(Transaction.form_no, func.count(Transaction.id).label("cnt"))
                .filter(Transaction.batch_id == job.batch_id)
                .filter(Transaction.form_no.isnot(None))
                .group_by(Transaction.form_no)
                .order_by(func.count(Transaction.id).desc())
                .limit(20)
                .all()
            )
            for form_no, _cnt in form_candidates:
                detected = detect_form_category(form_no, [])
                if detected:
                    category_code = detected
                    break

        category_info = FORM_CATEGORY_MAP.get(category_code or "", None)
        category_label = category_info.get("label") if category_info else category_code
        category_desc = category_info.get("description") if category_info else None

        return render_template(
            "screening_results.html",
            job=job,
            batch=batch,
            results=results,
            tx_groups=tx_groups,
            page=page,
            per_page=per_page,
            per_page_options=[5, 10, 20, 50],
            min_score=min_score,
            total_tx_with_matches=total_tx_with_matches,
            total_pages=total_pages,
            page_start=page_start,
            page_end=page_end,
            reporter_code_selected=reporter_code_selected,
            reporter_options=reporter_options,
            sanction_source_selected=sanction_source_selected,
            sanction_source_options=sanction_source_options,
            kpi_total_matches=kpi_total_matches,
            kpi_sanctions_detected=kpi_sanctions_detected,
            category_code=category_code,
            category_label=category_label,
            category_desc=category_desc,
        )
    finally:
        db.close()

@web_bp.route("/search", methods=["GET"])
def search_by_name():
    db = SessionLocal()
    try:
        query_name = ""
        query_dob = ""
        query_citizenship = ""
        results = None

        if request.method == "POST":
            query_name = (request.form.get("name") or "").strip()
            query_dob = (request.form.get("dob") or "").strip()
            query_citizenship = (request.form.get("citizenship") or "").strip()

            if not query_name:
                flash("Nama wajib diisi untuk pencarian.", "warning")
                results = []
            else:
                results = search_single_entity(
                    db=db,
                    name=query_name,
                    dob=query_dob or None,
                    citizenship=query_citizenship or None,
                    limit=50,
                    name_threshold=40.0,
                    final_threshold=50.0,
                )

        return render_template(
            "search.html",
            query_name=query_name,
            query_dob=query_dob,
            query_citizenship=query_citizenship,
            results=results,
        )
    finally:
        db.close()