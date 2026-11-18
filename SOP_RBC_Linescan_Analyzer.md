# SOP: RBC Linescan Analyzer

**Purpose:** Batch-analyze linescans, check the detected RBC lines, and export corrected counts and flux.

## 1. Set up the computer — once

1. Extract **RBC Analyzer - Application.zip**. Keep the extracted folder and all its contents together.
2. Install **Python 3.10 or newer with Tk support** from [python.org](https://www.python.org/downloads/) and **Fiji** from [fiji.sc](https://fiji.sc/).
3. In the extracted application folder, run the setup file for your computer:

   | Mac | Windows |
   | --- | --- |
   | `First Time Setup.command` | `First Time Setup.bat` |

4. Keep the computer connected to the internet during setup. Wait for **Python setup complete**. If setup reports an error, resolve it before continuing.

Run setup again when moving the application to a different computer. Do not copy another computer’s `.venv` as a substitute for setup.

## 2. Prepare the images

- Keep each scan’s original **Ch3 OME TIFF** and matching **XML** together in their numbered experiment subfolders.
- Each input must be a **single 2D grayscale linescan**, with position across columns and time down rows. Split multi-plane images before analysis.
- Select the original experiment folder containing these subfolders; the application collects and organizes the files automatically.

## 3. Run the batch

1. Open **Launch RBC Analyzer.command** (Mac) or **Launch RBC Analyzer.bat** (Windows).
2. Next to **Original scan folder**, click **Browse…** and select your experiment folder.
3. Check the **Fiji executable**. Use Browse if necessary:
   - Mac: typically `/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx`.
   - Windows: select `ImageJ-win64.exe` inside the Fiji folder.
4. Set **Fallback duration** to the known scan duration in **seconds**. It is used only when XML frame timing is unavailable; do not leave a guessed value for scans lacking timing metadata.
5. Start with **Simultaneous images = 2**. Use **1** if the computer struggles or you prefer sequential processing.
6. Click **Run entire folder**. The themed indicator shows activity during collection and actual progress during analysis. Wait for analysis to finish; the linescan editor opens automatically. Do not close the application during analysis.

The application creates a new **`<experiment> - RBC Analysis - <date and time>`** folder beside the selected experiment folder. Original inputs are preserved.

## 4. Review every image

Check whether the red lines follow the RBC streaks and whether any detections are missing or duplicated. Pay extra attention to images showing a QC flag.

| Task | Action |
| --- | --- |
| Add a missing detection | Select **Add / remove RBC lines**, then left-click the streak. |
| Remove an extra detection | Right-click near the line; Control-click also works on Mac. |
| Move around the image | Select **Pan image** and drag, or hold Space while dragging. |
| Zoom / scroll | Use the zoom buttons or `+` / `−`; use the mouse wheel to scroll. |
| Improve visibility | Adjust **Brightness / Contrast**. This changes the display only. |
| Undo an edit | Click **Undo**. |
| Start counting from zero | Click **Clear, edit manually**, then add a line for each RBC streak. |
| Restore automatic detections | Click **Revert to original**. |

New lines use the detected angle. After checking an image, click **Save / Next**. This saves the corrected annotation and measurements and advances to the next image. Use **Previous** to revisit an image. Save periodically during long edits.

**Appearance** is optional: Standard, Arasaka, Ocean, Seattle, Seattle Rain, and Tokyo affect the interface only, not the analysis or exports.

## 5. Finish and collect the results

1. Review all images, then click **Finish / export**. If any image remains unreviewed, the application opens it first.
2. In the run folder, find:
   - **`RBC_Final_Results.xlsx`** — final results workbook.
   - **`RBC_Final_Results.csv`** — detailed final count/edit table.
   - **`RBC_Annotated/`** — saved annotated TIFF images.
3. Check the final counts and frame times before using the results.

**Flux (RBCs/s) = final RBC count ÷ frame period (seconds).** The exported flux already includes this calculation; do not divide it by frame period again.

## 6. Pause or resume

Click **Save** before stopping. To return later, launch the application, click **Resume saved review…**, and select **`session.json`** inside the run folder. Keep the **entire run folder** together; the session needs its supporting files.

## Quick troubleshooting

- **Application does not launch:** run First Time Setup on that computer and check its error message.
- **No images found:** verify the selected experiment folder and Ch3 OME TIFF files.
- **Analysis fails:** read the run folder’s **`fiji.log`** and, for parallel runs, the indicated **`fiji_worker_N.log`**.
- **Computer slows down:** reduce **Simultaneous images**.
- **Final workbook is missing:** complete and save the review of every image, then click Finish / export.

The on-screen log appears as text over the background. Scroll to read earlier messages; right-click (Control-click on Mac) and select **Copy log** to copy all messages.
