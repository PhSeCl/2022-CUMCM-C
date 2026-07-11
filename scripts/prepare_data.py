"""Convert the competition workbook into versionable machine-readable files."""

from __future__ import annotations

import argparse
from pathlib import Path

from cumcm2022c.data.convert import convert_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="path to the source XLSX")
    parser.add_argument("--output", type=Path, required=True, help="output directory")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = convert_workbook(args.source, args.output)
    print(f"source sha256: {manifest['source']['sha256']}")
    for sheet in manifest["sheets"]:
        print(
            f"{sheet['name']} -> {sheet['file']}: "
            f"{sheet['rows']} rows x {sheet['columns']} columns, sha256={sheet['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
