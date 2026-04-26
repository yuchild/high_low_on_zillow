#!/usr/bin/env python

from high_low_on_zillow.ingestion.downloader import download_enabled_zillow_datasets


def main() -> None:
    results = download_enabled_zillow_datasets()

    print("\nZillow download results:")
    for result in results:
        print(
            f"- dataset_family={result.dataset_family} "
            f"status={result.status} "
            f"bytes_written={result.bytes_written} "
            f"path={result.local_path}"
        )


if __name__ == "__main__":
    main()