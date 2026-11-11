#!/usr/bin/env python3
"""
Batch extract Frame-level PrairieView/Bruker linescan timing metadata from XML files.

What it extracts from each XML file:
  - scanLinePeriod
  - framePeriod

By default, this tool searches one folder for *.xml files and writes a tab-delimited
text file that can be opened in Excel, Prism, R, Python, or Fiji workflows.
Output rows are sorted numerically by the leading scan number in the filename
(e.g. 1_LineScan-... before 10_LineScan-...).

The extractor prioritizes Frame-level metadata:
  PVScan > Sequence > Frame > PVStateShard > PVStateValue

That matters because PrairieView XML files may contain earlier/global values that differ
from the actual Frame-level linescan values.

Examples
--------
1) Batch extract every XML in one folder:
   python extract_linescan_periods_batch.py "/path/to/xml_folder"

2) Batch extract recursively through subfolders:
   python extract_linescan_periods_batch.py "/path/to/xml_folder" --recursive

3) Write output somewhere specific:
   python extract_linescan_periods_batch.py "/path/to/xml_folder" -o "/path/to/output.tsv"

4) Keep only the two requested columns:
   python extract_linescan_periods_batch.py "/path/to/xml_folder" --minimal

5) Run with no folder argument to choose a folder using a file-picker window:
   python extract_linescan_periods_batch.py

6) Disable automatic numeric sort (output in filesystem order instead):
   python extract_linescan_periods_batch.py "/path/to/xml_folder" --no-sort
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional


REQUESTED_KEYS = ("scanLinePeriod", "framePeriod")


def local_name(tag: str) -> str:
    """Return an XML tag without namespace, if present."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def children_named(element: ET.Element, name: str) -> list[ET.Element]:
    """Return direct children with a given local tag name."""
    return [child for child in list(element) if local_name(child.tag) == name]


def first_child_named(element: ET.Element, name: str) -> Optional[ET.Element]:
    """Return first direct child with a given local tag name."""
    for child in list(element):
        if local_name(child.tag) == name:
            return child
    return None


def pvstate_values_from_shard(shard: ET.Element) -> dict[str, str]:
    """Extract key=value pairs from direct PVStateValue children of a PVStateShard."""
    values: dict[str, str] = {}
    for child in children_named(shard, "PVStateValue"):
        key = child.attrib.get("key")
        value = child.attrib.get("value")
        if key is not None and value is not None:
            values[key] = value
    return values


def extract_frame_level_values(xml_file: Path) -> list[dict[str, str]]:
    """
    Extract one row per Frame that contains scanLinePeriod and/or framePeriod.

    Returns detailed rows with file/sequence/frame identifiers so batch outputs remain traceable.
    """
    try:
        tree = ET.parse(xml_file)
    except ET.ParseError as exc:
        raise ValueError(f"XML parse error: {exc}") from exc

    root = tree.getroot()
    rows: list[dict[str, str]] = []

    for sequence in root.iter():
        if local_name(sequence.tag) != "Sequence":
            continue

        sequence_type = sequence.attrib.get("type", "")
        cycle = sequence.attrib.get("cycle", "")

        for frame in children_named(sequence, "Frame"):
            shard = first_child_named(frame, "PVStateShard")
            values = pvstate_values_from_shard(shard) if shard is not None else {}

            scan_line_period = values.get("scanLinePeriod", "")
            frame_period = values.get("framePeriod", "")

            if scan_line_period or frame_period:
                rows.append(
                    {
                        "File": xml_file.name,
                        "FullPath": str(xml_file),
                        "SequenceType": sequence_type,
                        "Cycle": cycle,
                        "FrameIndex": frame.attrib.get("index", ""),
                        "scanLinePeriod": scan_line_period,
                        "framePeriod": frame_period,
                    }
                )

    return rows


def extract_fallback_global_values(xml_file: Path) -> Optional[dict[str, str]]:
    """
    Fallback extraction from the first PVStateShard in the file.

    This is optional and only used with --fallback-global. It is not the preferred behavior,
    because Frame-level metadata is usually the desired source for linescan timing.
    """
    try:
        tree = ET.parse(xml_file)
    except ET.ParseError as exc:
        raise ValueError(f"XML parse error: {exc}") from exc

    root = tree.getroot()
    for shard in root.iter():
        if local_name(shard.tag) == "PVStateShard":
            values = pvstate_values_from_shard(shard)
            scan_line_period = values.get("scanLinePeriod", "")
            frame_period = values.get("framePeriod", "")
            if scan_line_period or frame_period:
                return {
                    "File": xml_file.name,
                    "FullPath": str(xml_file),
                    "SequenceType": "GLOBAL_FALLBACK",
                    "Cycle": "",
                    "FrameIndex": "",
                    "scanLinePeriod": scan_line_period,
                    "framePeriod": frame_period,
                }
    return None


def choose_folder_with_dialog() -> Optional[Path]:
    """Open a simple folder-picker window if no input folder is provided."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:  # pragma: no cover - depends on local GUI availability
        print(f"Could not open folder picker because tkinter is unavailable: {exc}", file=sys.stderr)
        return None

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Choose folder containing PrairieView XML files")
    root.destroy()
    return Path(folder) if folder else None


def find_xml_files(folder: Path, recursive: bool = False) -> list[Path]:
    """Find XML files in a folder."""
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Input is not a folder: {folder}")

    pattern = "**/*.xml" if recursive else "*.xml"
    return sorted(path for path in folder.glob(pattern) if path.is_file())


def scan_number_key(row: dict[str, str]) -> tuple[int, str]:
    """
    Sort key: numeric prefix from the File column, then the full filename.
    '1_LineScan-...' → (1, '1_LineScan-...')
    '10_LineScan-...' → (10, '10_LineScan-...')
    Files without a numeric prefix sort last.
    """
    match = re.match(r"^(\d+)_", row["File"])
    return (int(match.group(1)), row["File"]) if match else (10**9, row["File"])


def sort_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Sort rows numerically by the leading scan number in the File column."""
    return sorted(rows, key=scan_number_key)


def write_rows(output_path: Path, rows: list[dict[str, str]], minimal: bool) -> None:
    """Write rows as tab-delimited text."""
    detailed_fieldnames = [
        "File",
        "SequenceType",
        "Cycle",
        "FrameIndex",
        "scanLinePeriod",
        "framePeriod",
        "FullPath",
    ]
    minimal_fieldnames = ["scanLinePeriod", "framePeriod"]
    fieldnames = minimal_fieldnames if minimal else detailed_fieldnames

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch extract Frame-level scanLinePeriod and framePeriod from a folder of PrairieView/Bruker XML files."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        help="Folder containing XML files. If omitted, a folder-picker window opens when possible.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .tsv/.txt path. Default: <selected folder>/linescan_periods_batch.tsv",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subfolders too.",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Output only two columns: scanLinePeriod and framePeriod.",
    )
    parser.add_argument(
        "--fallback-global",
        action="store_true",
        help="If no Frame-level values are found in a file, fall back to the first global PVStateShard values.",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Disable numeric sort by scan number (output in filesystem order instead).",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    folder: Optional[Path] = args.folder
    if folder is None:
        folder = choose_folder_with_dialog()
        if folder is None:
            print("No folder selected. Provide a folder path, for example:", file=sys.stderr)
            print('  python extract_linescan_periods_batch.py "/path/to/xml_folder"', file=sys.stderr)
            return 1

    try:
        xml_files = find_xml_files(folder, recursive=args.recursive)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if not xml_files:
        print(f"No XML files found in: {folder}", file=sys.stderr)
        return 1

    rows: list[dict[str, str]] = []
    skipped: list[str] = []
    parse_errors: list[str] = []

    for xml_file in xml_files:
        try:
            file_rows = extract_frame_level_values(xml_file)
            if not file_rows and args.fallback_global:
                fallback_row = extract_fallback_global_values(xml_file)
                file_rows = [fallback_row] if fallback_row is not None else []
        except ValueError as exc:
            parse_errors.append(f"{xml_file}: {exc}")
            continue

        if file_rows:
            rows.extend(file_rows)
        else:
            skipped.append(str(xml_file))

    if not args.no_sort:
        rows = sort_rows(rows)

    output_path = args.output if args.output is not None else folder / "linescan_periods_batch.tsv"
    write_rows(output_path, rows, minimal=args.minimal)

    sort_note = "" if args.no_sort else " (sorted numerically by scan number)"
    print(f"XML files scanned: {len(xml_files)}")
    print(f"Rows written: {len(rows)}{sort_note}")
    print(f"Output: {output_path}")

    if skipped:
        print(f"Files with no extracted Frame-level values: {len(skipped)}", file=sys.stderr)
        for item in skipped[:10]:
            print(f"  - {item}", file=sys.stderr)
        if len(skipped) > 10:
            print(f"  ...and {len(skipped) - 10} more", file=sys.stderr)

    if parse_errors:
        print(f"Files with XML parse errors: {len(parse_errors)}", file=sys.stderr)
        for item in parse_errors[:10]:
            print(f"  - {item}", file=sys.stderr)
        if len(parse_errors) > 10:
            print(f"  ...and {len(parse_errors) - 10} more", file=sys.stderr)

    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
