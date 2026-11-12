# RBC Linescan Analyzer

Lab sharing edition • November 11, 2026

Extract the ZIP and keep this entire folder together on your computer. Run setup once on each computer before launching. No experimental images, results, or computer-specific Python environment are included.

## 1. Install prerequisites

- **Python 3.10 or newer, with Tkinter/Tk:** https://www.python.org/downloads/
- **Fiji:** https://fiji.sc/

Python and Fiji are installed separately. The setup program installs Pillow and checks the application's Python imports; it needs internet access.

## 2. Run first-time setup

| Computer | Double-click |
| --- | --- |
| Mac | `First Time Setup.command` |
| Windows | `First Time Setup.bat` |

Wait for **Python setup complete**. Setup creates a local `.venv` for your computer. If setup is rerun, it backs up the old environment and restores it if installation fails.

## 3. Launch and analyze

| Computer | Double-click |
| --- | --- |
| Mac | `Launch RBC Analyzer.command` |
| Windows | `Launch RBC Analyzer.bat` |

1. Choose the **original experiment folder** containing the numbered scan subfolders. The app collects the OME images and XML automatically.
2. Select your **Fiji executable** using Browse. On Mac it is typically `/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx`; on Windows, select `ImageJ-win64.exe` inside Fiji.
3. Leave **Simultaneous images** at **2** initially. You can choose 1–8 workers; higher values use more CPU and memory. Choose 1 for sequential processing.
4. Set the **Fallback duration** in seconds. It is used only when a frame period cannot be read from XML.
5. Click **Run entire folder**. The progress bar counts completed images across all workers. The editor opens when the batch finishes.

Inputs must be individual 2D grayscale Ch3 linescans, with position across columns and time down rows. The expected raw filename pattern is `LineScan-*_Cycle*_Ch3_*.ome.tif`, with matching XML beside the raw images. An existing `collected_ome_tif` folder is also accepted when its XML is available in the neighboring `collected_xml` folder.

Results are saved beside the experiment in `<experiment> - RBC Analysis - <date and time>`. Raw inputs are preserved. Each image is analyzed once; review and exports retain scan order.

## 4. Review the lines

| Action | Control |
| --- | --- |
| Add a line | Left-click in Add / remove mode |
| Remove a line | Right-click; Control-click also works on Mac |
| Pan | Select Pan image and drag, or hold Space while dragging |
| Zoom | + / − keys, zoom buttons, or Ctrl + mouse wheel |
| Scroll | Mouse wheel anywhere in the editor |
| Save / Undo | Ctrl+S / Ctrl+Z; Command+S / Command+Z on Mac |

- **Brightness / Contrast** changes only the display. **Reset B&C** restores it.
- **Clear, edit manually** removes all lines and starts the count at zero. Click each RBC streak to count manually. Undo can restore the cleared lines.
- **Revert to original** restores the automatic lines/count and resets B&C. New runs preserve the first automatic TIFF for exact restoration when saved.
- **Save / Next**, Previous, Save, and closing the editor save the current review. Closing the editor leaves the analyzer open; **Open editor** brings it back.
- **Resume saved review** opens an existing run's `session.json`. Keep the entire run folder together.

## 5. Finish and get results

Click **Finish / export**, or Save / Next on the last image. If any image remains unreviewed, the app opens it. Once every image is reviewed, the app writes:

- **`RBC_Final_Results.xlsx`**: the Results sheet contains scan number, image dimensions, scan-line period, total frame time, final RBC count, and flux. Review Details contains filenames, automatic counts, net additions/removals, and final measurements.
- **`RBC_Final_Results.csv`**: the detailed final count/edit table.

**Final count = automatic count + lines added − lines removed.**

**Flux (RBCs/s) = final count ÷ frame period in seconds.**

The exported flux is already corrected for frame period; do not divide it again. Working CSVs and corrected TIFFs are saved throughout review. Later saved edits refresh final exports; an incomplete saved review removes stale final exports.

## Troubleshooting

- **Setup fails:** read the message in the setup window. Check Python/Tk installation and internet access.
- **App will not open:** run First Time Setup on this computer. To see the error, open a terminal in this folder and run `.venv/bin/python app/rbc_app.py` on Mac, or `.venv\Scripts\python.exe app\rbc_app.py` on Windows.
- **Analysis fails:** check `fiji.log` in the run folder. Parallel runs also have `fiji_worker_N.log`; the error identifies the relevant log. A failed worker stops the other workers.
- **Computer slows down:** lower Simultaneous images. More workers do not always finish sooner.

The `app/` folder and `requirements.txt` support the launchers and should stay in place.

Magnified editor views show sharp source pixels without smoothing, similar to Fiji. Zoomed-out views use Lanczos resampling. This changes display only; source resolution, detections, and exported annotations remain unchanged. Reopen the app and resume an existing session to use the updated display.
