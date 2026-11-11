import csv
import json
import tempfile
import unittest
from pathlib import Path
from collect_linescans_updated import collect_linescans
from rbc_workflow import prepare, build_macro, import_detections, result_row, save_session

XML = '''<PVScan><PVStateShard><PVStateValue key="micronsPerPixel"><IndexedValue index="XAxis" value="0.5"/></PVStateValue></PVStateShard><Sequence cycle="1"><Frame index="1"><PVStateShard><PVStateValue key="scanLinePeriod" value="0.001"/><PVStateValue key="framePeriod" value="2"/></PVStateShard></Frame><Frame index="2"><PVStateShard><PVStateValue key="scanLinePeriod" value="0.002"/><PVStateValue key="framePeriod" value="4"/></PVStateShard></Frame></Sequence></PVScan>'''

class WorkflowTests(unittest.TestCase):
    def test_original_collector_default_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'original'
            scan = root / '7'
            scan.mkdir(parents=True)
            image = 'LineScan-X_Cycle00001_Ch3_000001.ome.tif'
            for name, data in ((image, b'image'), ('LineScan-X.xml', XML.encode()),
                               ('LineScan-X-Cycle00001_Ch3Source.tif', b'source'),
                               ('LineScan-extra.xml', b'<PVScan/>')):
                (scan / name).write_bytes(data)
            copied = collect_linescans(root, log=lambda _: None)
            self.assertEqual(len(copied), 4)
            self.assertEqual((root.parent / 'collected_ome_tif' / ('7_' + image)).read_bytes(), b'image')
            self.assertTrue((root.parent / 'collected_xml/7_LineScan-extra.xml').exists())
            self.assertEqual((scan / image).read_bytes(), b'image')

    def test_collection_metadata_collision_and_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'raw'
            for branch in ('a', 'b'):
                folder = root/branch/'1'
                folder.mkdir(parents=True)
                (folder/'LineScan-X_Cycle00001_Ch3_000001.ome.tif').write_bytes(b'source')
                (folder/'LineScan-X.xml').write_text(XML if branch == 'a' else XML.replace('value="2"', 'value="3"'))
            output = Path(temp)/'run'
            records = prepare(root, output, log=lambda _: None)
            self.assertEqual(len({r['image'] for r in records}), 2)
            self.assertEqual(records[0]['meta'][:3], [2, .001, .5])
            self.assertEqual({Path(r['source']).parts[-3]: r['meta'][0] for r in records}, {'a': 2, 'b': 3})
            macro = build_macro(records, output, 10)
            self.assertNotIn('macro "RBC Linescan Analyzer2.0"', macro)
            self.assertIn('count=detectRBCLines(imgID, true)', macro)
            for n in range(2):
                (output/'detections'/f'{n}.txt').write_text('45\nOK\n10\n20\n30\n')
            import_detections(records, output)
            records[0]['peaks'].append(40)
            records[0]['reviewed'] = True
            save_session(records, output)
            self.assertEqual(json.loads((output/'session.json').read_text())[0]['peaks'], [10,20,30,40])
            row = result_row(records[0])
            self.assertEqual(row['RBC Count'], 4)
            self.assertEqual(row['Automatic Count'], 3)
            self.assertEqual(row['Flux (RBCs/s)'], 2)
            self.assertAlmostEqual(row['Velocity (um/s)'], 500)
            self.assertAlmostEqual(row['Lineal Density (RBCs/um)'], .004)
            self.assertEqual(row['Inter-RBC CV'], 0)
            with (output/'RBC_Results.csv').open() as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)

    def test_no_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'raw'
            root.mkdir()
            with self.assertRaisesRegex(ValueError, 'No Ch3'):
                prepare(root, Path(temp)/'out')

    def test_missing_scale(self):
        row = result_row(dict(image='10_x', peaks=[], automatic_peaks=[], meta=[1,-1,-1,-1], angle=0, reviewed=False))
        self.assertEqual(row['Flux (RBCs/s)'], 0)
        self.assertIsNone(row['Velocity (um/s)'])
        self.assertIsNone(row['Inter-RBC CV'])

if __name__ == '__main__':
    unittest.main()
