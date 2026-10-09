#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure page raster differences without registration or a pass tolerance.

Viewer rasters and PDF renders stay external. Width sets one uniform PDF scale;
integer grid differences and nonoverlapping ink are reported explicitly. These
measurements cannot establish source font fidelity or identify a converter bug.
"""
import argparse
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

from native_text_order import digest

MAX_PIXELS = 4 * 1024 * 1024


def metrics(source, output):
    if (source.ndim != 2 or output.ndim != 2 or not source.size or not output.size
            or source.size > MAX_PIXELS or output.size > MAX_PIXELS):
        raise ValueError('grayscale raster dimensions outside bound')
    height, width = min(source.shape[0], output.shape[0]), min(source.shape[1], output.shape[1])
    a, b = source < 128, output < 128
    full = (max(source.shape[0], output.shape[0]), max(source.shape[1], output.shape[1]))
    if full[0] * full[1] > MAX_PIXELS:
        raise ValueError('comparison grid exceeds bound')
    left, right = np.zeros(full, dtype=bool), np.zeros(full, dtype=bool)
    left[:a.shape[0], :a.shape[1]], right[:b.shape[0], :b.shape[1]] = a, b

    def distances(first, second):
        if not first.any():
            return {'ink_pixels': 0, 'distance_quantiles': None}
        if not second.any():
            return {'ink_pixels': int(first.sum()), 'distance_quantiles': None, 'opposite_is_blank': True}
        values = distance_transform_edt(~second)[first]
        return {'ink_pixels': int(first.sum()),
                'distance_quantiles': dict(zip(('p50', 'p90', 'p95', 'p99', 'max'),
                                               map(float, np.quantile(values, (.5, .9, .95, .99, 1))))),
                'distance_gt_1': int((values > 1).sum()), 'distance_gt_2': int((values > 2).sum()),
                'distance_gt_4': int((values > 4).sum())}

    return {'status': 'MEASURED_NO_FIDELITY_VERDICT', 'threshold': 128,
            'source_size': list(reversed(source.shape)), 'pdf_size': list(reversed(output.shape)),
            'common_grid': [width, height],
            'common_grayscale_differences': int((source[:height, :width] != output[:height, :width]).sum()),
            'common_mask_differences': int((a[:height, :width] != b[:height, :width]).sum()),
            'source_nonoverlapping_ink': int(a.sum() - a[:height, :width].sum()),
            'pdf_nonoverlapping_ink': int(b.sum() - b[:height, :width].sum()),
            'source_to_pdf': distances(left, right), 'pdf_to_source': distances(right, left)}


def compare(capture_directory, pdf, pdf_sha256, output):
    if digest(pdf) != pdf_sha256:
        raise ValueError('PDF digest mismatch')
    pages = json.loads((capture_directory / 'pages.json').read_text())
    output.mkdir(exist_ok=False)
    result = []
    with fitz.open(pdf) as document:
        if len(document) != len(pages):
            raise ValueError('page inventory mismatch')
        for index, observed in enumerate(pages):
            row = {'page': index + 1}
            if observed['page'] != index + 1:
                raise ValueError('page inventory order mismatch')
            if observed['status'] != 'STABLE':
                row.update(status='NOT_MEASURED', reason=observed.get('reason', observed['status']))
            else:
                reference = capture_directory / observed['first']['pixmap']['file']
                if digest(reference) != observed['first']['pixmap']['sha256']:
                    raise ValueError('reference raster changed')
                with Image.open(reference) as image:
                    if image.width * image.height > MAX_PIXELS:
                        raise ValueError('reference pixel limit')
                    source = np.asarray(image.convert('L'))
                page = document[index]
                scale = source.shape[1] / page.rect.width
                if page.rect.width * page.rect.height * scale * scale > MAX_PIXELS - 8192:
                    raise ValueError('PDF render pixel limit')
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
                rendered = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
                target = output / f'page-{index + 1:03d}.png'
                pixmap.save(target)
                row.update(metrics(source, rendered))
                row.update(reference_sha256=digest(reference), pdf_render_sha256=digest(target),
                           uniform_scale=scale, pdf_page_box=list(page.rect))
            result.append(row)
            (output / 'pages.json').write_text(json.dumps(result, indent=2) + '\n')
    if digest(pdf) != pdf_sha256:
        raise ValueError('PDF changed during comparison')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture_directory', type=Path)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--pdf-sha256', required=True)
    args = parser.parse_args()
    compare(args.capture_directory, args.pdf, args.pdf_sha256, args.output)
