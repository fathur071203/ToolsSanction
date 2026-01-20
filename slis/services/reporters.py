from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def reporters_json_path() -> Path:
    return (_repo_root() / "data" / "reporters.json").resolve()


def load_reporters_map() -> Dict[str, str]:
    """Load reporter code->name mapping from data/reporters.json.

    File format:
      {
        "777958110": "PT Syaftraco",
        "777959364": "PT Peniti Money Remittance"
      }

    If the file doesn't exist, returns empty mapping.
    """
    p = reporters_json_path()
    if not p.exists():
        return {}

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: Dict[str, str] = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            code = str(k).strip()
            name = str(v).strip() if v is not None else ""
            if code:
                out[code] = name
    return out


def format_reporter_label(code: str, name: Optional[str]) -> str:
    c = (code or "").strip()
    n = (name or "").strip()
    if not c:
        return "(unknown)"
    if n:
        return f"{c} — {n}"
    return c
