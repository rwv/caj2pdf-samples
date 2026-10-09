# SPDX-License-Identifier: MIT
"""Original misleading-trace controls for process, time and row identity."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jpeg_trace import matching_chains, read_trace


def row(sequence=0, time=10, process=21, compressor=1, width=397,
        height=561, rows=561, kind="FINISH_RGB", rgb="a" * 64,
        encoded="e" * 64):
    return "\t".join(map(str, [sequence, time, process, kind, sequence + 1,
        compressor, width, height, rows, 3, 2, 100, 0, "221111", 1,
        rgb, encoded, process])) + "\n"


class JpegTrace(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.tsv"
            path.write_text(text)
            return read_trace(path)

    def links(self, text, deadline=30):
        return matching_chains(self.read(text), "b" * 64, (397, 561), deadline)

    def test_finish_and_complete_rows_at_destroy_are_distinct_valid_links(self):
        for kind in ("FINISH_RGB", "RGB_ROWS_AT_DESTROY"):
            with self.subTest(kind=kind):
                links = self.links(row() + row(1, 20, compressor=0, kind=kind, rgb="b" * 64))
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0]["decoder"]["kind"], kind)
                self.assertNotEqual(links[0]["encoder"]["rgb_sha256"],
                                    links[0]["decoder"]["rgb_sha256"])

    def test_identical_bytes_from_another_process_do_not_form_a_chain(self):
        text = row() + row(0, 20, process=22, compressor=0, rgb="b" * 64)
        self.assertEqual(len(self.read(text)["events"]), 2)
        self.assertEqual(self.links(text), [])

    def test_reversed_time_late_decode_wrong_size_and_wrong_bytes_are_not_links(self):
        for changes in ({"time": 5}, {"time": 31}, {"encoded": "f" * 64},
                        {"width": 398}):
            with self.subTest(changes=changes):
                decoder = dict(sequence=1, time=20, compressor=0, rgb="b" * 64)
                decoder.update(changes)
                self.assertEqual(self.links(row() + row(**decoder)), [])

    def test_partial_destroy_and_missing_encoded_bytes_are_not_links(self):
        partial = row(1, 20, compressor=0, kind="INCOMPLETE_DESTROY", rows=560, rgb="")
        self.assertEqual(self.links(row() + partial), [])
        missing = row(1, 20, compressor=0, rgb="b" * 64, encoded="")
        self.assertEqual(self.links(row(encoded="") + missing), [])
        with self.assertRaises(ValueError):
            self.read(row(rows=560))
        with self.assertRaises(ValueError):
            self.read(row(kind="RGB_ROWS_AT_DESTROY"))

    def test_missing_process_sequence_and_digest_evidence_is_rejected(self):
        for text in (row().rsplit("\t", 1)[0] + "\n", row() + row(),
                     row(sequence=1), row(rgb="invalid"), "", row(width=4097)):
            with self.subTest(text=text[:60]), self.assertRaises(ValueError):
                self.read(text)

    def test_limits_and_ambiguous_encoders_remain_explicit(self):
        text = row() + row(1, 11) + row(2, 20, compressor=0, rgb="b" * 64)
        self.assertEqual(len(self.links(text)), 2)
        self.assertEqual(self.links(text + "LIMIT_EVENTS\n"), [])
        self.assertEqual(self.links(text + row(3, 25, kind="LIMIT_CONTEXTS")), [])

    def test_trace_and_record_bounds_are_enforced(self):
        with self.assertRaises(ValueError):
            self.read("x" * 513)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.tsv"
            with path.open("wb") as output:
                output.truncate(16 * 1024 * 1024 + 1)
            with self.assertRaises(ValueError):
                read_trace(path)

    def test_repeated_identical_encodings_cannot_expand_to_unbounded_matches(self):
        text = "".join(row(i, 10 + i) for i in range(100))
        text += "".join(row(100 + i, 1000 + i, compressor=0, rgb="b" * 64)
                        for i in range(101))
        with self.assertRaisesRegex(ValueError, "candidate pairs"):
            self.links(text, deadline=2000)


if __name__ == "__main__":
    unittest.main()
