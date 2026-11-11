#!/usr/bin/env python3
"""
collect_linescans.py

Recursively finds LineScan files and copies them into three organized folders,
prefixing each file with its numbered parent folder name:
  - collected_ome_tif/    -> 1_LineScan-*_Cycle*_Ch3_*.ome.tif
  - collected_xml/        -> 1_LineScan-*.xml
  - collected_ch3source/  -> 1_LineScan-*Ch3Source.tif

Usage:
    python3 collect_linescans.py /path/to/your/root/data/folder

Example:
    python3 collect_linescans.py ~/Desktop/Experiments
"""

import sys
import hashlib
import shutil
from pathlib import Path


def collect_linescans(root_dir: Path, output_dir: Path | None = None, log=print):
    """Collect scans, returning destination-to-source paths.

    The CLI writes beside the original folder; the app supplies its run folder.
    """
    root_dir = root_dir.resolve()
    if not root_dir.is_dir():
        raise ValueError(f"'{root_dir}' is not a valid directory.")

    # Keep the original CLI location unless the app supplies an isolated run.
    parent_dir = Path(output_dir).resolve() if output_dir is not None else root_dir.parent
    if parent_dir == root_dir or (output_dir is not None and root_dir.is_relative_to(parent_dir)):
        raise ValueError('Output must not contain the source folder.')
    parent_dir.mkdir(parents=True, exist_ok=True)
    ome_out = parent_dir / "collected_ome_tif"
    xml_out = parent_dir / "collected_xml"
    src_out = parent_dir / "collected_ch3source"

    ome_out.mkdir(exist_ok=True)
    xml_out.mkdir(exist_ok=True)
    src_out.mkdir(exist_ok=True)

    log(f"Scanning:            {root_dir}")
    log(f"Output (ome.tif):    {ome_out}")
    log(f"Output (xml):        {xml_out}")
    log(f"Output (Ch3Source):  {src_out}")
    log("-" * 60)

    ome_count = 0
    xml_count = 0
    src_count = 0

    sources = {}
    used = set()
    prefixes = {}

    def numbered_dest(folder: Path, file: Path) -> Path:
        """Prefix filename with the numbered parent folder (e.g. '1_LineScan-...')."""
        # Keep every file from a scan together if two branches share a number.
        scan = (file.parent, file.name.split('_Cycle')[0].split('-Cycle')[0].removesuffix('.xml'))
        if scan not in prefixes:
            number = file.parent.name
            identity = (number, scan[1])
            if identity in used:
                number = hashlib.sha256(str(file.parent.relative_to(root_dir)).encode()).hexdigest()[:10] + '_' + number
            used.add(identity)
            prefixes[scan] = number
        number = prefixes[scan]
        dest = folder / f"{number}_{file.name}"
        return dest

    def copy_bytes_only(src: Path, dst: Path):
        """Copy only raw file bytes, skipping all permission/metadata operations."""
        with open(src, "rb") as src_f, open(dst, "wb") as dst_f:
            shutil.copyfileobj(src_f, dst_f)
        sources[dst] = src

    def inputs(pattern):
        return sorted(file for file in root_dir.rglob(pattern)
                      if not file.is_relative_to(ome_out)
                      and not file.is_relative_to(xml_out)
                      and not file.is_relative_to(src_out)
                      and not (output_dir is not None and file.is_relative_to(parent_dir)))

    # Collect .ome.tif files
    for file in inputs("LineScan-*_Cycle*_Ch3_*.ome.tif"):
        dest = numbered_dest(ome_out, file)
        copy_bytes_only(file, dest)
        log(f"[ome.tif]    {dest.name}")
        ome_count += 1

    # Collect .xml files
    for file in inputs("LineScan-*.xml"):
        dest = numbered_dest(xml_out, file)
        copy_bytes_only(file, dest)
        log(f"[xml]        {dest.name}")
        xml_count += 1

    # Collect Ch3Source.tif files
    for file in inputs("LineScan-*Ch3Source.tif"):
        dest = numbered_dest(src_out, file)
        copy_bytes_only(file, dest)
        log(f"[Ch3Source]  {dest.name}")
        src_count += 1

    log("-" * 60)
    log("Done!")
    log(f"  .ome.tif files copied:   {ome_count}  ->  {ome_out}")
    log(f"  .xml files copied:       {xml_count}  ->  {xml_out}")
    log(f"  Ch3Source files copied:  {src_count}  ->  {src_out}")
    return sources


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 collect_linescans.py <root_directory>")
        print("Example: python3 collect_linescans.py ~/Desktop/Experiments")
        sys.exit(1)

    collect_linescans(Path(sys.argv[1]).expanduser().resolve())
