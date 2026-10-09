# SPDX-License-Identifier: MIT
"""Complete source-body proofs and individually justified missing destinations."""
from decimal import Decimal
import json
from pathlib import Path

from pdf_source_inventory import JSON_LIMIT, digest, value_hash
from pdf_source_graphs import require
from caj_source_navigation import source_navigation
from caj_source_preservation import acquired_objects, check_objects
from caj_reviewed_framing import frame_selected
from caj_reviewed_selection import check_selection
from caj_source_accounting import Ref, account_source, source_layout, source_references
from caj_field_proofs import replace_expected

PLAN = 'caj-source-accounting-plan-20261009.json'
PLAN_SHA256 = '303571123c8b38afa0107d5f66d88a7b7962df23f8d296b242c3e79161af1709'
ANNOTATIONS = {
    '2508ca0e325bb7019948c08dc7b6849468306e85b9b3c5fa98e35ecd61f7a600': [224],
    '52c98a3112c7b80f1ea1361a2366903acf2311026a762b519491ec25e0612e51': [153],
    '964975c2d3269787be46de97ee0e574414d0e937de8a4190a923be0d02635c01': [212, 215, 216],
    'fc8a5c20626b3492aad9afae62709019f2038a8a4c669bc7c94ae653837b0cba': [85],
}


def profiles(notes):
    path = notes/PLAN
    require(path.stat().st_size <= JSON_LIMIT and digest(path) == PLAN_SHA256, 'accounting plan changed')
    cases = json.loads(path.read_text())['profiles']
    return {case['source_sha256']: case for case in cases}


def build_reference(case, directory, profile):
    require(case['source_sha256'] == digest(Path(case['source'])) == profile['source_sha256']
            and case['pdf_sha256'] == profile['pdf_sha256'] and case['pages'] == profile['pages'],
            'accounted source/output/profile identity changed')
    reference = directory/'source-body-inventory.pdf'
    framing = frame_selected(Path(case['source']), reference, profile['selection'])
    return reference, framing, {'file': PLAN, 'sha256': PLAN_SHA256,
                               'scope': 'Unverified source-only offset plan; complete body accounting is required.'}


def missing_destinations(values, pages, annotations):
    """Prove absent target definitions and exclusive consumers from raw syntax."""
    incoming = {}
    for owner, value in values.items():
        for target, path in source_references(value):
            incoming.setdefault(target, []).append((owner, path))
    repairs, arrays = {}, {}
    for number in annotations:
        value = values[number]
        require(isinstance(value, dict) and value.get('/Subtype') == '/Link'
                and value.get('/BS') == {'/W': Decimal(0)}
                and isinstance(value['/BS']['/W'], Decimal)
                and isinstance(value.get('/F'), Decimal) and value['/F'] == 4
                and value.get('/Type', '/Annot') == '/Annot'
                and set(value) <= {'/BS', '/Dest', '/F', '/P', '/Rect', '/Subtype', '/Type', '/StructParent'},
                'unmeasured Link destination role/appearance/action')
        target = value.get('/Dest')
        indirect = target.number if isinstance(target, Ref) else None
        destination = values.get(indirect) if indirect is not None else target
        require(isinstance(destination, list) and len(destination) == 5 and destination[1] == '/XYZ'
                and isinstance(destination[0], Ref)
                and all(isinstance(x, Decimal) and x.is_finite() for x in destination[2:]),
                'unmeasured missing XYZ destination')
        missing = destination[0].number
        require(missing not in values and missing not in pages, 'destination target is defined or in page table')
        # qpdf preserves the numbers but serializes the undefined target as
        # null. This is checked against raw syntax, never accepted as absence.
        reader_array = [None, '/XYZ'] + [int(x) if x.as_tuple().exponent == 0 else x for x in destination[2:]]
        repairs[number] = {'missing_target': missing, 'array_object': indirect, 'reader_array': reader_array}
        if indirect is not None:
            arrays.setdefault(indirect, []).append(number)
    for number, owners in arrays.items():
        require(sorted(incoming.get(number, [])) == sorted((owner, ('/Dest',)) for owner in owners),
                'indirect destination array has an unproved consumer/role')
    return repairs


def verify(row, profile):
    require(row['source_sha256'] == profile['source_sha256'] and row['pdf_sha256'] == profile['pdf_sha256'],
            'accounted proof pair changed')
    source_path = Path(row['source'])
    source, candidate, left, right = acquired_objects(row)
    require(row['source_reader']['exit'] == 0, 'accounted inventory has unresolved reader warnings')
    facts = profile['selection']
    check_selection(source_path, Path(row['inventory_directory'])/'source-body-inventory.pdf',
                    row['reference_framing'], facts, left)
    values, accounting = account_source(source_path, facts, left)
    _, pages = source_layout(source_path)
    require(len(pages) == profile['pages'], 'accounted source page count changed')
    repairs = missing_destinations(values, pages, ANNOTATIONS.get(row['source_sha256'], []))
    normalized, expected, events = dict(source), dict(left), []
    for number, repair in repairs.items():
        key = f'obj:{number} 0 R'
        value = source[key]['value']
        indirect = repair['array_object']
        dest = f'{indirect} 0 R' if indirect is not None else repair['reader_array']
        require(value_hash(value.get('/Dest')) == value_hash(dest), 'source reader destination differs from raw proof')
        replacement = {k: v for k, v in value.items() if k != '/Dest'}
        replace_expected(normalized, expected, key, replacement, events, 'complete-source absent Link target')
        if indirect is not None:
            array_key = f'obj:{indirect} 0 R'
            require(value_hash(source[array_key]['value']) == value_hash(repair['reader_array']),
                    'source reader indirect destination differs from raw proof')
            replace_expected(normalized, expected, array_key, None, events, 'unused destination array with exclusive removed Link consumers')
    result = check_objects(normalized, candidate, expected, right, source_navigation(source_path))
    return {**result, 'status': 'VERIFIED_WITH_COMPLETE_SOURCE_ACCOUNTING', 'accounting': accounting,
            'field_changes': events, 'missing_destinations': {str(n): {k: v for k, v in r.items() if k != 'reader_array'}
                                                            for n, r in repairs.items()},
            'selection_plan': PLAN, 'selection_plan_sha256': PLAN_SHA256,
            'scope': 'Complete source-body selected values/opaque stream extents, identical duplicates/proper prefixes, tightly proved partial headers, navigation and individually absent Link destinations. Original viewer geometry and full visual fidelity remain unproved.'}
