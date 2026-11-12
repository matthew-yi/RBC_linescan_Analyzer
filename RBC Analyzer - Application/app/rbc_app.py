#!/usr/bin/env python3
"""Launch with python3 rbc_app.py."""
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from contextlib import ExitStack
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from rbc_workflow import prepare, build_macro, import_detections, save_session


def create_run_folder(source):
    experiment = source.parent.name if source.name == 'collected_ome_tif' else source.name
    label = f'{experiment or "Experiment"} - RBC Analysis - {datetime.now():%Y-%m-%d %H-%M}'
    number = 1
    while True:
        suffix = f' ({number})' if number > 1 else ''
        output = source.parent / (label + suffix)
        try:
            output.mkdir()
            return output
        except FileExistsError:
            number += 1


def completed_image_count(output, total):
    # External Mac volumes can contain ._0.txt resource-fork sidecars. Count
    # only the exact output names generated for this batch, never all *.txt.
    expected = {f'{index}.txt' for index in range(total)}
    return sum(path.name in expected and path.is_file()
               for path in (output / 'detections').glob('*.txt'))


class App:
    def __init__(self, root):
        self.root = root
        root.title('RBC Linescan Analyzer')
        root.geometry('820x430')
        root.minsize(640, 360)
        self.events = queue.Queue()
        self.records = []
        self.index = 0
        self.busy = False
        self.process = None
        self.processes = []
        self.undo = []
        self.scale = 1.0
        self.source = tk.StringVar()
        self.fiji = tk.StringVar(value='/Applications/Fiji.app/Contents/MacOS/ImageJ-macosx')
        self.duration = tk.StringVar(value='1.0')
        self.workers = tk.IntVar(value=min(2, os.cpu_count() or 1))
        form = ttk.Frame(root, padding=10)
        form.pack(fill='x')
        for row, (label, variable, command) in enumerate((('Original scan folder', self.source, self.choose_source), ('Fiji executable', self.fiji, self.choose_fiji))):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky='w')
            ttk.Entry(form, textvariable=variable, width=85).grid(row=row, column=1, sticky='ew')
            ttk.Button(form, text='Browse…', command=command).grid(row=row, column=2)
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text='Fallback duration (seconds)').grid(row=2, column=0, sticky='w')
        ttk.Entry(form, textvariable=self.duration, width=12).grid(row=2, column=1, sticky='w')
        ttk.Label(form, text='Simultaneous images').grid(row=3, column=0, sticky='w')
        self.worker_control = ttk.Spinbox(form, from_=1, to=8, textvariable=self.workers, width=10)
        self.worker_control.grid(row=3, column=1, sticky='w')
        actions = ttk.Frame(root, padding=(10,0))
        actions.pack(fill='x')
        self.run_button = ttk.Button(actions, text='Run entire folder', command=self.run)
        self.run_button.pack(side='left')
        self.resume_button = ttk.Button(actions, text='Resume saved review…', command=self.resume)
        self.resume_button.pack(side='left', padx=10)
        self.status = tk.StringVar(value='Choose the original folder containing the numbered scans. Collection runs automatically.')
        ttk.Label(root, textvariable=self.status, padding=10, wraplength=1050).pack(fill='x')
        self.progress_text = tk.StringVar(value='Ready')
        ttk.Label(root, textvariable=self.progress_text, padding=(10, 0)).pack(anchor='w')
        self.progress = ttk.Progressbar(root, mode='determinate', maximum=1)
        self.progress.pack(fill='x', padx=10, pady=8)
        self.open_editor_button = ttk.Button(actions, text='Open editor', command=self.open_editor, state='disabled')
        self.open_editor_button.pack(side='left')
        self.build_editor()
        self.log = tk.Text(root, height=5, state='disabled')
        self.log.pack(fill='both', expand=True, padx=10, pady=8)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(150, self.poll)

    def build_editor(self):
        self.editor = tk.Toplevel(self.root)
        self.editor.title('Linescan editor')
        self.editor.geometry('580x900')
        self.editor.minsize(460, 480)
        self.editor.withdraw()
        self.editor.protocol('WM_DELETE_WINDOW', self.close_editor)
        self.editor_status = tk.StringVar(value='')
        self.measurements = tk.StringVar(value='')
        self.tool = tk.StringVar(value='add')
        self._space_pan = False
        self.shortcut_tag = f'RBCEditorKeys{id(self)}'
        self.show_lines = tk.BooleanVar(value=True)
        self._image_key = None
        self.brightness = tk.DoubleVar(value=0)
        self.contrast = tk.DoubleVar(value=1)
        self._contrast_after = None
        self.origin_x = 0
        self.review_buttons = []
        sidebar = ttk.Frame(self.editor, padding=12, width=200)
        sidebar.pack(side='right', fill='y')
        ttk.Label(sidebar, text='LINESCAN TOOLS', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w', pady=(0, 12))
        ttk.Label(sidebar, textvariable=self.measurements, justify='left').pack(anchor='w', pady=(0, 12))
        for label, mode in [('Add / remove RBC lines', 'add'), ('Pan image', 'pan')]:
            button = ttk.Radiobutton(sidebar, text=label, variable=self.tool, value=mode, command=self.render)
            button.pack(anchor='w', pady=3)
            self.review_buttons.append(button)
        bc = ttk.LabelFrame(sidebar, text='Brightness / Contrast', padding=6)
        bc.pack(fill='x', pady=8)
        for label, variable, low, high in [('Brightness', self.brightness, -127, 127),
                                          ('Contrast', self.contrast, .25, 4)]:
            ttk.Label(bc, text=label).pack(anchor='w')
            slider = ttk.Scale(bc, from_=low, to=high, variable=variable, command=self.adjust_contrast)
            slider.pack(fill='x')
            self.review_buttons.append(slider)
        button = ttk.Button(bc, text='Reset B&C', command=self.reset_contrast)
        button.pack(fill='x', pady=(4, 0))
        self.review_buttons.append(button)
        ttk.Separator(sidebar).pack(fill='x', pady=10)
        for label, command in [('Clear, edit manually', self.clear_manual), ('Revert to original', self.reset)]:
            button = ttk.Button(sidebar, text=label, command=command, state='disabled')
            button.pack(fill='x', pady=3)
            self.review_buttons.append(button)
        buttons = ttk.Frame(sidebar)
        buttons.pack(fill='x')
        for column in range(2):
            buttons.columnconfigure(column, weight=1)
        for n, (label, command) in enumerate([
            ('Zoom +', lambda:self.zoom(1.5)), ('Zoom −', lambda:self.zoom(1/1.5)),
            ('Fit width', self.fit), ('Fit entire image', self.fit_image),
            ('100%', lambda:self.set_zoom(1)), ('Undo', self.undo_edit),
            ('Save', self.save), ('Finish / export', self.finish_review),
            ('Previous', lambda:self.move(-1)), ('Save / Next', lambda:self.move(1))]):
            button = ttk.Button(buttons, text=label, command=command, state='disabled')
            button.grid(row=n//2, column=n%2, sticky='ew', pady=3, padx=1)
            self.review_buttons.append(button)
        check = ttk.Checkbutton(sidebar, text='Show RBC lines', variable=self.show_lines, command=self.render)
        check.pack(anchor='w', pady=10)
        self.review_buttons.append(check)
        ttk.Label(sidebar, text='Left click: add • Right click: remove\nHold Space: pan\n+ / −: zoom • Wheel: scroll\nCtrl + wheel: zoom', justify='left').pack(anchor='w', pady=8)
        viewport = ttk.Frame(self.editor)
        viewport.pack(side='left', fill='both', expand=True)
        ttk.Label(viewport, textvariable=self.editor_status, padding=8, wraplength=300).pack(fill='x')
        frame = ttk.Frame(viewport)
        frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(frame, background='#202020', highlightthickness=0)
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=self.canvas.xview)
        vertical = ttk.Scrollbar(frame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        horizontal.grid(row=1, column=0, sticky='ew')
        vertical.grid(row=0, column=1, sticky='ns')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<Button-3>', self.remove)
        self.canvas.bind('<Button-2>', self.remove)
        self.canvas.bind('<Control-Button-1>', self.remove)
        self.canvas.bind('<Configure>', self.resize_editor)
        modifiers = ('Control', 'Command') if sys.platform == 'darwin' else ('Control',)
        for modifier in modifiers:
            self.editor.bind(f'<{modifier}-z>', lambda event:self.undo_edit())
            self.editor.bind(f'<{modifier}-s>', lambda event:self.save())
        # Run shortcuts before button/slider class bindings so Space cannot
        # accidentally activate a focused button while the user is panning.
        self.editor.bind_class(self.shortcut_tag, '<KeyPress-space>', self.start_space_pan)
        self.editor.bind_class(self.shortcut_tag, '<KeyRelease-space>', self.stop_space_pan)
        for key in ('plus', 'equal', 'KP_Add'):
            self.editor.bind_class(self.shortcut_tag, f'<KeyPress-{key}>', lambda event:self.key_zoom(1.5))
        for key in ('minus', 'KP_Subtract'):
            self.editor.bind_class(self.shortcut_tag, f'<KeyPress-{key}>', lambda event:self.key_zoom(1/1.5))
        self.editor.bind('<FocusOut>', self.editor_focus_out)
        self.bind_editor_scroll(self.editor)

    def bind_editor_scroll(self, widget):
        widget.bindtags((self.shortcut_tag,) + widget.bindtags())
        # Widget bindings run before class/toplevel bindings. Returning "break"
        # in wheel() scrolls exactly once, including over buttons and scrollbars.
        for sequence in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            widget.bind(sequence, self.wheel)
        for child in widget.winfo_children():
            self.bind_editor_scroll(child)

    def open_editor(self):
        if not self.records or self.busy:
            return
        self.editor.deiconify()
        self.editor.lift()
        self.editor.update_idletasks()

    def close_editor(self):
        if self.save():
            self.stop_space_pan()
            self.editor.withdraw()

    def resize_editor(self, event):
        if self.records and hasattr(self, 'image'):
            self.render()

    def drag(self, event):
        if self.active_tool() == 'pan' and not self.busy:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def active_tool(self):
        return 'pan' if self._space_pan else self.tool.get()

    def start_space_pan(self, event=None):
        if self.records and not self.busy:
            self._space_pan = True
            self.canvas.configure(cursor='fleur')
        return 'break'

    def stop_space_pan(self, event=None):
        self._space_pan = False
        self.canvas.configure(cursor='fleur' if self.active_tool() == 'pan' else 'crosshair')
        return 'break'

    def editor_focus_out(self, event):
        def release_if_outside():
            focus = self.editor.focus_get()
            if focus is None or focus.winfo_toplevel() != self.editor:
                self.stop_space_pan()
        self.root.after_idle(release_if_outside)

    def key_zoom(self, factor):
        if self.records and not self.busy:
            self.zoom(factor)
        return 'break'

    def wheel(self, event):
        if not self.records or self.busy:
            return 'break'
        delta = getattr(event, 'delta', 0)
        direction = -1 if getattr(event, 'num', None) == 4 or delta > 0 else 1
        if event.state & 0x4:
            self.zoom(1.2 if direction < 0 else 1/1.2)
        else:
            steps = max(1, int(abs(delta)/120)) if abs(delta) >= 120 else max(1, int(abs(delta)))
            self.canvas.yview_scroll(direction * steps, 'units')
        return 'break'

    def choose_source(self):
        value = filedialog.askdirectory(title='Choose raw linescan experiment folder or collected_ome_tif')
        if value:
            self.source.set(value)

    def choose_fiji(self):
        value = filedialog.askopenfilename(title='Choose Fiji executable (inside Fiji.app/Contents/MacOS on macOS)')
        if value:
            self.fiji.set(value)

    def write_log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text+'\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def set_busy(self, busy):
        self.busy = busy
        self.worker_control.configure(state='disabled' if busy else 'normal')
        for button in (self.run_button, self.resume_button):
            button.configure(state='disabled' if busy else 'normal')
        self.open_editor_button.configure(state='normal' if self.records and not busy else 'disabled')
        for button in self.review_buttons:
            button.configure(state='normal' if self.records and not busy else 'disabled')

    def run(self):
        if self.records and not self.save():
            return
        try:
            from PIL import Image, ImageTk
            source = Path(self.source.get()).expanduser().resolve()
            executable = Path(self.fiji.get()).expanduser()
            duration = float(self.duration.get())
            workers = self.workers.get()
            if not 1 <= workers <= 8:
                raise ValueError('Simultaneous images must be between 1 and 8.')
            if not source.is_dir() or not self.source.get():
                raise ValueError('Choose an existing source folder.')
            if not executable.is_file():
                raise ValueError('Choose the Fiji executable first.')
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError('Fallback duration must be a positive number.')
            output = create_run_folder(source)
        except (ValueError, ImportError, OSError, tk.TclError) as exc:
            messagebox.showerror('Cannot start', str(exc)+'\nInstall dependencies with: python3 -m pip install -r requirements.txt')
            return
        # Every run is isolated, preserving previous analyses and source files.
        self.set_busy(True)
        self.status.set('Collecting images and metadata…')
        self.progress.configure(mode='indeterminate')
        self.progress.start(15)
        self.progress_text.set('Collecting input files…')
        threading.Thread(target=self.worker, args=(source, output, executable, duration, workers), daemon=True).start()

    def worker(self, source, output, executable, duration, workers=1):
        processes = []
        try:
            records = prepare(source, output, lambda line:self.events.put(('log', line)))
            if not records:
                raise ValueError('No images to analyze.')
            workers = min(max(1, workers), len(records))
            self.events.put(('log', f'Analyzing {len(records)} images with {workers} Fiji worker(s). Output: {output}'))
            self.events.put(('status', f'Analyzing up to {workers} images simultaneously. The editor opens when the batch finishes.'))
            self.events.put(('progress', (0, len(records))))
            with ExitStack() as stack:
                summary = stack.enter_context((output / 'fiji.log').open('w'))
                jobs = []
                for worker in range(workers):
                    indices = list(range(worker, len(records), workers))
                    macro = output / ('run_analysis.ijm' if workers == 1 else f'run_analysis_worker_{worker+1}.ijm')
                    marker = 'complete.txt' if workers == 1 else f'worker_{worker+1}_complete.txt'
                    if workers == 1:
                        macro.write_text(build_macro(records, output, duration))
                        log = summary
                    else:
                        macro.write_text(build_macro(records, output, duration, indices=indices, completion_name=marker))
                        log = stack.enter_context((output / f'fiji_worker_{worker+1}.log').open('w'))
                        summary.write(f'Worker {worker+1}: {len(indices)} images; log: {log.name}\n')
                        summary.flush()
                    process = subprocess.Popen([str(executable), '--headless', '--console', '-macro', str(macro)], stdout=log, stderr=subprocess.STDOUT)
                    processes.append(process)
                    jobs.append((process, output / marker, log.name))
                self.processes = processes
                self.process = processes[0]
                completed = -1
                while jobs:
                    count = completed_image_count(output, len(records))
                    if count != completed:
                        completed = count
                        self.events.put(('progress', (count, len(records))))
                    for job in jobs[:]:
                        process, marker, log_name = job
                        try:
                            code = process.wait(timeout=0.1)
                        except subprocess.TimeoutExpired:
                            continue
                        if code or not marker.exists():
                            raise RuntimeError(f'Fiji worker did not complete (exit {code}). See {log_name}.')
                        jobs.remove(job)
                if completed_image_count(output, len(records)) != len(records):
                    raise RuntimeError('Fiji finished without all expected image results. See the worker logs.')
                (output / 'complete.txt').write_text('complete')
            self.events.put(('progress', (len(records), len(records))))
            self.events.put(('status', 'Saving measurements and review session…'))
            import_detections(records, output)
            self.events.put(('done', (records, output)))
        except Exception as exc:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            self.events.put(('error', str(exc)))
        finally:
            self.process = None
            self.processes = []

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'log': self.write_log(value)
                elif kind == 'status': self.status.set(value)
                elif kind == 'progress':
                    done, total = value
                    self.progress.stop()
                    self.progress.configure(mode='determinate', maximum=max(total, 1), value=done)
                    self.progress_text.set(f'{done} / {total} images complete ({done/total:.0%})' if total else 'No images')
                elif kind == 'error':
                    self.progress.stop()
                    self.progress_text.set('Analysis stopped')
                    self.set_busy(False)
                    self.status.set('Analysis stopped. See error and Fiji log.')
                    messagebox.showerror('Analysis failed', value)
                elif kind == 'done':
                    self.records, self.output = value
                    self.index = 0
                    self.set_busy(False)
                    self.progress.stop()
                    self.progress.configure(mode='determinate', maximum=len(self.records), value=len(self.records))
                    self.progress_text.set(f'{len(self.records)} / {len(self.records)} images complete (100%)')
                    self.status.set(f'Analysis complete. Results: {self.output}')
                    self.load()
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    def resume(self):
        path = filedialog.askopenfilename(title='Choose session.json in an RBC Analysis folder', filetypes=[('Review session', '*.json')])
        if not path: return
        try:
            from PIL import Image, ImageTk
            records = json.loads(Path(path).read_text())
            output = Path(path).parent
            if not records or not all((output / 'previews' / f'{n}.png').exists() for n in range(len(records))):
                raise ValueError('Session has no images or is missing its previews.')
            for rec in records:
                for key in ('image', 'peaks', 'automatic_peaks', 'meta', 'angle', 'reviewed'):
                    rec[key]
            if self.records and not self.save(): return
            self.records, self.output = records, output
            self.index = next((i for i,r in enumerate(records) if not r['reviewed']), 0)
            self.set_busy(False)
            self.load()
        except Exception as exc:
            messagebox.showerror('Could not open session', str(exc))

    def load(self):
        from PIL import Image
        with Image.open(self.output / 'previews' / f'{self.index}.png') as image:
            self.image = image.convert('RGB')
        self.undo = []
        self.reset_contrast()
        self._image_key = None
        self.open_editor()
        self.editor.title(f'Linescan {self.index+1}/{len(self.records)} — {self.records[self.index]["image"]}')
        self.fit()

    def fit(self):
        if not self.records: return
        self.scale = min(8, max(.02, (self.canvas.winfo_width()-24)/self.image.width))
        self.render()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def fit_image(self):
        if not self.records: return
        self.scale = max(.005, min((self.canvas.winfo_width()-24)/self.image.width,
                                  (self.canvas.winfo_height()-24)/self.image.height, 8))
        self.render()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def zoom(self, factor):
        if self.records:
            self.set_zoom(self.scale * factor)

    def set_zoom(self, scale):
        if not self.records: return
        old_scale = self.scale
        center_y = self.canvas.canvasy(self.canvas.winfo_height()/2)/old_scale
        self.scale = min(8, max(.005, scale))
        self.render()
        height = max(self.canvas.winfo_height(), round(self.image.height*self.scale))
        self.canvas.yview_moveto(max(0, (center_y*self.scale-self.canvas.winfo_height()/2)/height))

    def render(self):
        if not self.records or not hasattr(self, 'image'): return
        from PIL import Image, ImageTk
        w,h = max(1, round(self.image.width*self.scale)), max(1, round(self.image.height*self.scale))
        # Keep the bitmap when editing lines; only rebuild it after zoom or load.
        key = (self.index, w, h, self.brightness.get(), self.contrast.get())
        if key != self._image_key:
            lut = [max(0, min(255, round((v-127.5+self.brightness.get())*self.contrast.get()+127.5))) for v in range(256)]
            display = self.image.convert('L').point(lut)
            # Enlarging should reveal source pixels rather than blur their boundaries.
            resampling = Image.Resampling.NEAREST if self.scale >= 1 else Image.Resampling.LANCZOS
            self.photo = ImageTk.PhotoImage(display.resize((w,h), resampling))
            self.canvas.delete('bitmap')
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw', tags='bitmap')
            self._image_key = key
        self.origin_x = max(12, (self.canvas.winfo_width()-w)/2)
        self.canvas.coords('bitmap', self.origin_x, 0)
        self.canvas.delete('lines')
        rec = self.records[self.index]
        slope = math.tan(math.radians(rec['angle']))
        if self.show_lines.get():
            for y in rec['peaks']:
                self.canvas.create_line(self.origin_x, y*self.scale,
                    self.origin_x+(self.image.width-1)*self.scale,
                    (y-(self.image.width-1)*slope)*self.scale,
                    fill='#ff3030', width=1, tags='lines')
        self.canvas.configure(scrollregion=(0,0,max(w+24,self.canvas.winfo_width()),max(h,self.canvas.winfo_height())))
        reviewed = sum(r['reviewed'] for r in self.records)
        self.editor_status.set(f'{self.index+1}/{len(self.records)} • {self.scale:.0%} • {reviewed} reviewed')
        duration = rec['meta'][0]
        flux = f'{len(rec["peaks"])/duration:.2f}' if duration > 0 else 'N/A'
        self.measurements.set(f'RBC count: {len(rec["peaks"])}\nFrame period: {duration:g} s\nFlux: {flux} RBCs/s\n{rec.get("qc", "OK")}')
        self.canvas.configure(cursor='fleur' if self.active_tool() == 'pan' else 'crosshair')

    def click(self, event):
        self.canvas.focus_set()
        if self.active_tool() == 'pan':
            self.canvas.scan_mark(event.x, event.y)
            return
        return self.edit(event, False)

    def remove(self, event):
        if self.active_tool() != 'pan':
            self.edit(event, True)
        return 'break'

    def edit(self, event, remove):
        if not self.records or self.busy: return
        x,y = (self.canvas.canvasx(event.x)-self.origin_x)/self.scale, self.canvas.canvasy(event.y)/self.scale
        if not (0<=x<self.image.width and 0<=y<self.image.height): return
        rec = self.records[self.index]
        slope = math.tan(math.radians(rec['angle']))
        intercept = y+x*slope
        peaks = rec['peaks']
        before = peaks.copy()
        if remove:
            if peaks:
                nearest = min(peaks, key=lambda p:abs(p-intercept))
                # Screen-space perpendicular distance: avoid removing a distant line.
                if abs(nearest-intercept)*self.scale/math.sqrt(1+slope*slope)<=12:
                    peaks.remove(nearest)
        elif not any(abs(p-intercept)<.5 for p in peaks):
            peaks.append(intercept)
            peaks.sort()
        if peaks == before:
            return
        self.undo.append(before)
        rec['reviewed'] = False
        self.render()

    def undo_edit(self):
        if self.undo:
            self.records[self.index]['peaks'] = self.undo.pop()
            self.records[self.index]['reviewed'] = False
            self.render()

    def reset(self):
        if self.records:
            rec = self.records[self.index]
            self.undo.append(rec['peaks'].copy())
            rec['peaks'] = rec['automatic_peaks'].copy()
            rec['reviewed'] = False
            self.tool.set('add')
            self.show_lines.set(True)
            self.reset_contrast()
            self.render()

    def clear_manual(self):
        if not self.records or self.busy: return
        rec = self.records[self.index]
        self.undo.append(rec['peaks'].copy())
        rec['peaks'] = []
        rec['reviewed'] = False
        self.tool.set('add')
        self.show_lines.set(True)
        self.render()

    def adjust_contrast(self, value=None):
        if self._contrast_after is not None:
            self.root.after_cancel(self._contrast_after)
        self._contrast_after = self.root.after(40, self.draw_contrast)

    def draw_contrast(self):
        self._contrast_after = None
        self.render()

    def reset_contrast(self):
        if self._contrast_after is not None:
            self.root.after_cancel(self._contrast_after)
            self._contrast_after = None
        self.brightness.set(0)
        self.contrast.set(1)
        self.render()

    def save(self):
        if not self.records: return True
        try:
            from PIL import ImageDraw
            rec = self.records[self.index]
            annotated = self.image.copy()
            draw = ImageDraw.Draw(annotated)
            slope = math.tan(math.radians(rec['angle']))
            for y in rec['peaks']:
                draw.line((0,y,self.image.width-1,y-(self.image.width-1)*slope), fill=(255,0,0), width=1)
            path = self.output / 'RBC_Annotated' / (rec['image']+'_annotated.tif')
            temp = path.with_suffix('.tmp')
            original = self.output / 'original_annotations' / path.name
            if original.exists() and sorted(rec['peaks']) == sorted(rec['automatic_peaks']):
                shutil.copyfile(original, temp)
            else:
                annotated.save(temp, format='TIFF')
            temp.replace(path)
            rec['reviewed'] = True
            save_session(self.records, self.output)
            self.render()
            return True
        except Exception as exc:
            messagebox.showerror('Save failed', str(exc))
            return False

    def move(self, delta):
        if not self.records or not self.save(): return
        target = self.index+delta
        if target >= len(self.records):
            self.finish_review(save_current=False)
        elif target >= 0:
            self.index = target
            self.load()

    def finish_review(self, save_current=True):
        if not self.records or self.busy: return
        if save_current and not self.save(): return
        missing = next((i for i,r in enumerate(self.records) if not r['reviewed']), None)
        if missing is not None:
            messagebox.showinfo('Review remaining images', 'Review every image before exporting final results. Opening the first unreviewed image.', parent=self.editor)
            self.index = missing
            self.load()
            return
        messagebox.showinfo('Review complete', f'Final corrected results saved:\n{self.output / "RBC_Final_Results.xlsx"}\n{self.output / "RBC_Final_Results.csv"}', parent=self.editor)

    def close(self):
        if self.busy:
            messagebox.showinfo('Analysis running', 'Let analysis finish before closing this window. Fiji progress is recorded in the run folder’s fiji.log.')
            return
        if self.records and not self.save(): return
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
