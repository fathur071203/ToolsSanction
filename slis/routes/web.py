from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from datetime import datetime, timezone

from slis.db import SessionLocal
from slis.models import (
    UploadBatch,
    SanctionSource,
    SanctionSnapshot,
    ScreeningJob,
    ScreeningResult,
    Transaction,
    SanctionEntity,
)
from slis.services.transactions import create_transaction_batch
from slis.services.sanctions import import_sanction_file
from slis.celery_app import celery_app
from slis.db import SessionLocal
from slis.services.screening import search_single_entity

web_bp = Blueprint("web", __name__)

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
            tx_source = request.form.get("transaction_source")
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

            threshold_name = float(request.form.get("threshold_name_score") or 70.0)
            threshold_final = float(request.form.get("threshold_score") or 60.0)
            created_by = request.form.get("created_by") or None

            job = ScreeningJob(
                batch_id=batch_id,
                status="PENDING",
                threshold_name_score=threshold_name,
                threshold_score=threshold_final,
                created_at=datetime.now(timezone.utc),
                created_by=created_by,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Trigger Celery Task
            async_result = celery_app.send_task(
                "slis.run_screening_task",
                args=[job.id],
            )

            # Simpan celery_task_id agar progress/cancel bisa bekerja saat masih PENDING
            job.celery_task_id = async_result.id
            db.commit()

            flash(f"Screening Job #{job.id} sedang berjalan...", "success")
            return redirect(url_for("web.screening_jobs"))
       
        return render_template(
            "screening_start.html",
            batches=batches,
            preselected_batch_id=preselected_batch_id,
        )
    finally:
        db.close()


@web_bp.route("/sanctions/upload", methods=["GET", "POST"])
def sanctions_upload_reference():
    db = SessionLocal()
    try:
        sources = db.query(SanctionSource).order_by(SanctionSource.code).all()

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

        return render_template("sanctions_upload.html", sources=sources)
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

        rows = (
            db.query(ScreeningResult, Transaction, SanctionEntity)
            .outerjoin(Transaction, ScreeningResult.transaction_id == Transaction.id)
            .outerjoin(SanctionEntity, ScreeningResult.sanction_entity_id == SanctionEntity.id)
            .filter(ScreeningResult.job_id == job_id)
            .order_by(ScreeningResult.final_score.desc())
            .limit(500)
            .all()
        )
        
        results = []
        for sr, tx, se in rows:
            results.append({
                "id": sr.id,
                "target_role": sr.target_role,
                "transaction_id": tx.id,
                "sender_name": getattr(tx, "sender_name", "") or getattr(tx, "nama_pengirim", "") or "-",
                "receiver_name": getattr(tx, "receiver_name", "") or getattr(tx, "nama_penerima", "") or "-",
                "sanction_name": getattr(se, "primary_name", "") or getattr(se, "name", ""),
                "sanction_source_id": sr.sanction_source_id,
                "target_country": sr.target_country,
                "sanction_citizenship": sr.sanction_citizenship,
                "geographic_insights": sr.geographic_insights,
                "name_score": sr.name_score,
                "dob_score": sr.dob_score,
                "citizenship_score": sr.citizenship_score,
                "final_score": sr.final_score,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
            })

        return render_template(
            "screening_results.html",
            job=job,
            results=results,
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