# RBC Linescan Analyzer

This folder contains the application only. Copy this whole folder to your computer.

## First-time setup

1. Install Python 3.10 or newer with Tkinter/Tk support.
2. Double-click **First Time Setup.command** on Mac or **First Time Setup.bat** on Windows. Internet access is required to install Pillow. Setup creates a Python environment for this computer; do not copy an environment from another computer.
3. Install Fiji from https://fiji.sc/ if it is not already installed. Setup checks common locations but does not install Python or Fiji automatically.

## Launch and analyze

Double-click **Launch RBC Analyzer.command** on Mac or **Launch RBC Analyzer.bat** on Windows. Use Browse to select the Fiji executable on your computer.

Choose the original experiment folder containing the numbered scan subfolders, then click **Run entire folder**. The app automatically collects images and XML, reads frame periods, counts RBCs in Fiji, and calculates flux as count divided by frame period in seconds. A progress bar tracks completed images.

Results go into a separate folder beside your experiment, named `<experiment> - RBC Analysis - <date and time>`.

## Review

The separate linescan editor opens after analysis. Use **Add / remove RBC lines** for left-click to add and right-click to remove, or choose **Pan image** to drag. Hold **Space** to temporarily pan and release to return to the selected mode. Press **+** or **−** to zoom; **=** and the numeric keypad also work. Side tools provide undo, save, and navigation. The mouse wheel scrolls from anywhere in the editor; Ctrl + wheel zooms. Counts, frame periods, and flux appear beside the image.

**Save / Next**, Previous, and closing the editor save your review. Closing the editor leaves the analyzer open; use **Open editor** to return. To continue a previous run, choose **Resume saved review** and select its `session.json`.

## Terminal alternatives

Mac/Linux setup: `python3 app/install_rbc.py`

Windows setup: `py -3 app\install_rbc.py`

Mac/Linux launch after setup: `.venv/bin/python app/rbc_app.py`

Windows launch after setup: `.venv\Scripts\python.exe app\rbc_app.py`

Only Pillow is installed through pip. Tkinter comes with the Python installation, and Fiji is installed separately.

## Contrast, manual counting, and final spreadsheets

- **Brightness / Contrast** sliders change only the display. **Reset B&C** restores it. Counts and source image pixels are unchanged.
- **Clear, edit manually** clears all lines and sets the count to zero. Click each streak to add RBCs manually. Undo restores the previous lines.
- **Revert to original** restores the automatic lines and count, resets B&C, and restores the preserved first annotated TIFF when saved. New runs preserve it in `original_annotations/`. Older sessions without that backup restore automatic line coordinates on the original preview.
- **Finish / export** saves the current image and opens any remaining unreviewed image. Once every image is reviewed, the app automatically writes `RBC_Final_Results.xlsx` and `RBC_Final_Results.csv` in the run folder.

Final exports contain automatic count, net lines added, net lines removed, final RBC count, frame period, and corrected flux for each image. Final count = automatic count + added − removed. Final flux = final count / frame period in seconds. Later saved edits refresh the final files; incomplete saved reviews remove stale final files and retain the working results.


The Excel **Results** sheet follows the Ag8 workbook's core columns: Line scan #, # of lines, pixels/line, line scan period (s), total time (s), # of RBCs, and # RBCs/s. Headers are on row 2; flux cells contain Excel formulas such as `F3/E3`, with calculated values already cached. The **Review Details** sheet contains filenames and the automatic counts, net additions/removals, final counts, frame periods, and flux. The CSV retains this detailed edit table.
