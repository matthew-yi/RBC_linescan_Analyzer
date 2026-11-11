#!/usr/bin/env python3
"""
sort_rbc_results.py

Re-sorts RBC_Results.csv numerically by the leading scan number in the Image column.

Usage:
    python3 sort_rbc_results.py RBC_Results.csv

Output:
    RBC_Results_sorted.csv  (saved alongside the input file)
"""

import sys
import csv
import re
from pathlib import Path


def sort_csv(input_path: Path):
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    def scan_number(row):
        match = re.match(r"^(\d+)_", row["Image"])
        return int(match.group(1)) if match else float("inf")

    rows.sort(key=scan_number)

    output_path = input_path.parent / (input_path.stem + "_sorted.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Sorted {len(rows)} rows -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sort_rbc_results.py RBC_Results.csv")
        sys.exit(1)

    sort_csv(Path(sys.argv[1]).expanduser().resolve())
