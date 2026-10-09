#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Bounded lexical observation of incomplete hexadecimal page-content operands.

This is research evidence, not a repair or a general content interpreter.
Inline images and other unclosed lexical constructs remain unmeasured.
"""
SPACE = b'\x00\t\n\x0c\r '
DELIMITERS = b'()<>[]{}/%'
HEX = b'0123456789abcdefABCDEF'
MAX_CONTENT = 1 << 20
MAX_NESTING = 256


def unfinished_hex(data):
    if not isinstance(data, bytes) or len(data) > MAX_CONTENT:
        raise ValueError('content type or byte limit')
    at, text_depth, graphics_depth = 0, 0, 0
    containers = []
    while at < len(data):
        byte = data[at]
        if byte in SPACE:
            at += 1
        elif byte == ord('%'):
            while at < len(data) and data[at] not in b'\r\n':
                at += 1
        elif byte == ord('('):
            at += 1
            depth = 1
            while at < len(data) and depth:
                byte = data[at]
                at += 1
                if byte == ord('\\'):
                    if at == len(data):
                        raise ValueError('unfinished literal escape')
                    if data[at:at + 2] == b'\r\n':
                        at += 2
                    else:
                        at += 1
                elif byte == ord('('):
                    depth += 1
                    if depth > MAX_NESTING:
                        raise ValueError('literal nesting limit')
                elif byte == ord(')'):
                    depth -= 1
            if depth:
                raise ValueError('unfinished literal string')
        elif data[at:at + 2] in (b'<<', b'>>'):
            marker = data[at:at + 2]
            if marker == b'<<':
                containers.append(marker)
                if len(containers) > MAX_NESTING:
                    raise ValueError('container nesting limit')
            elif not containers or containers.pop() != b'<<':
                raise ValueError('dictionary boundary')
            at += 2
        elif byte == ord('<'):
            start = at
            at += 1
            digits = 0
            while at < len(data) and data[at] != ord('>'):
                if data[at] in HEX:
                    digits += 1
                elif data[at] not in SPACE:
                    raise ValueError('invalid hexadecimal digit')
                at += 1
            if at == len(data):
                return {'offset': start, 'hex_digits': digits,
                        'whitespace_bytes': at - start - 1 - digits,
                        'container_depth': len(containers),
                        'text_depth': text_depth, 'graphics_depth': graphics_depth}
            at += 1
        elif byte in b'[]':
            if byte == ord('['):
                containers.append(b'[')
                if len(containers) > MAX_NESTING:
                    raise ValueError('container nesting limit')
            elif not containers or containers.pop() != b'[':
                raise ValueError('array boundary')
            at += 1
        elif byte in b')>{}':
            raise ValueError('unexpected delimiter')
        else:
            name = byte == ord('/')
            start = at
            if name:
                at += 1
            while at < len(data) and data[at] not in SPACE + DELIMITERS:
                at += 1
            word = data[start:at]
            if not name and not containers:
                if word == b'BI':
                    raise ValueError('inline image requires a separate observer')
                if word in (b'BT', b'ET'):
                    text_depth += 1 if word == b'BT' else -1
                    if text_depth not in (0, 1):
                        raise ValueError('unmeasured text nesting')
                if word in (b'q', b'Q'):
                    graphics_depth += 1 if word == b'q' else -1
                    if graphics_depth < 0:
                        raise ValueError('unmeasured graphics nesting')
                    if graphics_depth > MAX_NESTING:
                        raise ValueError('graphics nesting limit')
    if containers:
        raise ValueError('unfinished container')
    return None
