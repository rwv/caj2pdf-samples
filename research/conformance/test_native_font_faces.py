# SPDX-License-Identifier: MIT
"""Original lifetime traces distinguish resources despite family/address reuse."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from native_font_faces import bind, isolated_mapping


def resource(sha, name):
    return {'resource': name, 'sha256': sha, 'family': 'Original_CNKI',
            'bytes': 1234, 'freetype_error': 0, 'face_index': 0,
            'num_faces': 1, 'num_glyphs': 8}


def fixtures():
    def face(event, clock, op, sha='a' * 64, pid=7):
        return [event, clock, pid, 8, op, '0xabc', 'Original_CNKI', 0, 0,
                'file' if op == 'open' else '-', 1234 if op == 'open' else 0,
                sha if op == 'open' else '-', '/fonts/font.ttf'.encode().hex() if op == 'open' else '-']
    def glyph(event, clock, op, a, b, depth=0):
        return [event, clock, 7, 8, op, '0xabc', 'Original_CNKI', a, b, 0, 20, 20, depth]
    faces = [face(0, 10, 'open'), face(1, 20, 'reference'), face(2, 30, 'done'),
             face(3, 60, 'done'), face(4, 70, 'open', 'b' * 64), face(5, 100, 'done'),
             face(0, 15, 'open', pid=9), face(1, 25, 'done', pid=9)]
    glyphs = [glyph(0, 40, 'cmap', 200, 2), glyph(1, 45, 'load', 2, 75785, 1),
              glyph(2, 50, 'load', 2, 65548), glyph(3, 80, 'cmap', 200, 3),
              glyph(4, 90, 'load', 3, 65548)]
    return faces, glyphs, [resource('a' * 64, 'one.ttf'), resource('b' * 64, 'two.ttf')]


class FaceBindingTests(unittest.TestCase):
    def run_case(self, faces, glyphs, resources, marker=None, isolated=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, rows in [('ft-faces.tsv', faces), ('ft-events.tsv', glyphs)]:
                (root / name).write_text(''.join('\t'.join(map(str, row)) + '\n' for row in rows))
            if marker:
                (root / marker).touch()
            binding = bind(root / 'ft-faces.tsv', root / 'ft-events.tsv', resources)
            return isolated_mapping(root / 'ft-events.tsv', binding) if isolated else binding

    def test_reference_lifetimes_processes_and_pointer_reuse_are_distinguished(self):
        result = self.run_case(*fixtures())
        self.assertEqual(result['status'], 'OBSERVED_CALLS_BOUND')
        self.assertEqual(result['face_processes'], 2)
        self.assertEqual(result['live_faces_at_trace_end'], 0)
        self.assertEqual([(r['sha256'], r['rendered_glyph_ids'], r['outer_render_loads'])
                          for r in result['resources']], [('a' * 64, [2], 1), ('b' * 64, [3], 1)])
        self.assertEqual(result['resources'][0]['nested_events'], 1)
        faces, glyphs, resources = fixtures()
        # Append ordering can differ across threads/processes. Actual clocks
        # and complete per-process event-number sets determine the same result.
        self.assertEqual(self.run_case(faces[::-1], glyphs[::-1], resources)['resources'], result['resources'])

    def test_unknown_or_opaque_resource_identity_cannot_be_assigned(self):
        for column, value in [(11, 'c' * 64), (11, 'unmeasured'), (9, 'opaque-stream'),
                              (10, 999), (6, 'Different_CNKI'), (7, 1), (8, 6), (12, 'invalid')]:
            with self.subTest(column=column, value=value):
                faces, glyphs, resources = fixtures(); faces[0][column] = value
                with self.assertRaises(ValueError):
                    self.run_case(faces, glyphs, resources)

    def test_missing_reference_overlapping_open_or_stale_face_is_refused(self):
        for index, column, value in [(1, 4, 'done'), (1, 4, 'open'), (3, 1, 35),
                                      (4, 1, 55), (0, 5, '0xdef')]:
            with self.subTest(index=index, column=column, value=value):
                faces, glyphs, resources = fixtures(); faces[index][column] = value
                with self.assertRaises(ValueError):
                    self.run_case(faces, glyphs, resources)

    def test_api_errors_glyph_bounds_and_equal_timestamp_ambiguity_are_refused(self):
        for index, column, value in [(2, 9, 1), (2, 7, 0), (2, 7, 8), (0, 8, 8),
                                      (2, 6, 'Other_CNKI'), (2, 1, 60), (2, 2, 99)]:
            with self.subTest(index=index, column=column, value=value):
                faces, glyphs, resources = fixtures(); glyphs[index][column] = value
                with self.assertRaises(ValueError):
                    self.run_case(faces, glyphs, resources)

    def test_trace_and_resource_incompleteness_is_refused(self):
        for marker in ['ft-limit', 'ft-face-limit']:
            with self.assertRaisesRegex(ValueError, 'event limit'):
                self.run_case(*fixtures(), marker=marker)
        faces, glyphs, resources = fixtures()
        for changed in [glyphs[1:], glyphs + [glyphs[0]], []]:
            with self.assertRaises(ValueError):
                self.run_case(faces, changed, resources)
        for changed in [resources + [resources[0]], [{**resources[0], 'num_faces': 2}]]:
            with self.assertRaises(ValueError):
                self.run_case(faces, glyphs, changed)

    def test_isolated_mapping_reports_observed_sizes_without_inventing_missing_calls(self):
        faces, glyphs, resources = fixtures()
        result = self.run_case(faces[:4], glyphs[:3], resources, isolated=True)
        self.assertEqual((result['cmap_argument'], result['glyph_id']), (200, 2))
        self.assertEqual(result['observed_sizes'], [[20, 20]])
        self.assertEqual(result['missing_size_coverage'], 'UNVERIFIED')
        with self.assertRaisesRegex(ValueError, 'one bound resource'):
            self.run_case(*fixtures(), isolated=True)

    def test_isolated_mapping_refuses_probes_extra_glyphs_and_unpaired_loads(self):
        for mutation in ('probe', 'unpaired', 'second-glyph', 'changed-alias'):
            with self.subTest(mutation=mutation):
                faces, glyphs, resources = fixtures(); faces, glyphs = faces[:4], glyphs[:3]
                if mutation == 'probe':
                    glyphs[1][4:5] = ['cmap']; glyphs[1][7:13] = [201, 2, 0, 20, 20, 0]
                elif mutation == 'unpaired':
                    glyphs[0][8] = 3
                else:
                    extra = [list(glyphs[0]), list(glyphs[2])]
                    for i, row in enumerate(extra):
                        row[0], row[1] = 3 + i, 51 + i
                        if mutation == 'changed-alias':
                            row[10:12] = [30, 30]
                    if mutation == 'changed-alias':
                        extra[0][7] = 201
                    glyphs.extend(extra)
                with self.assertRaises(ValueError):
                    self.run_case(faces, glyphs, resources, isolated=True)


if __name__ == '__main__':
    unittest.main()
