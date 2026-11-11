"""Exercise analyzer progress without launching Fiji or a desktop window."""
import queue
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rbc_app import App, completed_image_count


class ProgressTests(unittest.TestCase):
    def test_parallel_workers_have_disjoint_outputs_and_keep_order(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output/'detections').mkdir()
            app = App.__new__(App)
            app.events = queue.Queue()
            records = [dict(image=f'{i}_scan.tif', meta=[1.5, -1, -1, -1],
                            peaks=[], automatic_peaks=[], angle=0, reviewed=False) for i in range(4)]
            started = []

            class Process:
                calls = 0

                def __init__(self, command, **kwargs):
                    self.macro = Path(command[-1])
                    self.text = self.macro.read_text()
                    self.index = len(started)
                    started.append(self)

                def wait(self, timeout):
                    self.calls += 1
                    # Both Fiji instances must start before either is waited on.
                    if len(started) != 2:
                        raise AssertionError('Workers were started sequentially')
                    if self.index == 0 and self.calls == 1:
                        raise subprocess.TimeoutExpired('Fiji', timeout)
                    for index in re.findall(r'/detections/(\d+)\.txt', self.text):
                        (output/'detections'/f'{index}.txt').write_text(f'45\nOK\n{index}\n')
                    (output/f'worker_{self.index+1}_complete.txt').write_text('complete')
                    return 0

            with patch('rbc_app.prepare', return_value=records), patch('rbc_app.subprocess.Popen', side_effect=Process):
                app.worker(output, output, Path('Fiji'), 1, 2)
            events = list(app.events.queue)
            self.assertEqual(events[-1][0], 'done')
            self.assertEqual([r['peaks'] for r in records], [[0], [1], [2], [3]])
            indices = [re.findall(r'/detections/(\d+)\.txt', proc.text) for proc in started]
            self.assertEqual(indices, [['0', '2'], ['1', '3']])
            self.assertTrue((output/'complete.txt').exists())
            self.assertTrue(all(0 <= done <= total == 4 for kind, value in events if kind == 'progress' for done,total in [value]))
            self.assertEqual(app.processes, [])

    def test_failed_parallel_worker_stops_other_worker(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output/'detections').mkdir()
            app = App.__new__(App)
            app.events = queue.Queue()
            records = [dict(image=f'{i}.tif', meta=[1, -1, -1, -1]) for i in range(2)]
            from unittest.mock import Mock
            failed = Mock()
            failed.wait.return_value = 1
            failed.poll.return_value = 1
            running = Mock()
            running.poll.return_value = None
            with patch('rbc_app.prepare', return_value=records), patch('rbc_app.subprocess.Popen', side_effect=[failed, running]):
                app.worker(output, output, Path('Fiji'), 1, 2)
            running.terminate.assert_called_once()
            self.assertEqual(list(app.events.queue)[-1][0], 'error')
            self.assertFalse((output/'complete.txt').exists())

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
