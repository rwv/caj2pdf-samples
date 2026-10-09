#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded exact RGB differences, without alignment or acceptance tolerance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from raster_gray_comparison import MAX_PIXELS, read


def confirm_original_page_five(image):
    """Identify the authored six-page fixture by marker occupancy, not shade.

    The authored bits use black (0) and white (255). Decode their fixed
    positions at the source levels' midpoint, 128; do not require a renderer
    to preserve those endpoint values. This establishes page identity only.
    It is not a pixel-match tolerance: every value, including marker pixels,
    still participates in the separate exact RGB comparison.
    """
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
            or image.shape not in ((561,397,3), (562,397,3))):
        raise ValueError('unexpected original-control page grid')
    height, width = image.shape[:2]
    y = round((841.8898-814.5)*height/841.8898)
    for n in range(6):
        x = round((35.5+16*n)*width/595.2756)
        patch = image[y-1:y+2, x-1:x+2]
        grayscale = np.all(patch == patch[:, :, :1])
        expected_bit = np.all(patch < 128) if n < 5 else np.all(patch >= 128)
        if not (grayscale and expected_bit):
            raise ValueError('original page-five marker inventory differs')
        for dx, dy in ((5,0), (0,10)):
            guard = image[y+dy-1:y+dy+2, x+dx-1:x+dx+2]
            if not (np.all(guard >= 128) and np.all(guard == guard[:, :, :1])):
                raise ValueError('original marker background not confirmed')


def compare(first, second):
    for image in (first, second):
        if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
                or image.ndim != 3 or image.shape[2] != 3
                or not 0 < image.shape[0]*image.shape[1] <= MAX_PIXELS):
            raise ValueError('expected bounded uint8 RGB image')
    if first.shape != second.shape:
        raise ValueError('raster dimensions differ; no resizing or alignment')
    delta = second.astype(np.int16)-first.astype(np.int16)
    maximum = np.abs(delta).max(axis=2)
    changed = maximum != 0
    ys, xs = np.where(changed)
    chromatic = (np.any(first != first[:, :, :1], axis=2)
                 | np.any(second != second[:, :, :1], axis=2))
    bins = np.bincount(maximum.ravel(), minlength=256)
    return {
        'pixels': int(changed.size), 'changed_pixels': int(changed.sum()),
        'channel_delta': [int(delta.min()), int(delta.max())],
        'per_channel_delta': [[int(delta[:, :, c].min()), int(delta[:, :, c].max())] for c in range(3)],
        'bounds_exclusive': [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else None,
        'maximum_absolute_delta_counts': {str(i): int(n) for i, n in enumerate(bins) if n},
        'changed_involving_chromatic_pixels': int((changed & chromatic).sum()),
        'changed_gray_in_both': int((changed & ~chromatic).sum()),
        'first_rgb_sha256': hashlib.sha256(first.tobytes()).hexdigest(),
        'second_rgb_sha256': hashlib.sha256(second.tobytes()).hexdigest(),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    parser.add_argument('--first-sha256', required=True)
    parser.add_argument('--second-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(compare(read(args.first, args.first_sha256),
                             read(args.second, args.second_sha256)), indent=2))
