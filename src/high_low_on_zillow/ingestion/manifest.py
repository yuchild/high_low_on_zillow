from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import json
import pandas as pd


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def append_manifest_record(manifest_csv_path: Path, record: dict) -> None:
    manifest_csv_path.parent.mkdir(parents=True, exist_ok=True)

    if manifest_csv_path.exists():
        df = pd.read_csv(manifest_csv_path)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])

    df.to_csv(manifest_csv_path, index=False)


def write_latest_run_summary(summary_path: Path, payload: dict) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)