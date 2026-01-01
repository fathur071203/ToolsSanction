from __future__ import annotations

from datetime import datetime, timezone
from celery.utils.log import get_task_logger

# Import Celery app dengan alias
from slis.celery_app import celery_app as celery
from slis.db import SessionLocal
from slis.models import (
    ScreeningJob,
    Transaction,
    SanctionEntity,
    ScreeningResult,
)
from slis.matching.names import (
    normalize_name,
    calculate_advanced_name_score_normed,
    HybridNameIndex,
)
from slis.matching.geo import generate_geographic_insights
from slis.matching.dob import calculate_dob_score_flexible

logger = get_task_logger(__name__)

def compute_component_weights(has_dob: bool, has_citizenship: bool) -> tuple[float, float, float]:
    if has_dob and has_citizenship:
        return 0.50, 0.35, 0.15
    elif has_dob and not has_citizenship:
        return 0.70, 0.30, 0.0
    elif has_citizenship and not has_dob:
        return 0.80, 0.0, 0.20
    else:
        return 1.0, 0.0, 0.0

def compute_final_score(
    name_score: float,
    dob_score: float,
    citizenship_score: float,
    has_dob: bool,
    has_citizenship: bool,
) -> float:
    w_name, w_dob, w_citz = compute_component_weights(has_dob, has_citizenship)
    return (name_score * w_name) + (dob_score * w_dob) + (citizenship_score * w_citz)

def determine_scheme_name(has_dob: bool, has_citizenship: bool) -> str:
    """Helper untuk string weighting_scheme."""
    if has_dob and has_citizenship:
        return "NAME_DOB_CITIZENSHIP"
    elif has_dob:
        return "NAME_DOB"
    elif has_citizenship:
        return "NAME_CITIZENSHIP"
    else:
        return "NAME_ONLY"
    
def normalize_country_code(val: str | None) -> str | None:
    """Helper sederhana untuk normalisasi kode negara (lowercasing)."""
    if not val: return None
    return str(val).lower().strip()

@celery.task(bind=True, name="slis.run_screening_task")
def run_screening_task(self, job_id: int) -> dict:
    """
    Screening job utama dengan batch processing manual (tanpa yield_per).
    """
    db = SessionLocal()
    try:
        job = db.get(ScreeningJob, job_id)
        if not job:
            raise ValueError(f"screening_job id={job_id} not found")

        logger.info(f"[job={job_id}] Starting screening task")

        # 1. Update status awal
        job.celery_task_id = self.request.id
        job.status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Threshold settings
        name_threshold = job.threshold_name_score or 70.0
        final_threshold = job.threshold_score or 60.0

        # 2. Hitung Total Transaksi
        tx_query_base = db.query(Transaction).filter(Transaction.batch_id == job.batch_id)
        total_transactions = tx_query_base.count()

        # 3. Load Sanctions ke Memory (Optimasi)
        sanctions_orm = db.query(SanctionEntity).filter(SanctionEntity.is_active.is_(True)).all()
        
        sanction_rows = []
        for s in sanctions_orm:
            norm_name = s.primary_name_normalized or normalize_name(s.primary_name)
            sanction_rows.append({
                "id": s.id,
                "source_id": s.source_id,
                "snapshot_id": s.snapshot_id,
                "name": s.primary_name,
                "name_norm": norm_name,
                "dob_raw": s.date_of_birth_raw,
                "citizenship": s.citizenship,
                "citizenship_norm": s.citizenship_normalized or normalize_country_code(s.citizenship),
                "source_code": s.source.code if getattr(s, "source", None) else "UNKNOWN",
            })

        sanction_index = HybridNameIndex([s["name_norm"] for s in sanction_rows])

        # Update info job
        job.total_transactions = total_transactions
        job.total_sanctions = len(sanction_rows)
        db.commit()

        # Inisialisasi State di Redis (0%)
        self.update_state(state='PROGRESS', meta={
            'current': 0,
            'total': total_transactions,
            'percent': 0,
            'matches': 0
        })

        logger.info(f"[job={job_id}] Loaded {total_transactions} tx, {len(sanction_rows)} sanctions")

        # 4. LOOP PROCESS (MANUAL BATCHING)
        # Menggantikan yield_per yang error
        BATCH_SIZE = 100
        offset = 0
        
        processed_count = 0
        total_matches = 0
        results_bulk = []
        
        # Logic frekuensi update progress bar
        update_frequency = 1 if total_transactions < 100 else 50

        while True:
            # Ambil chunk data (Pagination)
            tx_chunk = tx_query_base.limit(BATCH_SIZE).offset(offset).all()
            
            if not tx_chunk: break

            for tx in tx_chunk:
                processed_count += 1

                # Allow cancellation (checked at a low frequency)
                if processed_count % 25 == 0:
                    db.expire(job)
                    if job.status == "CANCELED":
                        logger.info(f"[job={job_id}] Canceled by user")
                        self.update_state(state='REVOKED', meta={
                            'current': processed_count,
                            'total': total_transactions,
                            'percent': int((processed_count / (total_transactions or 1)) * 100),
                            'matches': total_matches
                        })
                        return {"job_id": job_id, "status": "CANCELED"}
                
                # Cek Sender dan Receiver
                parties = [
                    {
                        "role": "sender",
                        "raw_name": tx.sender_name,
                        "norm_name": tx.sender_name_normalized,
                        "dob": tx.sender_dob,
                        "country": tx.sender_country
                    },
                    {
                        "role": "receiver",
                        "raw_name": tx.receiver_name,
                        "norm_name": tx.receiver_name_normalized,
                        "dob": tx.receiver_dob,
                        "country": tx.receiver_country
                    }
                ]

                for p in parties:
                    raw_name = p["raw_name"]
                    norm_name = p["norm_name"]
                    
                    if not raw_name: continue
                    target_norm = norm_name or normalize_name(raw_name)
                    if not target_norm: continue

                    # Data Transaksi untuk Matching
                    tx_dob_val = p["dob"]
                    tx_country_norm = normalize_country_code(p["country"])

                    candidate_idxs = sanction_index.filter_indices(target_norm)
                    for idx in candidate_idxs:
                        s = sanction_rows[idx]
                        # 1. Name Score
                        name_score = calculate_advanced_name_score_normed(target_norm, s["name_norm"])
                        if name_score < name_threshold: continue

                        # 2. DOB Score Logic
                        dob_score = 0.0
                        has_dob = False
                        dob_match_type = None
                        
                        # Hanya hitung jika kedua pihak punya data DOB
                        if tx_dob_val and s["dob_raw"]:
                            score, desc = calculate_dob_score_flexible(
                                str(tx_dob_val), 
                                str(s["dob_raw"]), 
                                s["source_code"]
                            )
                            dob_score = float(score)
                            dob_match_type = desc
                            has_dob = True

                        # 3. Citizenship Score Logic
                        citizenship_score = 0.0
                        has_cit = False
                        matched_citizenship_val = None
                        
                        # Hanya hitung jika kedua pihak punya data Country
                        if tx_country_norm and s["citizenship_norm"]:
                            # Exact match pada kode negara yang sudah dinormalisasi (iso2/lower)
                            if tx_country_norm == s["citizenship_norm"]:
                                citizenship_score = 100.0
                                matched_citizenship_val = s["citizenship"] # Simpan nilai asli
                            has_cit = True

                        # 4. Final Score & Scheme Dynamic
                        final_score = compute_final_score(
                            name_score, dob_score, citizenship_score, has_dob, has_cit
                        )
                        
                        scheme_name = determine_scheme_name(has_dob, has_cit)

                        if final_score < final_threshold: continue

                        # 5. Geographic Insights
                        customer_geo = {
                            "Citizenship": p["country"], 
                            "Country_of_Residence": tx.destination_country, 
                            "Place_of_Birth": None
                        }
                        sanction_geo = { "Citizenship": s["citizenship"] }
                        geo_insights = generate_geographic_insights(customer_geo, sanction_geo)

                        total_matches += 1
                        
                        sr = ScreeningResult(
                            job_id=job.id,
                            transaction_id=tx.id,
                            sanction_entity_id=s["id"],
                            sanction_source_id=s["source_id"],
                            sanction_snapshot_id=s["snapshot_id"],
                            
                            target_role=p["role"],
                            target_name=raw_name,
                            target_name_normalized=target_norm,
                            target_country=tx.destination_country,
                            
                            sanction_name=s["name"],
                            sanction_name_normalized=s["name_norm"],
                            sanction_dob_raw=s["dob_raw"],
                            sanction_citizenship=s["citizenship"],
                            
                            name_score=name_score,
                            dob_score=dob_score,
                            citizenship_score=citizenship_score,
                            final_score=final_score,
                            
                            # Simpan metadata dinamis
                            dob_match_type=dob_match_type,
                            matched_dob_text=tx_dob_val if has_dob else None,
                            matched_citizenship=matched_citizenship_val,
                            weighting_scheme=scheme_name, # <--- INI SEKARANG DINAMIS
                            geographic_insights=geo_insights
                        )
                        results_bulk.append(sr)

                # Update Progress ke Redis
                if processed_count % update_frequency == 0 or processed_count == total_transactions:
                    safe_total = total_transactions if total_transactions > 0 else 1
                    percent = int((processed_count / safe_total) * 100)
                    self.update_state(state='PROGRESS', meta={
                        'current': processed_count,
                        'total': total_transactions,
                        'percent': percent,
                        'matches': total_matches
                    })

            # Flush DB per batch
            if len(results_bulk) > 0:
                db.bulk_save_objects(results_bulk)
                db.commit()
                results_bulk = [] # Kosongkan list untuk batch berikutnya
            
            # Geser offset untuk batch selanjutnya
            offset += BATCH_SIZE

        # 5. Update Status Akhir
        # Refresh object job agar session sync
        db.expire(job)
        
        job.processed_transactions = processed_count
        job.total_matches = total_matches
        job.status = "SUCCESS"
        job.finished_at = datetime.now(timezone.utc)
        job.progress_percentage = 100.0
        db.commit()

        logger.info(f"[job={job_id}] Finished. Tx={total_transactions}, Matches={total_matches}")

        return {
            "job_id": job_id,
            "status": "SUCCESS",
            "matches": total_matches
        }

    except Exception as e:
        db.rollback()
        logger.exception(f"[job={job_id}] Failed: {e}")
        try:
            job = db.get(ScreeningJob, job_id)
            if job:
                job.status = "FAILURE"
                job.error_message = str(e)
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        raise e

    finally:
        db.close()