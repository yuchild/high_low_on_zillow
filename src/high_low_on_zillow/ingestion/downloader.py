from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import requests

from high_low_on_zillow.config import get_data_sources
from high_low_on_zillow.paths import RAW_DIR
from high_low_on_zillow.ingestion.manifest import (
    append_manifest_record,
    utc_now_iso,
    write_latest_run_summary,
)


@dataclass
class DownloadResult:
    dataset_family: str
    url: str
    local_path: str
    status: str
    downloaded_at_utc: str
    bytes_written: int


def infer_filename_from_url(url: str, fallback_stub: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if name:
        return name
    return f"{fallback_stub}.csv"


def download_file(url: str, destination: Path, timeout: int = 120) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        total_bytes = 0

        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

    return total_bytes


def download_enabled_zillow_datasets() -> list[DownloadResult]:
    sources = get_data_sources()
    zillow_cfg = sources["zillow_research"]

    if not zillow_cfg.get("enabled", False):
        raise ValueError("zillow_research is disabled in configs/data_sources.yaml")

    raw_subdir = zillow_cfg.get("raw_subdir", "zillow")
    raw_target_dir = RAW_DIR / raw_subdir
    raw_target_dir.mkdir(parents=True, exist_ok=True)

    manifest_csv_path = raw_target_dir / "download_manifest.csv"
    latest_summary_path = raw_target_dir / "latest_download_summary.json"

    results: list[DownloadResult] = []

    for dataset_family, meta in zillow_cfg["datasets"].items():
        if not meta.get("enabled", False):
            continue

        url = (meta.get("url") or "").strip()
        filename_stub = meta.get("filename_stub", dataset_family)

        if not url:
            results.append(
                DownloadResult(
                    dataset_family=dataset_family,
                    url="",
                    local_path="",
                    status="skipped_missing_url",
                    downloaded_at_utc=utc_now_iso(),
                    bytes_written=0,
                )
            )
            continue

        filename = infer_filename_from_url(url, fallback_stub=filename_stub)
        destination = raw_target_dir / filename
        downloaded_at = utc_now_iso()

        try:
            bytes_written = download_file(url, destination)
            result = DownloadResult(
                dataset_family=dataset_family,
                url=url,
                local_path=str(destination),
                status="downloaded",
                downloaded_at_utc=downloaded_at,
                bytes_written=bytes_written,
            )
        except Exception:
            result = DownloadResult(
                dataset_family=dataset_family,
                url=url,
                local_path=str(destination),
                status="failed",
                downloaded_at_utc=downloaded_at,
                bytes_written=0,
            )

        results.append(result)

        append_manifest_record(
            manifest_csv_path,
            {
                "dataset_family": result.dataset_family,
                "url": result.url,
                "local_path": result.local_path,
                "status": result.status,
                "downloaded_at_utc": result.downloaded_at_utc,
                "bytes_written": result.bytes_written,
            },
        )

    write_latest_run_summary(
        latest_summary_path,
        {
            "run_completed_at_utc": utc_now_iso(),
            "results": [r.__dict__ for r in results],
        },
    )

    return results