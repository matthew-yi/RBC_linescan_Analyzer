"""Compare a completed desktop workflow run with the supplied Ag8 baseline.

Usage: .venv/bin/python tools/validate_ag8.py validation/validation_ag8
"""
import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))

from PIL import Image, ImageChops
from rbc_workflow import import_detections, result_row


def compare(run, baseline):
    if not (run / 'complete.txt').exists():
        raise RuntimeError('Fiji has not completed the validation run.')
    records_path = run / 'session.json'
    if not records_path.exists():
        records = json.loads((run / 'records.json').read_text())
        import_detections(records, run)
    records = json.loads(records_path.read_text())
    with (baseline / 'collected_ome_tif/RBC Results_sorted.csv').open() as handle:
        reference = {row['Image']: row for row in csv.DictReader(handle)}
    timing_text = (baseline / 'collected_xml/linescan_periods_batch.tsv').read_text()
    timing = {
        (row['File'], int(row['Cycle']), int(row['FrameIndex'])): float(row['framePeriod'])
        for row in csv.DictReader(io.StringIO(timing_text), delimiter='\t')
    }
    comparisons = []
    for record in records:
        row = result_row(record)
        name = row['Image']
        ref = reference[name]
        scan, suffix = name.split('_Cycle')
        cycle = int(suffix.split('_')[0])
        frame = int(suffix.rsplit('_', 1)[1].split('.')[0])
        period = timing[(scan + '.xml', cycle, frame)]
        count = int(ref['RBC Count'])
        old_annotation = baseline / 'collected_ome_tif/RBC_Annotated' / (name.removesuffix('.tif') + '_annotated.tif')
        new_annotation = run / 'RBC_Annotated' / (name + '_annotated.tif')
        with Image.open(old_annotation) as old, Image.open(new_annotation) as new:
            identical = old.size == new.size and ImageChops.difference(old.convert('RGB'), new.convert('RGB')).getbbox() is None
        comparisons.append({
            'Image': name,
            'Baseline Count': count,
            'App Count': row['RBC Count'],
            'Count Matches': count == row['RBC Count'],
            'Baseline Frame Period (s)': period,
            'App Frame Period (s)': row['Duration (s)'],
            'Period Matches': math.isclose(period, row['Duration (s)'], rel_tol=1e-9),
            'Expected Flux (RBCs/s)': count / period,
            'App Flux (RBCs/s)': row['Flux (RBCs/s)'],
            'Flux Matches': math.isclose(count / period, row['Flux (RBCs/s)'], rel_tol=1e-9),
            'Annotation Pixels Match': identical,
        })
    with (run / 'baseline_comparison.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    summary = {
        'reference_images': len(reference),
        'analyzed_images': len(comparisons),
        'unique_images': len({r['Image'] for r in comparisons}),
        'matching_counts': sum(r['Count Matches'] for r in comparisons),
        'matching_frame_periods': sum(r['Period Matches'] for r in comparisons),
        'matching_corrected_flux': sum(r['Flux Matches'] for r in comparisons),
        'identical_annotations': sum(r['Annotation Pixels Match'] for r in comparisons),
        'baseline_total_count': sum(r['Baseline Count'] for r in comparisons),
        'app_total_count': sum(r['App Count'] for r in comparisons),
        'frame_period_min_s': min(r['App Frame Period (s)'] for r in comparisons),
        'frame_period_max_s': max(r['App Frame Period (s)'] for r in comparisons),
        'fallback_durations': sum(r.get('duration_source') != 'frame metadata' for r in records),
    }
    (run / 'validation_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    assert set(reference) == {r['Image'] for r in comparisons}, 'Image set mismatch'
    assert all(r[key] for r in comparisons for key in ('Count Matches', 'Period Matches', 'Flux Matches', 'Annotation Pixels Match')), 'See baseline_comparison.csv for differences'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--baseline', type=Path, default=Path('Ag8 Baseline'))
    args = parser.parse_args()
    compare(args.run, args.baseline)
