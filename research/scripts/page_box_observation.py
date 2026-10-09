#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fixed-grid observations for original 80% Letter capture protocols.

The grid and frame probes come from original controls, never candidate fitting.
These observations do not establish general viewer readiness or lost geometry.
"""
import hashlib
import numpy as np

GRID = (499, 245, 1150, 1088)


def page_grid(page, total, mode='single'):
    if type(page) is not int or type(total) is not int or not 1 <= page <= total <= 75:
        raise ValueError('page outside bounded inventory')
    if mode == 'single':
        return GRID
    if mode == 'continuous' and total == 75:
        # The last page is clamped at the viewport bottom. These positions
        # were measured on original controls before any corpus observations.
        return (499, 325, 1150, 1168) if page == 75 else (499, 157, 1150, 1000)
    raise ValueError('unsupported capture profile')


def page_pixels(frame, *, page_field, zoom_field, page, total, markers=False, mode='single'):
    if (not isinstance(frame, np.ndarray) or frame.dtype != np.uint8
            or frame.shape != (1200, 1600, 3)):
        raise ValueError('unexpected full-frame raster grid')
    x0, y0, x1, y1 = page_grid(page, total, mode)
    if page_field != f'{page}/{total}' or zoom_field != '80%':
        raise ValueError('page/zoom state not confirmed')
    corners = ((x0-1, y0-1), (x1, y0-1), (x0-1, y1), (x1, y1))
    if any(not np.all(frame[y, x] == 209) for x, y in corners):
        raise ValueError('complete Letter page frame not confirmed')
    if markers:
        observed = 0
        for bit in range(7):
            # Probe centers are derived from the original PDF marker boxes.
            x = x0+round((46+20*bit)*651/612)
            y = y0+round((792-746)*843/792)
            patch = frame[y-1:y+2, x-1:x+2]
            if np.all(patch == 0):
                observed |= 1 << bit
            elif not np.all(patch == 255):
                raise ValueError('original page marker not confirmed')
        if observed != page:
            raise ValueError('original page marker identity differs')
    return frame[y0:y1, x0:x1].copy()


def difference(first, second):
    if any(not isinstance(a,np.ndarray) or a.dtype != np.uint8
           or a.shape != (843,651,3) for a in (first,second)):
        raise ValueError('complete declared page grids required')
    delta = second.astype(np.int16)-first.astype(np.int16)
    changed = np.any(delta != 0,axis=2)
    ys,xs = np.where(changed)
    return {'changed_pixels':int(changed.sum()),
            'channel_delta':[int(delta.min()),int(delta.max())],
            'bounds_exclusive':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None,
            'first_rgb_sha256':hashlib.sha256(first.tobytes()).hexdigest(),
            'second_rgb_sha256':hashlib.sha256(second.tobytes()).hexdigest()}
