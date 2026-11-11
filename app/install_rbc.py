#!/usr/bin/env python3
"""First-time setup. Run with an installed Python 3.10+ interpreter."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError('Install Python 3.10 or newer from https://www.python.org/downloads/ and run setup again.')
    # Check before replacing any existing environment. Tk is supplied by Python,
    # rather than pip, and is needed for the desktop interface.
    try:
        import tkinter
        tkinter.Tcl()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError('This Python installation needs Tkinter/Tk. Install Python with Tcl/Tk support, then run setup again.') from exc

    project = Path(__file__).resolve().parent.parent
    environment = project / '.venv'
    backup = project / ('.venv.previous-' + uuid.uuid4().hex[:8])
    if environment.exists() or environment.is_symlink():
        environment.rename(backup)
        print(f'Previous environment saved as {backup.name}', flush=True)
    try:
        print('Creating a Python environment for this computer...', flush=True)
        venv.EnvBuilder(with_pip=True, symlinks=False).create(environment)
        python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        print('Installing image dependencies (internet access required)...', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(project / 'requirements.txt')], check=True)
        subprocess.run([str(python), '-c', 'import tkinter; from PIL import Image, ImageTk; import rbc_app'], cwd=project / 'app', check=True)
    except Exception:
        # Restore the original environment if installation fails.
        if environment.is_dir() and not environment.is_symlink():
            shutil.rmtree(environment)
        if backup.exists() or backup.is_symlink():
            backup.rename(environment)
        raise

    fiji_candidates = [
        Path('/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx'),
        Path.home() / 'Applications/Fiji.app/Contents/MacOS/ImageJ-macosx',
        project / 'Fiji.app/ImageJ-win64.exe',
        Path.home() / 'Fiji.app/ImageJ-win64.exe',
        Path('C:/Fiji.app/ImageJ-win64.exe'),
    ]
    fiji = next((p for p in fiji_candidates if p.is_file()), None)
    fiji = fiji or shutil.which('ImageJ-linux64') or shutil.which('ImageJ-win64.exe')
    print('\nPython setup complete.', flush=True)
    if fiji:
        print(f'Fiji found: {fiji}')
    else:
        print('Fiji is also required for analysis. Download it from https://fiji.sc/ and install it.')
    print('In the app, use Browse beside Fiji executable to select Fiji if needed.')
    print('Open Launch RBC Analyzer.command (Mac) or Launch RBC Analyzer.bat (Windows).')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'\nSetup failed: {exc}', file=sys.stderr)
        sys.exit(1)
