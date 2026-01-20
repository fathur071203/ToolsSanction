import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure repo root is on sys.path so `import slis` works when running:
#   python scripts/init_db.py
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

load_dotenv()


def main() -> int:
    # Import engine (uses DATABASE_URL if set, otherwise falls back to local SQLite)
    from slis.db import engine

    # IMPORTANT: models use their own Base metadata
    from slis import models

    models.Base.metadata.create_all(bind=engine)
    print("OK: database schema created/verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
