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

The separate linescan editor opens after analysis. Use the side tools to add/remove RBC lines, pan, zoom, undo, save, and navigate. The mouse wheel scrolls from anywhere in the editor; Ctrl + wheel zooms. Counts, frame periods, and flux appear beside the image.

**Save / Next**, Previous, and closing the editor save your review. Closing the editor leaves the analyzer open; use **Open editor** to return. To continue a previous run, choose **Resume saved review** and select its `session.json`.

## Terminal alternatives

Mac/Linux setup: `python3 app/install_rbc.py`

Windows setup: `py -3 app\install_rbc.py`

Mac/Linux launch after setup: `.venv/bin/python app/rbc_app.py`

Windows launch after setup: `.venv\Scripts\python.exe app\rbc_app.py`

Only Pillow is installed through pip. Tkinter comes with the Python installation, and Fiji is installed separately.
