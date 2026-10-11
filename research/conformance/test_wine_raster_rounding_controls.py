# SPDX-License-Identifier: MIT
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "cajviewer")]
from hnc8_layout_source import FileInput, SourceExtractor
from native_text_order import digest
from wine_raster_rounding_controls import CASES, control


class RasterControls(unittest.TestCase):
    def test_declared_page_and_placement_change_keeps_one_identical_type1_payload(self):
        hashes = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.caj"
            for name, parameters in CASES.items():
                data = control(*parameters)
                self.assertEqual(struct.unpack_from("<HH", data, 32), (parameters[0], 4800))
                path.write_bytes(data)
                with FileInput(path) as source:
                    page = next(SourceExtractor(source, digest(path)).iter_pages())
                self.assertEqual(page["image_count"], 1)
                self.assertEqual(page["images"][0]["record_type"], 1)
                hashes.append(page["images"][0]["payload_sha256"])
            self.assertEqual(len(set(hashes)), 1)
        baseline = control(*CASES["baseline"])
        wider = control(*CASES["width-plus1"])
        self.assertEqual([i for i, (a, b) in enumerate(zip(baseline, wider)) if a != b], [32])
        shifted = control(*CASES["placement-plus20"])
        self.assertEqual([i for i, (a, b) in enumerate(zip(baseline, shifted)) if a != b], [104, 106])


if __name__ == "__main__":
    unittest.main()
