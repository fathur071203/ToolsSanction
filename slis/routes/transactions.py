from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from slis.db import SessionLocal
from slis.services.transactions import create_transaction_batch

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions/upload-txt", methods=["POST"])
def upload_transaction_txt():

    if "file" not in request.files:
        return jsonify({"error": "file field is required"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(file.filename)
    created_by = request.form.get("created_by")  

    db = SessionLocal()
    try:
        batch = create_transaction_batch(db, file, filename, created_by=created_by)
        
        sample_rows = []
        for tx in batch.transactions[:5]:
            sample_rows.append(
                {
                    "id": tx.id,
                    "record_no": tx.record_no,
                    "sender_name": tx.sender_name,
                    "receiver_name": tx.receiver_name,
                    "destination_country": tx.destination_country,
                    "amount": str(tx.amount) if tx.amount is not None else None,
                }
            )

        return jsonify(
            {
                "batch_id": batch.id,
                "filename": batch.filename,
                "row_count": batch.row_count,
                "source_type": batch.source_type,
                "sample_transactions": sample_rows,
            }
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()
