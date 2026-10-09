# SPDX-License-Identifier: MIT
"""Existing original-control glyph models, evaluated independently with rationals.

Source: c8-native-records/controls, c8-additional-profiles, hnb-compact-index,
hnb-magnesium-profile and Rust #391 provenance. Original MIT Rust was consulted
for coverage; this is model consistency, not a newly discovered format oracle.
"""
from fractions import Fraction as F
import struct

from native_text_order import character, read_exact, source_glyphs
from source_image_geometry import UNIT, require

EM = F(75, 301)
STEPS = (21, 24, 28, 31, 35, 42, 48, 56, 63, 72, 84)
LATIN_DOWN = (11, 10, 9, 9, 8, 6, 5, 3, 1, -1, -4)
AXIS_DOWN = {1: 0, 4: 15, 22: 11, 28: 9, 34: 8, 36: 8, 38: 7, 40: 7, 43: 6}
# Opening/closing parenthesis x, parenthesis down, square x/down.
BRACKETS = ((18, 16, 3, 24, 1), (19, 18, 1, 27, -1), (22, 21, 0, 30, -3),
            (26, 25, -4, 36, -7), (30, 28, -7, 41, -10),
            (35, 33, -10, 48, -15), (39, 37, -14, 54, -18))
EXPLICIT_BRACKETS = {22: (14, 13, 6, 19, 4), 34: (21, 20, 0, 29, -3),
                     40: (25, 23, -2, 34, -5), 43: (27, 25, -4, None, None)}
LATIN_ROLES = {0: 'latin', 4: 'alternate-latin', 3: 'latin-state3',
               28: 'latin-state28', 31: 'latin-state31'}
CURRENT_SYMBOLS = {0xa0a6, 0xa0ae, 0xa0af, 0xa0ba, 0xaab1, 0xaab2,
                   0xa1aa, 0xa1ab, 0xa1ad, 0xa1ae, 0xa1af, 0xa3a3, 0xa3a5,
                   0xa3a7, 0xa3dc, *range(0xa2d9, 0xa2e0), *range(0xa3ab, 0xa3ba),
                   *range(0xa3bb, 0xa3c1), *range(0xa3fb, 0xa3fe)}
FIXED_SYMBOLS = {0xa1c6, 0xa1c8, 0xa9aa, 0xaab3, 0xaca3}
C8_SYMBOLS = {0xa1c1, 0xa1de, 0xa1e4, 0xa6b8, 0xa6c4, 0xa6c5, 0xa6c8}
HNB_SYMBOLS = {0xa0ad, 0xa1b4, 0xa1b5, 0xa1c0, 0xa1c1, 0xa1c3, 0xa1e4,
               0xa2f2, 0xa6b8, 0xa6c4, 0xa6cc, 0xa6d2, 0xa661, 0xa6c2}
PAREN = {0xa1b0, 0xa1b1, 0xa1b2, 0xa1b3, 0xa1b6, 0xa1b7, 0xa3a8, 0xa3a9}
SQUARE = {0xa3db, 0xa3dd}
MODE0_SYMBOLS = {0x9ff5, 0xa1a1, 0xa1a2, 0xa1a3, 0xa1aa, 0xa1ae, 0xa1af,
                 0xa1b0, 0xa1b1, 0xa3a7, *range(0xa3ab, 0xa3af),
                 0xa3ba, 0xa3bb, 0xa3bf, 0xa3db, 0xa3dd, 0xaab1, 0xaab2}


def dimensions(style, axes, mode, variant):
    if axes != (None, None):
        a, b = axes
        require(mode != 0 or axes == (36, 36), 'unmeasured legacy axes')
        allowed = {1, 4, 22, 34, 36, 38, 40} if variant == 'C8' else {28, 36, 43}
        require(a in allowed and b in allowed, 'unmeasured variant axes')
        require((a == b and a in AXIS_DOWN) or (a in (28, 43) and b in (28, 43)),
                'unmeasured glyph axes')
        return a * EM, b * EM, AXIS_DOWN[b]
    if mode == 0:
        require(style in (0, 0x1000, 0x0484, 0x0884, 0x1084, 0x9c84, 0x0ca4,
                          0x10a4, 0x10a5, 0x04e7, 0x0ce7, 0x154a), 'unmeasured legacy style')
        if style == 0:
            style = 0x1000
    if style == 0x096b and variant == 'C8':
        return 95 * EM, 95 * EM, 0  # Only the controlled CJK/symbol geometry.
    if style in (0xe58c, 0x114a, 0x154a, 0xb94c):
        return (109 if style == 0xe58c else 84) * EM, (109 if style in (0xe58c, 0xb94c) else 84) * EM, 0
    width, height = (style >> 5) & 31, style & 31
    if width < 2 or height < 2:
        small = {0x1000, 0x1021} if variant == 'HN-B' else {0x1000, 0x1001, 0x1020, 0x1021, 0x1022, 0x1041}
        require(style in small, 'unmeasured small glyph style')
    if style & 0xfc00 == 0x0400 and variant == 'HN-B' and mode == 2:
        require(2 <= width <= 8 and 2 <= height <= 8, 'unmeasured HN-B regular flags')
        style = 0x1000 | (style & 0x03ff)
    require(width < len(STEPS) and height < len(STEPS), 'unmeasured glyph size fields')
    require(style & 0xfc00 in (0x0800, 0x0c00, 0x1000)
            or style in (0x04e7, 0x14e7, 0x0484, 0x1484, 0x9c84, 0x04c6, 0x14c6, 0x14a5, 0xa4a5),
            'unmeasured glyph style')
    return STEPS[width] * EM, STEPS[height] * EM, LATIN_DOWN[height]


def bracket_offset(code, style, axes, variant):
    if code not in PAREN | SQUARE:
        return 0, 0
    width, height = (style >> 5) & 31, style & 31
    if axes == (None, None):
        if code in SQUARE and style in (0x1021, 0x1022, 0x1041):
            return {0x1021: (21, 3), 0x1022: (21, 1), 0x1041: (24, 3)}[style]
        if code in (0xa1b2, 0xa1b3):
            return (21, 6) if height == 4 else (25, 5)
        require(2 <= width <= 8 and 2 <= height <= 8, 'unmeasured bracket fields')
        horizontal, vertical = BRACKETS[width - 2], BRACKETS[height - 2]
    else:
        a, b = axes
        require(a == b, 'unmeasured rectangular bracket axes')
        if code in (0xa1b2, 0xa1b3) and variant == 'HN-B':
            require(a in (28, 43), 'unmeasured tortoise bracket axes')
            return {28: (16, 8), 43: (25, 4)}[a]
        require(a in EXPLICIT_BRACKETS, 'unmeasured bracket axes')
        horizontal = vertical = EXPLICIT_BRACKETS[a]
    if code in SQUARE:
        require(horizontal[3] is not None, 'unmeasured square bracket axes')
        return horizontal[3], vertical[4]
    column = 0 if code in (0xa1b6, 0xa1b7, 0xa3a8) else 1
    extra = {0xa1b6: 4, 0xa1b7: -6}.get(code, 0)
    # Explicit-43 book marks use x=30/20; ordinary style-5 uses the same x.
    if axes == (43, 43) and code in (0xa1b6, 0xa1b7):
        return {0xa1b6: 30, 0xa1b7: 20}[code], -4
    return horizontal[column] + extra, vertical[2]


class Model:
    def __init__(self, variant, mode, origin, height):
        self.variant, self.mode, self.origin, self.height = variant, mode, origin, height
        self.style, self.axes, self.y = 0, (None, None), None
        self.role, self.cjk, self.shear, self.gray = 'latin', False, F(0), F(68, 255)

    def control(self, source, at, tag, value):
        if tag == 0x8001:
            self.y = value
        elif tag == 0x8002:
            self.style, self.axes = value, (None, None)
            if self.variant == 'C8':
                self.style = {0x6084: 0x1084, 0x0508: 0x1108, 0x64c6: 0x10c6}.get(value, value)
        elif tag in (0x8070, 0x8071):
            axes = list(self.axes); axes[tag - 0x8070] = value; self.axes = tuple(axes)
        elif tag == 0x801d:
            require(value in LATIN_ROLES, 'unmeasured font state')
            self.role = LATIN_ROLES[value]
        elif tag == 0x80ce:
            require(value in (0, 1), 'unmeasured CJK state')
            self.cjk = self.variant == 'C8' and value == 0
        elif tag == 0x8024:
            require(value in (0x2800, 0x2815, 0x281c, 0x281d), 'unmeasured shear')
            self.shear = {0x2800: F(0), 0x2815: F(105, 1000),
                          0x281c: F(225, 1000), 0x281d: F(24, 100)}[value]
        elif tag == 0x81ff:
            require(value in (1, 2, 3) and read_exact(source, at + 4, 4) == struct.pack('<HH', 0, 200),
                    'unmeasured glyph color')
            self.gray = F(0)

    def glyph(self, x, code):
        require(self.y is not None, 'glyph without source y')
        char = character(code, self.mode)
        w, h, latin_down = dimensions(self.style, self.axes, self.mode, self.variant)
        if self.axes == (None, None) and self.style in (0xe58c, 0x114a, 0x154a, 0xb94c):
            require(0x3400 <= ord(char) <= 0x9fff, 'unmeasured title glyph class')
            require(self.variant == 'C8' or self.style != 0xb94c, 'unmeasured title variant')
        if self.variant == 'HN-B' and code == 0xa6c2:
            require(self.mode == 2 and self.style == 0x10a5 and self.axes == (None, None), 'unmeasured beta style')
        left = (x - self.origin[0] + 20) * UNIT
        top = (self.y - self.origin[1]) * UNIT
        role = self.role
        if self.mode == 0:
            require(self.variant == 'HN-B', 'unmeasured mode-0 variant')
            if code in MODE0_SYMBOLS:
                role = 'symbols'
                down = 0 if code in (0xa3ba, 0xa3db, 0xa3dd) else 10
            elif code in (0xa3a8, 0xa3a9):
                role, down = 'latin', 0
            elif code == 0xa3af:
                role, down = 'cjk', 0
            elif 0xa980 <= code <= 0xa9b3:
                role, down = 'alternate-latin', 10
            elif 0xa3b0 <= code <= 0xa3b9 or 0xa3c1 <= code <= 0xa3da or 0xa3e1 <= code <= 0xa3fa:
                role, down = 'latin', 10
            else:
                require(0x3400 <= ord(char) <= 0x9fff, 'unmeasured legacy character class')
                role, down = 'cjk', 0
            if 0xa3b0 <= code <= 0xa3b9:
                size = 4 if self.axes == (36, 36) else self.style & 31
                require(size in (0, 4, 5), 'unmeasured mode-0 digit')
                dx, down = {0: (21, 15), 4: (22, 18), 5: (22, 20)}[size]
                left -= dx * UNIT
            if code == 0xaab2:
                size = 4 if self.axes == (36, 36) else self.style & 31
                require(size in (0, 4, 5), 'unmeasured mode-0 hyphen')
                left -= {0: 31, 4: 33, 5: 34}[size] * UNIT
            top += down * UNIT
            geometry = 'legacy-' + role + '-' + str(down)
            shear, gray = F(0), F(68, 255)
        else:
            if code in (0x006c, 0x0070):
                role, geometry = 'cjk', 'symbol'
            elif self.cjk:
                require((char.isascii() and char.isalnum()) or 0x3400 <= ord(char) <= 0x9fff
                        or 0xa3c1 <= code <= 0xa3da or 0xa3e1 <= code <= 0xa3fa, 'unmeasured CJK-mode class')
                role, geometry = 'cjk', 'cjk'
            elif code in ({0xa1ce, 0xa1fa} if self.variant == 'C8' else {0xa1d6, 0xa1dd}):
                self.role = role = 'latin'
                geometry = 'symbol'
            elif code in CURRENT_SYMBOLS or code in (C8_SYMBOLS if self.variant == 'C8' else HNB_SYMBOLS):
                geometry = 'symbol'
            elif code in FIXED_SYMBOLS:
                role, geometry = 'latin', 'symbol'
            elif code in (0xa1a4, 0xa3ba):
                geometry = 'raised-symbol'
            elif code in PAREN:
                geometry = 'cjk'
            elif code in SQUARE:
                role, geometry = 'latin', 'cjk'
            elif code in (0xa1a1, 0xa3a6) or (self.variant == 'C8' and (0xa3c1 <= code <= 0xa3da or 0xa3e1 <= code <= 0xa3fa)):
                role, geometry = 'cjk', 'cjk'
            elif code in (0xa1a2, 0xa1a3):
                geometry = 'punctuation'
            elif char.isascii() and char.isalnum():
                geometry = 'latin'
            elif 0x3400 <= ord(char) <= 0x9fff:
                role, geometry = 'cjk', 'cjk'
            else:
                raise ValueError(f'unmeasured source glyph class {code:04x}')
            if self.style == 0x096b or self.axes == (1, 1):
                require(geometry not in ('latin', 'punctuation'), 'unmeasured NJU Latin baseline')
            if geometry in ('latin', 'punctuation'):
                top += (latin_down - 15) * UNIT
                if geometry == 'latin':
                    left += w / 8
            elif geometry == 'cjk':
                top -= 15 * UNIT
            elif geometry == 'raised-symbol':
                top -= h / 8
            dx, dy = bracket_offset(code, self.style, self.axes, self.variant)
            left += dx * UNIT; top += dy * UNIT
            if code in (0xa1a4, 0xa1af):
                width = (self.style >> 5) & 31
                require(self.axes == (None, None) and 2 <= width <= 8, 'unmeasured dot/quote')
                left += (7, 7, 8, 10, 11, 13, 15)[width - 2] * UNIT
            if self.variant == 'HN-B' and code == 0xa6c2:
                top += 25 * UNIT
            shear, gray = self.shear, self.gray
        return {'matrix': (w, F(0), w * shear, h, left, self.height * UNIT - top - h),
                'gray': gray, 'role': role, 'character': char, 'kind': 'g', 'clip': None,
                'profile': f'{self.mode}/{self.style:04x}/{self.axes[0]}/{self.axes[1]}/{code:04x}',
                'state': f'{self.mode}/{self.style:04x}/{self.axes[0]}/{self.axes[1]}/{geometry}/{role}/{self.cjk}/{shear}/{gray}'}

    def ornaments(self, value, points):
        require(self.variant == 'C8' and self.mode == 2 and value in (1, 2, 46, 117), 'unmeasured ornament')
        require(value != 117 or (self.style in (0x1084, 0x10a5) and self.axes == (None, None)),
                'unmeasured ornament 117 state')
        require((self.axes == (None, None) and 2 <= ((self.style >> 5) & 31) <= 8 and 2 <= (self.style & 31) <= 8)
                or self.axes in ((34, 34), (40, 40)), 'unmeasured ornament dimensions')
        width, height, _ = dimensions(self.style, self.axes, self.mode, self.variant)
        x, y, end, end_y = points
        require(end > x and y == end_y, 'unmeasured ornament direction')
        left, span = (x - self.origin[0]) * UNIT, (end - x) * UNIT
        ratio = span / width
        count = -(-ratio.numerator // ratio.denominator)
        require(count <= 1000, 'ornament repetition bound')
        return [{'matrix': (width, F(0), F(0), height, left + i * width,
                            (self.height - y + self.origin[1]) * UNIT - height / 2),
                 'gray': F(0), 'role': 'latin', 'character': '', 'kind': 'o',
                 'clip': (left, F(0), span, self.height * UNIT), 'record_start': i == 0,
                 'profile': f'8010/{value:04x}/{self.style:04x}/{self.axes}',
                 'state': f'ornament/{value:04x}/{self.style:04x}/{self.axes}'} for i in range(count)]


def source_model(source, page, variant, mode, origin, height):
    model, rows, painting = Model(variant, mode, origin, height), [], []
    def visit(at, tag, value, size):
        if tag < 0x8000:
            rows.append(model.glyph(tag, value))
            painting.append('g')
        elif tag == 0x8010:
            ornaments = model.ornaments(value, struct.unpack('<4H', read_exact(source, at + 4, 8)))
            rows.extend(ornaments); painting.extend('o' for _ in ornaments)
        elif tag in (0x800a, 0x810a):
            painting.append('i')
        elif tag in (0x8006, 0x8007, 0x8008, 0x8090):
            painting.append('v')
        else:
            model.control(source, at, tag, value)
        require(len(painting) <= 131072, 'expanded source painting bound')
    glyphs, _ = source_glyphs(source, page, variant, mode, record_visitor=visit)
    require(sum(row['kind'] == 'g' for row in rows) == len(glyphs), 'source glyph count')
    return rows, painting
