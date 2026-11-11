# RBC Linescan Analyzer

A desktop workflow around the existing Fiji detection macro. Original scripts and raw images are preserved.

## Folder layout

Use the **First Time Setup** and **Launch RBC Analyzer** files at the top level. Supporting files are organized into:

- `app/`: application, installer, original processing scripts, and Fiji macro.
- `tests/`: automated checks; run `.venv/bin/python -B -m unittest` from the project folder.
- `tools/`: baseline comparison utility.
- `validation/`: saved validation runs, reports, and comparison results.
- `Ag8 Baseline/`: original sample data and baseline results.

Keep these folders together when copying the project to another computer, then run First Time Setup there.

## Setup and launch

Requires Python 3.10+ with Tk, Fiji/ImageJ, and Pillow:

On a new computer, install Python with Tk support, then double-click **First Time Setup.command** (Mac) or **First Time Setup.bat** (Windows). Setup creates a fresh `.venv` for that computer, installs Pillow, and checks imports. A copied environment is backed up; a failed installation restores it. Internet access is needed for package installation. Setup checks common Fiji locations and provides installation instructions if Fiji is missing; it does not install Python or Fiji automatically.

After setup, double-click **Launch RBC Analyzer.command** (Mac) or **Launch RBC Analyzer.bat** (Windows). Select the Fiji executable in the app if needed. To run setup from a terminal, use `python3 app/install_rbc.py` (Mac/Linux) or `py -3 app/install_rbc.py` (Windows).

Manual setup is also available:

```sh
python3 -m pip install -r requirements.txt
python3 app/rbc_app.py
```

On macOS you can also double-click **Launch RBC Analyzer.command** after installing dependencies. The app defaults to `/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx`; use Browse if Fiji is installed elsewhere. On Windows/Linux choose the Fiji executable for your platform.

## Workflow

1. Choose the original experiment folder containing your numbered linescan subfolders. For the Ag8 sample, select `Ag8 Baseline/L4 Line scans Baseline`. The app calls `collect_linescans_updated.py` to create numbered image, XML, and Ch3Source copies, then automatically reads the collected images and XML. An existing `collected_ome_tif` folder is also accepted.
2. Enter a fallback scan duration in seconds. It is used only when a positive frame duration cannot be extracted from XML.
3. Click **Run entire folder** in the analyzer window. Collection, frame timing extraction, Fiji batch analysis, and numeric result sorting run automatically. The progress bar animates during collection, then shows completed images and percentage during Fiji analysis. A separate linescan editor opens after the entire batch completes.
4. Use the editor's side toolbar to choose **Add RBC line**, **Remove RBC line**, or **Pan image**. Left-click performs the selected action; right-click (or Control-click on macOS) removes the nearest line within 12 screen pixels. The image initially fits the viewport width, with vertical scrolling for long scans. Use the mouse wheel to scroll, Ctrl + wheel to zoom, or drag with the Pan tool. Fit width, Fit entire image, 100%, line visibility, undo, and reset to automatic lines are available. Count, frame period, and flux are displayed beside the image.
5. **Save / Next** saves the corrected annotation and measurements, then advances to the next image. Previous also saves. Closing saves the current image. **Resume saved review** opens the run's `session.json` and resumes at the first unreviewed image.

Closing the editor saves and hides it while leaving the analyzer open. Use **Open editor** to return to the current scan. Ctrl+S / Ctrl+Z (Command+S / Command+Z on Mac) save and undo in the editor.
The mouse wheel scrolls the linescan from anywhere inside the editor, including over the side tools and measurements. Ctrl + wheel zooms from those areas as well.

Each run creates a folder beside the selected folder, named after the experiment and a readable date/time, for example `L4 Line scans Baseline - RBC Analysis - 2026-11-11 14-30`. If a name already exists, a suffix such as `(2)` keeps the runs separate. When starting from `collected_ome_tif`, the experiment name comes from its parent folder. Existing runs can still be resumed using their `session.json`.

Each output folder contains:

- `collected_ome_tif`, `collected_xml`, `collected_ch3source`: organized input copies. Duplicate image names receive a path hash to prevent overwriting.
- `linescan_periods_batch.tsv`: frame-level timing metadata.
- `RBC_Annotated`: annotated TIFF images, updated after manual corrections.
- `RBC_Results.csv` and `RBC_Results_sorted.csv`: numeric-sorted measurements, automatic counts, review flags, and duration source. Corrections update counts, flux, lineal density, and interval CV; the detected angle and velocity remain fixed.
- `session.json`: editable line coordinates, metadata, and review state.
- `analysis_input`: TIFF copies with plain filenames for Fiji’s native headless TIFF reader.
- `previews`, `detections`: grayscale display images and original automatic detections. Keep these with the session to resume review.
- `run_analysis.ijm`, `fiji.log`: generated Fiji batch macro and diagnostic output.

## Measurement behavior

The included macOS launcher uses `.venv/bin/python` when a project virtual environment exists.

Detection uses the supplied `RBC_Linescan_Analyzer2.0.ijm` unchanged, including angle search, adaptive detection, and QC fallback. The wrapper bypasses its menus and exports individual line positions. Metadata is matched to the image's cycle and frame rather than taking the last frame in the XML. Missing scale/timing values produce `N/A` for measurements that require them. Metadata warnings appear in the app log. Frame-level timing extraction retains the existing extractor's behavior.

The analyzer expects a **single 2D grayscale linescan per TIFF**, with spatial position across columns and time down rows. A multi-plane TIFF stops the run with an explanation in `fiji.log`; split it before analysis. Collection targets `LineScan-*_Cycle*_Ch3_*.ome.tif` files recursively. A flat folder of TIFFs is also accepted when no matching raw linescans are found.

The editor works from the same 8-bit grayscale display conversion used by Fiji's detector and exports RGB annotations. Raw image bit depth is preserved in the collected copies. Added lines share the detected slope; editing slope or drawing arbitrary segments is not supported. Review is saved on navigation, Save, and close; save periodically during long edits. Automatic detections remain available for reset.

## Ag8 baseline validation

The supplied `Ag8 Baseline` sample contains 84 scans, saved annotations and counts, and a frame-period table. Start from `Ag8 Baseline/L4 Line scans Baseline`; the app collects and analyzes one copy of each scan. Collection outputs are placed in the new run folder so existing baseline results remain available for comparison. Running the collector script directly retains its default behavior of writing collected folders alongside the original folder.

The baseline CSV's flux column contains counts for a 1-second placeholder duration. Compare RBC counts directly, then divide each count by its XML frame period to compare flux in RBCs/s. The app performs this division automatically and stores frame period in `Duration (s)`.

For the recorded validation run, regenerate the per-image comparison and summary with:

```sh
.venv/bin/python tools/validate_ag8.py validation/validation_ag8
```

Outputs are `validation/validation_ag8/baseline_comparison.csv` and `validation/validation_ag8/validation_summary.json`. The comparison checks counts, frame periods against the supplied timing table, corrected flux, and automatic annotation pixels. It checks agreement with the supplied baseline; it does not independently establish biological detection accuracy.
# RBC_linescan_Analyzer
