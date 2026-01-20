from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Avoid PermissionError when some __pycache__ folders are owned by root
sys.dont_write_bytecode = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_out_path() -> Path:
    return _repo_root() / "data" / "sanctions.json"


def export_sanctions(
    out_path: Path,
    active_only: bool = True,
    batch_size: int = 5000,
    limit: Optional[int] = None,
) -> int:
    # Lazy imports after dont_write_bytecode
    from slis.db import SessionLocal
    from slis.models import SanctionEntity, SanctionSource

    out_path.parent.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        # Build a source_id -> code map once
        source_map: Dict[int, str] = {
            int(s.id): str(s.code)
            for s in db.query(SanctionSource).all()
        }

        exported: List[Dict[str, Any]] = []
        last_id: Optional[int] = None

        while True:
            q = db.query(SanctionEntity)
            if active_only:
                q = q.filter(SanctionEntity.is_active.is_(True))
            if last_id is not None:
                q = q.filter(SanctionEntity.id > last_id)

            q = q.order_by(SanctionEntity.id.asc()).limit(batch_size)
            rows = q.all()
            if not rows:
                break

            for s in rows:
                sid = int(s.id)
                last_id = sid

                payload: Dict[str, Any] = {
                    # Prefer external_id if present; else fallback to DB id
                    "id": str(s.external_id or s.id),
                    "source": source_map.get(int(s.source_id), "UNKNOWN"),
                    "name": s.primary_name,
                    "dob": s.date_of_birth_raw,
                    "citizenship": s.citizenship,
                }

                # Preserve extra columns that are commonly useful
                if getattr(s, "country_of_birth", None):
                    payload["country_of_birth"] = s.country_of_birth
                if getattr(s, "country_of_residence", None):
                    payload["country_of_residence"] = s.country_of_residence
                if getattr(s, "place_of_birth", None):
                    payload["place_of_birth"] = s.place_of_birth
                if getattr(s, "address", None):
                    payload["address"] = s.address
                if getattr(s, "city", None):
                    payload["city"] = s.city
                if getattr(s, "country", None):
                    payload["country"] = s.country
                if getattr(s, "entity_type", None):
                    payload["entity_type"] = s.entity_type
                if getattr(s, "programs", None):
                    payload["programs"] = s.programs
                if getattr(s, "remarks", None):
                    payload["remarks"] = s.remarks

                # Carry through DB extra_data if present
                if getattr(s, "extra_data", None):
                    payload["extra_data"] = s.extra_data

                exported.append(payload)

                if limit is not None and len(exported) >= limit:
                    break

            if limit is not None and len(exported) >= limit:
                exported = exported[:limit]
                break

        out_path.write_text(
            json.dumps(exported, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        return len(exported)

    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export sanctions from DB (sanction_entity) to JSON file for JSON-based screening."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_default_out_path(),
        help="Output path (default: data/sanctions.json)",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include records where is_active=false",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Chunk size for DB reads (default: 5000)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of records to export (for testing)",
    )

    args = parser.parse_args()

    # Ensure repo root is on sys.path so `import slis` works when running:
    #   python scripts/export_sanctions_to_json.py
    sys.path.insert(0, str(_repo_root()))

    count = export_sanctions(
        out_path=args.out,
        active_only=not args.include_inactive,
        batch_size=max(1, int(args.batch_size)),
        limit=args.limit,
    )

    print(f"OK: exported {count} sanctions -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
