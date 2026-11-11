"""Shared collection, Fiji bridge, and review persistence for the desktop app."""
from __future__ import annotations
import csv
from collections import Counter
import hashlib
import json
import math
import re
import shutil
import zipfile
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
from pathlib import Path
from collect_linescans_updated import collect_linescans
from extract_linescan_periods_batch_v2 import extract_frame_level_values, sort_rows, write_rows, local_name


def natural_key(value):
    return tuple((0, int(p)) if p.isdigit() else (1, p.lower()) for p in re.split(r'(\d+)', str(value)))


def prepare(source: Path, output: Path, log=print):
    source, output = source.resolve(), output.resolve()
    if source == output or source.is_relative_to(output):
        raise ValueError('Output must not contain the source folder.')
    folders = {name: output / name for name in ('collected_ome_tif', 'collected_xml', 'collected_ch3source', 'RBC_Annotated', 'previews', 'detections', 'analysis_input')}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    files = [p for p in source.rglob('*') if p.is_file() and not p.is_relative_to(output)]
    images = [p for p in files if re.search(r'LineScan-.*_Cycle.*_Ch3_.*\.ome\.tiff?$', p.name, re.I)]
    collected_sources = {}
    if any(p.name.startswith('LineScan-') and p.name.endswith('.ome.tif') for p in images):
        # Use the original collector, then consume its numbered images and XML.
        collected_sources = collect_linescans(source, output_dir=output, log=log)
        images = [p for p in collected_sources if p.parent == folders['collected_ome_tif']]
        files = []  # The collector has already copied XML and Ch3Source files.
    if not images:
        # Also accept a previously collected image folder.
        images = [p for p in source.iterdir() if p.is_file() and p.name.lower().endswith(('.tif', '.tiff')) and 'ch3source' not in p.name.lower()]
    if not images:
        raise ValueError('No Ch3 OME TIFF linescans found in the selected folder.')
    used = set()
    records, timing = [], []
    copied_xml = {}
    for image in sorted(images, key=natural_key):
        name = image.name if image in collected_sources or source == image.parent and re.match(r'\d+_', image.name) else f'{image.parent.name}_{image.name}'
        if name in used:
            name = hashlib.sha256(str(image.relative_to(source)).encode()).hexdigest()[:10] + '_' + name
        used.add(name)
        target = folders['collected_ome_tif'] / name
        if image != target:
            shutil.copyfile(image, target)
        # Native TIFF opening avoids Bio-Formats' interactive OME importer in headless Fiji.
        shutil.copyfile(image, folders['analysis_input'] / f'{len(records)}.tif')
        scan_base = image.name.split('_Cycle')[0]
        candidates = [image.parent / (scan_base + '.xml')]
        if image.parent.name == 'collected_ome_tif':
            candidates.append(image.parent.parent / 'collected_xml' / (scan_base + '.xml'))
        xml = next((p for p in candidates if p.exists()), None)
        meta = [-1.0] * 4
        if xml:
            try:
                tree = ET.parse(xml)
                frames = [f for s in tree.getroot().iter() if local_name(s.tag) == 'Sequence' for f in list(s) if local_name(f.tag) == 'Frame']
                match = re.search(r'_Cycle(\d+)_Ch\d+_(\d+)', image.name)
                if match:
                    cycle, index = map(int, match.groups())
                    frames = [f for s in tree.getroot().iter() if local_name(s.tag) == 'Sequence' and int(s.get('cycle', '0')) == cycle for f in list(s) if local_name(f.tag) == 'Frame' and int(f.get('index', '0')) == index]
                if len(frames) != 1:
                    raise ValueError('Could not identify a unique metadata frame')
                values = {v.get('key'): v for v in frames[0].iter() if local_name(v.tag) == 'PVStateValue'}
                for i, key in ((0, 'framePeriod'), (1, 'scanLinePeriod')):
                    if key in values:
                        meta[i] = float(values[key].get('value', '-1'))
                # Scale may be inherited from the global state shard.
                scale_nodes = [n for shard in list(tree.getroot()) if local_name(shard.tag) == 'PVStateShard' for n in shard.iter()] + list(frames[0].iter())
                for node in scale_nodes:
                    if local_name(node.tag) == 'PVStateValue' and node.get('key') == 'micronsPerPixel':
                        for axis in node:
                            if axis.get('index') == 'XAxis':
                                meta[2] = float(axis.get('value', '-1'))
                length = next((float(n.get('lineLength')) for n in tree.getroot().iter() if n.get('lineLength')), -1)
                if length > 0 and meta[2] > 0:
                    meta[3] = length * meta[2]
            except (ValueError, ET.ParseError) as exc:
                log(f'Metadata warning for {image.name}: {exc}; missing values use fallback / N/A.')
            if xml not in copied_xml:
                xml_name = name.split('_Cycle')[0] + '.xml'
                xml_target = folders['collected_xml'] / xml_name
                if xml != xml_target:
                    shutil.copyfile(xml, xml_target)
                copied_xml[xml] = xml_target
                try:
                    timing.extend(extract_frame_level_values(xml_target))
                except ValueError as exc:
                    log(str(exc))
        record = dict(image=name, source=str(collected_sources.get(image, image)), meta=meta, angle=0, peaks=[], automatic_peaks=[], reviewed=False)
        records.append(record)
    for src in files:
        if src.name.lower().endswith('ch3source.tif'):
            name = f'{src.parent.name}_{src.name}'
            dest = folders['collected_ch3source'] / name
            if dest.exists():
                dest = dest.with_name(hashlib.sha256(str(src).encode()).hexdigest()[:10] + '_' + name)
            shutil.copyfile(src, dest)
    write_rows(output / 'linescan_periods_batch.tsv', sort_rows(timing), minimal=False)
    return records


def ij_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def build_macro(records, output: Path, fallback: float, indices=None, completion_name='complete.txt'):
    original = Path(__file__).with_name('RBC_Linescan_Analyzer2.0.ijm').read_text()
    start = original.index('macro "RBC Linescan Analyzer2.0"')
    end = original.index('// ── SINGLE MODE', start)
    commands = ['setBatchMode(true);']
    for n in range(len(records)) if indices is None else indices:
        rec = records[n]
        image = output / 'analysis_input' / f'{n}.tif'
        stem = str(n)
        commands.extend([
            f'open({ij_string(image)});',
            'if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");',
            'imgID=getImageID();',
            'run("Duplicate...", "title=_preview_"); run("8-bit");',
            f'saveAs("PNG", {ij_string(output / "previews" / (stem + ".png"))}); close();',
            'lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";',
            'count=detectRBCLines(imgID, true);',
            f'saveAs("Tiff", {ij_string(output / "RBC_Annotated" / (rec["image"] + "_annotated.tif"))}); close();',
            'text=""+lastAngleDeg+"\\n"+lastQCString+"\\n";',
            'for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\\n";',
            f'File.saveString(text, {ij_string(output / "detections" / (stem + ".txt"))});',
        ])
        if rec['meta'][0] <= 0:
            rec['meta'][0] = fallback
            rec['duration_source'] = 'manual fallback'
        else:
            rec['duration_source'] = 'frame metadata'
    commands.extend([f'File.saveString("complete", {ij_string(output / completion_name)});', 'setBatchMode(false);'])
    original = original.replace('showMessage("Image is blank."); return 0;', 'lastQCString="BLANK IMAGE"; return 0;')
    return original[:start] + '\n'.join(commands) + '\n' + original[end:]


def import_detections(records, output):
    originals = output / 'original_annotations'
    originals.mkdir(exist_ok=True)
    for n, rec in enumerate(records):
        lines = (output / 'detections' / f'{n}.txt').read_text().splitlines()
        rec.update(angle=float(lines[0]), qc=lines[1], peaks=[float(x) for x in lines[2:]])
        rec['automatic_peaks'] = rec['peaks'].copy()
        annotation = output / 'RBC_Annotated' / (rec['image'] + '_annotated.tif')
        original = originals / annotation.name
        if annotation.exists() and not original.exists():
            shutil.copyfile(annotation, original)
    save_session(records, output)


def result_row(rec):
    peaks = sorted(rec['peaks'])
    duration, period, scale, length = rec['meta']
    flux = len(peaks) / duration if duration > 0 else None
    tangent = abs(math.tan(math.radians(rec['angle'])))
    velocity = scale / period / tangent if scale > 0 and period > 0 and tangent > .001 else None
    gaps = [b-a for a,b in zip(peaks, peaks[1:])]
    mean = sum(gaps)/len(gaps) if gaps else 0
    cv = (sum((g-mean)**2 for g in gaps)/len(gaps))**.5 / mean if len(peaks)>=3 and mean>0 else None
    return {'Image':rec['image'], 'RBC Count':len(peaks), 'Duration (s)':duration, 'Angle (deg)':rec['angle'], 'Flux (RBCs/s)':flux, 'Velocity (um/s)':velocity, 'Lineal Density (RBCs/um)':flux/velocity if velocity and flux is not None else None, 'Inter-RBC CV':cv, 'Scan Rate (lines/s)':1/period if period>0 else None, 'Scale (um/px)':scale if scale>0 else None, 'QC Flag':rec.get('qc', 'OK'), 'Reviewed':rec['reviewed'], 'Automatic Count':len(rec['automatic_peaks']), 'Duration Source':rec.get('duration_source', '')}


def save_session(records, output):
    path = output / 'session.json'
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(records, indent=2))
    temp.replace(path)
    rows = [result_row(r) for r in sorted(records, key=lambda r:natural_key(r['image']))]
    for name in ('RBC_Results.csv', 'RBC_Results_sorted.csv'):
        path = output / name
        temp = path.with_suffix('.tmp')
        with temp.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({k: 'N/A' if v is None else v for k,v in row.items()} for row in rows)
        temp.replace(path)
    if all(rec['reviewed'] for rec in records):
        export_final_results(records, output)
    else:
        for name in ('RBC_Final_Results.csv', 'RBC_Final_Results.xlsx'):
            (output / name).unlink(missing_ok=True)


def final_rows(records):
    rows = []
    for rec in sorted(records, key=lambda r: natural_key(r['image'])):
        original, final = Counter(rec['automatic_peaks']), Counter(rec['peaks'])
        duration = rec['meta'][0]
        rows.append({'Image': rec['image'], 'Automatic Count': sum(original.values()),
                     'Lines Added': sum((final-original).values()),
                     'Lines Removed': sum((original-final).values()),
                     'Final RBC Count': sum(final.values()), 'Frame Period (s)': duration,
                     'Final Flux (RBCs/s)': sum(final.values())/duration if duration > 0 else None,
                     'Reviewed': rec['reviewed']})
    return rows


def export_final_results(records, output):
    """Write final counts and timing as CSV and a native Excel workbook."""
    if not records or not all(r['reviewed'] for r in records):
        raise ValueError('Review every image before exporting final results.')
    rows = final_rows(records)
    csv_path = output / 'RBC_Final_Results.csv'
    temp = csv_path.with_suffix('.tmp')
    with temp.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: 'N/A' if v is None else v for k,v in row.items()} for row in rows)
    temp.replace(csv_path)
    ordered = sorted(records, key=lambda r: natural_key(r['image']))
    headers = ['Line scan #', '# of lines', 'pixels/line', 'line scan period (s)',
               'total time (s)', '# of RBCs', '# RBCs/s']
    table = [[], headers]
    preview_indices = {id(rec): i for i, rec in enumerate(records)}
    for index, rec in enumerate(ordered, 1):
        match = re.search(r'(?:^|_)(\d+)_LineScan-', rec['image'])
        scan = int(match.group(1)) if match else index
        width = height = None
        preview_index = preview_indices[id(rec)]
        preview = output / 'previews' / f'{preview_index}.png'
        if preview.exists():
            from PIL import Image
            with Image.open(preview) as image:
                width, height = image.size
        duration, line_period = rec['meta'][:2]
        count = len(rec['peaks'])
        number = index + 2
        flux = ('formula', f'F{number}/E{number}', count/duration) if duration > 0 else None
        table.append([scan, height, width, line_period if line_period > 0 else None,
                      duration if duration > 0 else None, count, flux])
    sheets = [('Results', table, 2),
              ('Review Details', [list(rows[0])] + [list(row.values()) for row in rows], 1)]
    path = output / 'RBC_Final_Results.xlsx'
    _write_workbook(path, sheets)
    return path


def _write_workbook(path, sheets):
    """Write numeric cells, cached formulas, and an audit sheet without extra dependencies."""
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rel_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    rel_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    definitions, relationships, overrides = [], [], []
    temp = path.with_suffix('.tmp')
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        for sheet_index, (name, table, header_row) in enumerate(sheets, 1):
            xml_rows = []
            columns = max(len(row) for row in table)
            for number, values in enumerate(table, 1):
                cells = []
                for column, value in enumerate(values):
                    address = f'{chr(65+column)}{number}'
                    if isinstance(value, tuple) and value[0] == 'formula':
                        cells.append(f'<c r="{address}"><f>{escape(value[1])}</f><v>{value[2]}</v></c>')
                    elif isinstance(value, bool):
                        cells.append(f'<c r="{address}" t="b"><v>{int(value)}</v></c>')
                    elif isinstance(value, (int, float)) and math.isfinite(value):
                        cells.append(f'<c r="{address}"><v>{value}</v></c>')
                    else:
                        text = escape('N/A' if value is None else str(value))
                        cells.append(f'<c r="{address}" t="inlineStr"><is><t>{text}</t></is></c>')
                xml_rows.append(f'<row r="{number}">'+''.join(cells)+'</row>')
            first_width = 65 if name == 'Review Details' else 25
            worksheet = (f'<worksheet xmlns="{ns}"><sheetViews><sheetView workbookViewId="0">'
                         f'<pane ySplit="{header_row}" topLeftCell="A{header_row+1}" activePane="bottomLeft" state="frozen"/>'
                         f'</sheetView></sheetViews><cols><col min="1" max="1" width="{first_width}" customWidth="1"/>'
                         f'<col min="2" max="{columns}" width="23" customWidth="1"/></cols><sheetData>'
                         + ''.join(xml_rows) + f'</sheetData><autoFilter ref="A{header_row}:{chr(64+columns)}{len(table)}"/></worksheet>')
            target = f'worksheets/sheet{sheet_index}.xml'
            archive.writestr('xl/'+target, worksheet)
            definitions.append(f'<sheet name="{name}" sheetId="{sheet_index}" r:id="rId{sheet_index}"/>')
            relationships.append(f'<Relationship Id="rId{sheet_index}" Type="{rel_type}worksheet" Target="{target}"/>')
            overrides.append(f'<Override PartName="/xl/{target}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        contents = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                    + ''.join(overrides) + '</Types>')
        archive.writestr('[Content_Types].xml', contents)
        archive.writestr('_rels/.rels', f'<Relationships xmlns="{rel_ns}"><Relationship Id="rId1" Type="{rel_type}officeDocument" Target="xl/workbook.xml"/></Relationships>')
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="{rel_type[:-1]}"><sheets>'+''.join(definitions)+'</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', f'<Relationships xmlns="{rel_ns}">'+''.join(relationships)+'</Relationships>')
    temp.replace(path)
