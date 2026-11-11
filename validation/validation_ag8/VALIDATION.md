# Ag8 baseline validation

Validated November 11, 2026 using the desktop app's collection, macro generation, Fiji detection, detection import, and result export functions. Input: `Ag8 Baseline/collected_ome_tif`. Original sample files were preserved.

| Check | Result |
| --- | --- |
| Images analyzed | 84 unique scans |
| RBC counts matching saved baseline CSV | 84/84 |
| Frame periods matching supplied timing TSV | 84/84 |
| Flux matching baseline count / frame period | 84/84 |
| Automatic annotation pixels matching saved TIFFs | 84/84 |
| Total RBC count | 10,436 in both outputs |
| Frame period range | 1.1100–1.5912 s |
| Manual fallback durations | 0 |

The saved baseline CSV uses 1.0000 s and consequently stores counts in its flux column. The app's `RBC Count` matches that count; its `Duration (s)` contains XML frame period and its `Flux (RBCs/s)` contains count divided by frame period. Scan 1: 48 RBCs / 1.464 s = 32.786885 RBCs/s.

Fiji analysis was completed in four independent batches using the generated macro commands, after an initial serial run. All batches exited successfully. Counts and annotations were compared for every scan; frame periods were checked against the supplied `collected_xml/linescan_periods_batch.tsv` rather than the newly generated timing table.

Desktop smoke checks passed: initialize the app, load scan 1, add a line, save 49 RBCs with flux 49 / 1.464, undo, and save 48 RBCs. Review checks used a temporary copy. The three existing workflow unit tests and launcher shell syntax check passed.

The app now starts from `Ag8 Baseline/L4 Line scans Baseline` and calls `collect_linescans_updated.py` automatically. A subsequent collection check from that original folder produced 84 OME images, 84 XML files, and 84 Ch3Source images. All 252 files match the supplied collected copies byte-for-byte, and all 84 records have identical metadata to the detection validation above. See `raw_collection/collection_validation.json`. Detection was not rerun after this integration because the input image bytes and metadata are identical and the detection macro is unchanged. Four workflow tests pass, including standalone collector output and metadata pairing when scan folder names collide.

See `baseline_comparison.csv` for per-image comparisons, `validation_summary.json` for totals, `RBC_Results_sorted.csv` for app measurements, and `session.json` for a resumable review session. This checks agreement with the supplied baseline, not independent manual labeling accuracy.

Regenerate the comparison from the project directory:

```sh
.venv/bin/python tools/validate_ag8.py validation/validation_ag8
```
