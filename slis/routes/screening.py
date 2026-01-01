from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from celery.result import AsyncResult

from slis.db import SessionLocal
from slis.models import ScreeningJob, UploadBatch
from slis.celery_app import celery_app

from slis.services.screening import search_entities_bulk


screening_bp = Blueprint("screening", __name__)

@screening_bp.route("/jobs", methods=["POST"])
def create_screening_job():
   
    data = request.get_json() or {}
    batch_id = data.get("batch_id")
    if not batch_id:
        return jsonify({"error": "batch_id is required"}), 400

    db = SessionLocal()
    try:
        batch = db.get(UploadBatch, batch_id)
        if batch is None:
            return jsonify({"error": f"upload_batch id={batch_id} not found"}), 404

        job = ScreeningJob(
            batch_id=batch_id,
            status="PENDING",
            threshold_name_score=data.get("threshold_name_score", 70.0),
            threshold_score=data.get("threshold_score", 60.0),
            created_at=datetime.now(timezone.utc),
            created_by=data.get("created_by"),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Kirim ke Celery
        async_result = celery_app.send_task(
            "slis.run_screening_task",
            args=[job.id],
        )

        # Persist task id for progress/cancel while still PENDING
        job.celery_task_id = async_result.id
        db.commit()

        return jsonify(
            {
                "job_id": job.id,
                "celery_task_id": async_result.id,
                "status": job.status,
            }
        )
    finally:
        db.close()


@screening_bp.route("/jobs/<int:job_id>/cancel", methods=["POST"])
def cancel_screening_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(ScreeningJob, job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job.status in ["SUCCESS", "DONE", "FAILURE", "FAILED", "CANCELED"]:
            return jsonify({
                "job_id": job.id,
                "status": job.status,
                "message": "Job already finished"
            }), 409

        # Mark as canceled first (so worker can observe it)
        job.status = "CANCELED"
        job.finished_at = datetime.now(timezone.utc)
        if not job.error_message:
            job.error_message = "Canceled by user"
        db.commit()

        if job.celery_task_id:
            try:
                celery_app.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")
            except Exception:
                # Even if revoke fails, we keep DB as CANCELED
                pass

        return jsonify({"job_id": job.id, "status": "CANCELED"})
    finally:
        db.close()


@screening_bp.route("/jobs/<int:job_id>/progress", methods=["GET"])
def get_screening_progress(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(ScreeningJob, job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job.status in ["SUCCESS", "DONE"]:
            return jsonify({
                "job_id": job.id,
                "status": "SUCCESS",
                "processed": job.total_transactions,
                "total": job.total_transactions,
                "percent": 100,
                "matches": job.total_matches,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            })
        
        if job.status == "FAILURE":
             return jsonify({
                "job_id": job.id,
                "status": "FAILURE",
                "percent": 0,
                "error": job.error_message
            })

        response = {
            "job_id": job.id,
            "status": job.status,
            "DEBUG_MODE": "ACTIVE",
            "processed": job.processed_transactions,
            "total": job.total_transactions,
            "percent": job.progress_percentage or 0,
            "matches": job.total_matches,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }

        # Pas job RUNNING, ambil data Real-time dari Redis
        if job.status == "RUNNING" and job.celery_task_id:
            # AsyncResult un5uk mengambil meta dari Redis
            task = celery_app.AsyncResult(job.celery_task_id)

            print(f"FLASK DEBUG: Job {job_id} | State: {task.state} | Info: {task.info}")
            
            if isinstance(task.info, dict) and 'percent' in task.info:
                data = task.info
                response["status"] = "RUNNING"
                response["processed"] = data.get('current', job.processed_transactions)
                response["total"] = data.get('total', job.total_transactions)
                response["percent"] = data.get('percent', job.progress_percentage)
                response["matches"] = data.get('matches', job.total_matches)
            
            elif task.state == 'SUCCESS':
                response["status"] = "SUCCESS"
                response["percent"] = 100
                response["processed"] = job.total_transactions

        return jsonify(response)

    finally:
        db.close()

@screening_bp.route("/quick-search-bulk", methods=["POST"])
def quick_search_bulk():
    data = request.get_json() or {}
    queries = data.get("queries", [])
    
    # Default config
    threshold = float(data.get("threshold", 60.0))
    limit = int(data.get("limit", 10))

    if not queries:
        return jsonify({"error": "Queries list cannot be empty"}), 400

    db = SessionLocal()
    try:
        results = search_entities_bulk(
            db=db,
            queries=queries,
            limit=limit,
            name_threshold=threshold - 10,
            final_threshold=threshold
        )
        
        return jsonify({
            "status": "ok",
            "total_queries": len(queries),
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()