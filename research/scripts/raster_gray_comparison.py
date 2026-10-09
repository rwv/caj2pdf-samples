#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded exact grayscale comparisons; never a fitted fidelity tolerance."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image

MAX_PIXELS = 4*1024*1024
MAX_FILE_BYTES = 16*1024*1024


def compare(first, second):
    for image in (first, second):
        if (not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.ndim != 3
                or image.shape[2] != 3 or not 0 < image.shape[0]*image.shape[1] <= MAX_PIXELS):
            raise ValueError('expected bounded uint8 RGB image')
        if not (np.array_equal(image[:, :, 0], image[:, :, 1]) and
                np.array_equal(image[:, :, 0], image[:, :, 2])):
            raise ValueError('grayscale discriminator cannot admit colored pixels')
    if first.shape != second.shape:
        raise ValueError('raster dimensions differ; no resize or alignment is permitted')
    a, b = first[:, :, 0], second[:, :, 0]
    changed = a != b
    ys, xs = np.where(changed)
    delta = b.astype(np.int16)-a.astype(np.int16)
    counts = np.bincount((a.astype(np.int32)*256+b).ravel(), minlength=65536).reshape(256,256)
    forward = np.count_nonzero(counts, axis=1)
    reverse = np.count_nonzero(counts, axis=0)
    return {'pixels': int(a.size), 'changed_pixels': int(changed.sum()),
            'channel_delta': [int(delta.min()), int(delta.max())],
            'bounds_exclusive': [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else None,
            'first_values_with_multiple_second': int((forward > 1).sum()),
            'second_values_with_multiple_first': int((reverse > 1).sum()),
            'maximum_second_levels_per_first': int(forward.max()),
            'coordinate_independent_lookup_possible': not bool((forward > 1).any()),
            'first_white_pixels_changed': int(counts[255].sum()-counts[255,255]),
            'first_black_pixels_changed': int(counts[0].sum()-counts[0,0])}


def read(path, expected):
    # Decode the same bounded bytes whose identity was checked. Reopening the
    # path could otherwise read different bytes after the hash check.
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if not 0 < len(data) <= MAX_FILE_BYTES:
        raise ValueError('PNG file byte bound')
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('PNG identity mismatch')
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG' or not 0 < image.width*image.height <= MAX_PIXELS:
            raise ValueError('PNG pixel/format bound')
        result = np.array(image.convert('RGB'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    parser.add_argument('--first-sha256', required=True)
    parser.add_argument('--second-sha256', required=True)
    args = parser.parse_args()
    result = compare(read(args.first,args.first_sha256),read(args.second,args.second_sha256))
    result['scope'] = 'Exact observation only. A possible gray lookup does not establish an internal mechanism; no correction, tolerance or fidelity verdict follows.'
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
