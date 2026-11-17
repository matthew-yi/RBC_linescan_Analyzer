# RBC Linescan Analyzer

For setup and everyday use, see [SOP: RBC Linescan Analyzer](SOP_RBC_Linescan_Analyzer.md).

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

## Appearance

Choose **Appearance → Arasaka** in the analyzer window for a charcoal and red interface inspired by the reference PC. It applies to both the analyzer and linescan editor. Choose **Standard** to restore the original appearance. The theme affects interface colors only; linescan pixels, annotation colors, measurements, and exports are unchanged. Appearance defaults to Standard when the app launches.

Arasaka mode also includes small decorative code terminals in the analyzer header and editor sidebar: typed code, a pulsing link indicator, and a moving red trace. These are visual effects only. They never execute commands or read scan data. Switching to Standard removes them and stops their timers; hidden editor windows skip animation drawing.

Choose **Appearance → Ocean** for deep blue panels, turquoise accents, and small animated aquariums in the analyzer header and editor sidebar. Layered waves, rising bubbles, and animated pixel-art fish sprites animate only in Ocean mode. Switching themes stops and hides the aquarium. These decorations do not change scan images, measurements, or exports.

Ocean artwork now uses a reference-inspired four-species swimming sprite sheet and a pixel-art wave-painting vignette. Both are bundled in `app/assets/`; keep that folder with the app. Fish cycle through swimming frames, while the painting drifts gently beneath small water ripples and bubbles.

The Ocean editor now has a full-window animated background behind the controls and scan viewer: surface waves, water that darkens with depth, and a seabed with swaying seaweed. An open water area between the panels shows creatures passing at different levels. The scene retains the first four fish, adds eight fish varieties, and includes dolphins, orcas, humpbacks, and belugas in simplified flat-color pixel art. Ocean mode expands the editor to keep the controls and scan area usable; switching themes hides the scene and stops its animation.

Ocean mode’s top border now draws continuous rolling water with layered swells, shaded faces, crest foam, and light spray. It does not tile or distort the wave painting. Fish use stationary sprites in the editor; the analyzer header contains only water. Animation stops when switching away from Ocean.

The wave implementation is inspired by the painting’s indigo water and pale foam, rather than repeating the artwork. Fish remain at fixed positions and use a single frame; only water, bubbles and seaweed move.

Wave details include hollow curling lips, forked cream foam trails, fine water contours, and drifting spray inspired by woodblock wave shapes. The rendering remains continuous and uses no repeated painting tiles.

Current wave display: a single Great Wave pixel-art animation replaces the procedural wave curves. Eight aligned painting frames play forward and backward for a gentle loop. The painting retains its proportions, with proportional cropping to fill the banner. It is never tiled or warped into strips. Fish remain still.

The wave banner now fills its width using proportional scaling and cropping. It never stretches a single edge column into the margins. The taller analyzer banner shows more of the painting.

The large curling wave has been removed from the active Ocean animation. Smaller rolling waves, the warm sky, and Mount Fuji remain. Short banners crop toward the bottom to keep the waves visible.

Current Ocean behavior: water fills the entire background of both application windows, underneath the controls and scan viewer. The surface animation crops to water only, removing the remaining sky and mountain. Fish and marine mammals keep a single sprite pose but drift toward random destinations with smooth steering and direction changes, staying within decorative depth bands. Motion remains behind UI panels and never changes the scan image. Switching themes stops the animation.

Ocean now shows through the layout panels and text-label backgrounds in both windows. Panels reproduce the same animated scene at their screen position so water and fish remain aligned across boundaries. Input fields, dropdowns, buttons, boxed brightness controls, the log, and the scan image remain opaque and usable. Standard and Arasaka restore solid backgrounds.

Sprite color correction: nearest-neighbor resizing preserves the original visible palette and alpha; transparent magenta is no longer included in RGB palette reduction, and visible magenta key fringes are removed from marine mammals. The water surface now shows its full source width at proportional scale and fades into the depth gradient, avoiding a magnified strip and hard lower boundary.

Current theme fixes: Ocean uses simple gently rolling wave layers again; painting animation assets are retained but no longer displayed. Fish still drift behind the controls. Standard labels now use the native theme foreground and background, including macOS system colors, so text remains readable in light and dark appearance both on launch and after switching themes.

Ocean mode no longer displays any waves or painting animation. Both windows retain the continuous underwater depth gradient, drifting fish and marine mammals, bubbles, and seabed behind the controls.

Compact Ocean layout: the former wave header spacing, wide center gutter, and extra bottom padding are removed. The scan viewer and controls begin near the top of the editor and use the available window space. Theme selection no longer forces a larger editor size; backgrounds remain behind the UI.

## Seattle appearance

Choose **Appearance → Seattle** for a pixel-art adaptation of the supplied Seattle skyline photo, with the Space Needle, Mount Rainier, downtown buildings and foreground trees. The static artwork appears behind labels and between controls in both windows. The artwork fills each window edge to edge, preserves its proportions, and crops at the edges as needed. It is darkened slightly for readable labels. Navy and evergreen controls remain opaque. Theme changes do not alter scans, detections, measurements or exports.

Seattle backgrounds resize to fill both windows without borders or margins. Wide or tall windows may crop part of the skyline to preserve proportions.

## Tokyo and Seattle Rain

Choose **Appearance → Tokyo** for the supplied Tokyo skyline photo adapted to pixel art, with Tokyo Tower, Mount Fuji, sunset colors, and slowly drifting cherry blossom petals. Choose **Appearance → Seattle Rain** for the Seattle artwork in a cooler tone with slanted rain streaks. Both effects appear behind labels and layout areas in both windows, fill the window when resized, and leave control boxes and scan pixels unchanged. **Seattle** remains available without rain. Effects stop when changing themes; hidden windows skip particle updates.

Seattle Rain now uses its own overcast skyline artwork with layered grey storm clouds, muted wet-weather lighting, and haze around Mount Rainier. The rain is denser, faster, and longer, with differently weighted streaks for a pouring effect. Density adjusts to window area. Regular Seattle keeps its sunny artwork, and Tokyo petals are unchanged.
