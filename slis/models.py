from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Date,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"

Base = declarative_base()




class SanctionSource(Base):
    __tablename__ = "sanction_source"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    column_mapping: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    snapshots: Mapped[list["SanctionSnapshot"]] = relationship(
        "SanctionSnapshot",
        back_populates="source",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    entities: Mapped[list["SanctionEntity"]] = relationship(
        "SanctionEntity",
        back_populates="source",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )


class SanctionSnapshot(Base):
    __tablename__ = "sanction_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sanction_source.id"), nullable=False
    )

    version_label: Mapped[str | None] = mapped_column(Text)
    effective_date: Mapped[Date | None] = mapped_column(Date)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    record_count: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    raw_file_name: Mapped[str | None] = mapped_column(Text)
    raw_file_hash: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    source: Mapped["SanctionSource"] = relationship(
        "SanctionSource",
        back_populates="snapshots",
    )
    entities: Mapped[list["SanctionEntity"]] = relationship(
        "SanctionEntity",
        back_populates="snapshot",
    )


class SanctionEntity(Base):
    __tablename__ = "sanction_entity"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sanction_source.id"), nullable=False
    )
    snapshot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sanction_snapshot.id"), nullable=True
    )

    external_id: Mapped[str | None] = mapped_column(Text)

    primary_name: Mapped[str] = mapped_column(Text, nullable=False)
    primary_name_normalized: Mapped[str | None] = mapped_column(Text)

    date_of_birth_raw: Mapped[str | None] = mapped_column(Text)
    dob_year: Mapped[int | None] = mapped_column(Integer)
    dob_month: Mapped[int | None] = mapped_column(Integer)
    dob_day: Mapped[int | None] = mapped_column(Integer)

    citizenship: Mapped[str | None] = mapped_column(Text)
    citizenship_normalized: Mapped[str | None] = mapped_column(Text)

    country_of_birth: Mapped[str | None] = mapped_column(Text)
    country_of_residence: Mapped[str | None] = mapped_column(Text)
    place_of_birth: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)

    entity_type: Mapped[str | None] = mapped_column(Text)
    programs: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extra_data: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    source: Mapped["SanctionSource"] = relationship(
        "SanctionSource",
        back_populates="entities",
    )
    snapshot: Mapped["SanctionSnapshot | None"] = relationship(
        "SanctionSnapshot",
        back_populates="entities",
    )
    aliases: Mapped[list["SanctionAlias"]] = relationship(
        "SanctionAlias",
        back_populates="entity",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    # ScreeningResult is no longer FK-linked to sanction_entity (sanctions now sourced from JSON).


class SanctionAlias(Base):
    __tablename__ = "sanction_alias"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sanction_entity.id"), nullable=False
    )

    alias_name: Mapped[str] = mapped_column(Text, nullable=False)
    alias_name_normalized: Mapped[str | None] = mapped_column(Text)
    alias_type: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    entity: Mapped["SanctionEntity"] = relationship(
        "SanctionEntity",
        back_populates="aliases",
    )


# ---------- 2. UPLOAD BATCH & TRANSACTIONS ----------


class UploadBatch(Base):
    __tablename__ = "upload_batch"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    total_rows = Column(Integer, default=0)
    source_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    row_count = Column(Integer, default=0)

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="batch",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    screening_jobs: Mapped[list["ScreeningJob"]] = relationship(
        "ScreeningJob",
        back_populates="batch",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batch.id"), nullable=False)
    form_no = Column(String(100), nullable=True)
    reporter_code = Column(String(50), nullable=True)
    form_period_raw = Column(String(50), nullable=True)
    record_no = Column(String(100), nullable=True)

    sender_name = Column(String(255), nullable=True)
    sender_name_normalized = Column(String(255), nullable=True)
    sender_country = Column(String(100), nullable=True)
    sender_dob = Column(String(50), nullable=True)

    receiver_name = Column(String(255), nullable=True)
    receiver_name_normalized = Column(String(255), nullable=True)
    receiver_country = Column(String(100), nullable=True)
    receiver_dob = Column(String(50), nullable=True)

    amount = Column(Float, nullable=True)
    amount_raw = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=True)
    transaction_date = Column(String(50), nullable=True)
    reference_number = Column(String(100), nullable=True)

    origin_city_code = Column(String(100), nullable=True)
    destination_country = Column(String(100), nullable=True)
    purpose_code = Column(String(255), nullable=True)
    frequency_raw = Column(String(50), nullable=True)

    created_at_raw = Column(String(50), nullable=True)

    # Relationships
    batch = relationship(
        "UploadBatch",
        back_populates="transactions",
    )
    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        "ScreeningResult",
        back_populates="transaction",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )


class ScreeningJob(Base):
    __tablename__ = "screening_job"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batch.id"), nullable=False)

    status = Column(String(50), default="PENDING")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    threshold_name_score = Column(Float, default=70.0)
    threshold_score = Column(Float, default=60.0)

    # Optional filter: restrict matching to specific sanction source code(s).
    # Stored as comma-separated codes, e.g. "OFAC" or "OFAC,UN". Null/empty means ALL.
    sanction_source_filter = Column(Text, nullable=True)

    total_transactions = Column(Integer, default=0)
    processed_transactions = Column(Integer, default=0)
    total_sanctions = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)

    celery_task_id = Column(String(255), nullable=True)

    # Relationships
    batch = relationship(
        "UploadBatch",
        back_populates="screening_jobs",
    )
    results: Mapped[list["ScreeningResult"]] = relationship(
        "ScreeningResult",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class ScreeningResult(Base):
    __tablename__ = "screening_result"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("screening_job.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    # NOTE: sanctions are now sourced from JSON, not DB.
    # Keep this nullable and without FK so results can be stored without sanction_entity rows.
    sanction_entity_id = Column(Integer, nullable=True)

    # Stable identifier from JSON (string-friendly), plus human-readable source code.
    sanction_external_id = Column(String(255), nullable=True)
    sanction_source_code = Column(String(50), nullable=True)

    sanction_source_id = Column(Integer, nullable=True)
    sanction_snapshot_id = Column(Integer, nullable=True)

    target_role = Column(String(20), nullable=False)  # 'sender' or 'receiver'

    target_name = Column(String(255), nullable=True)
    target_name_normalized = Column(String(255), nullable=True)
    target_country = Column(String(100), nullable=True)

    sanction_name = Column(String(255), nullable=True)
    sanction_name_normalized = Column(String(255), nullable=True)
    sanction_dob_raw = Column(String(100), nullable=True)
    sanction_citizenship = Column(String(100), nullable=True)

    name_score = Column(Float, nullable=True)
    dob_score = Column(Float, nullable=True)
    citizenship_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)

    dob_match_type = Column(String(100), nullable=True)
    weighting_scheme = Column(String(100), nullable=True)
    weights_used = Column(JSON, nullable=True)
    geographic_insights = Column(JSON, nullable=True)


    matched_dob_text = Column(String(255), nullable=True)
    matched_citizenship = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship(
        "ScreeningJob",
        back_populates="results",
    )
    transaction = relationship(
        "Transaction",
        back_populates="screening_results",
    )
