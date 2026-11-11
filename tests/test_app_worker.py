"""Exercise analyzer progress without launching Fiji or a desktop window."""
import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rbc_app import App, completed_image_count


class ProgressTests(unittest.TestCase):
    def test_external_drive_sidecars_do_not_inflate_progress(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            folder = output / 'detections'
            folder.mkdir()
            for index in range(84):
                (folder / f'{index}.txt').write_text('45\nOK\n10\n')
            for index in range(8):
                (folder / f'._{index}.txt').write_bytes(b'Mac resource fork')
            self.assertEqual(len(list(folder.glob('*.txt'))), 92)
            self.assertEqual(completed_image_count(output, 84), 84)
            (folder / '83.txt').unlink()
            (folder / '84.txt').write_text('unrelated file')
            (folder / 'notes.txt').write_text('unrelated file')
            self.assertEqual(completed_image_count(output, 84), 83)

    def test_completed_images_and_export(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'detections').mkdir()
            app = App.__new__(App)
            app.events = queue.Queue()
            records = [dict(image='scan.tif', meta=[1.5, -1, -1, -1],
                            peaks=[], automatic_peaks=[], angle=0, reviewed=False)]

            class Process:
                calls = 0

                def wait(self, timeout):
                    self.calls += 1
                    if self.calls == 1:
                        (output / 'detections/0.txt').write_text('45\nOK\n10\n20\n30\n')
                        raise subprocess.TimeoutExpired('Fiji', timeout)
                    (output / 'complete.txt').write_text('complete')
                    return 0

            with patch('rbc_app.prepare', return_value=records), patch('rbc_app.build_macro', return_value=''), patch('rbc_app.subprocess.Popen', return_value=Process()):
                app.worker(output, output, Path('Fiji'), 1)
            events = list(app.events.queue)
            self.assertIn(('progress', (0, 1)), events)
            self.assertIn(('progress', (1, 1)), events)
            self.assertEqual(events[-1][0], 'done')
            self.assertEqual(records[0]['peaks'], [10, 20, 30])
            self.assertTrue((output / 'RBC_Results.csv').exists())

    def test_failure_does_not_report_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'detections').mkdir()
            app = App.__new__(App)
            app.events = queue.Queue()
            with patch('rbc_app.prepare', return_value=[{}]), patch('rbc_app.build_macro', return_value=''), patch('rbc_app.subprocess.Popen') as process:
                process.return_value.wait.return_value = 1
                app.worker(output, output, Path('Fiji'), 1)
            events = list(app.events.queue)
            self.assertEqual(events[-1][0], 'error')
            self.assertFalse(any(kind == 'done' for kind, _ in events))


if __name__ == '__main__':
    unittest.main()
