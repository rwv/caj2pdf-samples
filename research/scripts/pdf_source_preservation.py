# SPDX-License-Identifier: MIT
"""Acquire and check external PDF-family source preservation, without conversion."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess

from pdf_source_inventory import JSON_LIMIT, digest, probe
from pdf_source_graphs import require, verify as verify_pdf
from caj_source_preservation import verify as verify_caj
from caj_reviewed_framing import frame_selected, substitution_source
from caj_reviewed_selection import REPORTS, verify as verify_reviewed
from caj_field_proofs import FIELD_SOURCES, verify as verify_fields
import caj_accounted_profiles as accounted


def reviewed_profiles(notes):
    profiles = {}
    for name, (expected_hash, key, _) in REPORTS.items():
        path = notes/name
        require(path.stat().st_size <= JSON_LIMIT and digest(path) == expected_hash,
                'reviewed source-selection report changed: '+name)
        report = json.loads(path.read_text())
        frames = report[key] if isinstance(report[key], list) else [report[key]]
        for facts in frames:
            sha = report['source']['sha256'] if key == 'independent_diagnostic_framing' else facts['source_sha256']
            require(sha not in profiles, 'duplicate reviewed source')
            profiles[sha] = path, report, key, facts
    return profiles


def build_reviewed_reference(case, directory, profile):
    path, report, key, facts = profile
    source = Path(case['source'])
    if key == 'independent_diagnostic_framing':
        transformed = directory/'reviewed-13-site-source.caj'
        substitution_source(source, transformed, report['candidate_evidence']['source_constraints'])
        source = transformed
    require(digest(source) == facts['source_sha256'], 'reviewed reference source changed')
    reference = directory/'source-body-inventory.pdf'
    framing = frame_selected(source, reference, facts)
    return reference, framing, {'file': str(path), 'sha256': digest(path), 'framing_key': key,
                               'source_sha256': facts['source_sha256'], 'selection_scope': facts['scope']}


def run(manifest, output, notes):
    require(manifest.stat().st_size <= JSON_LIMIT, 'manifest size bound')
    cases = json.loads(manifest.read_text())
    require(isinstance(cases, list) and 0 < len(cases) <= 10000, 'manifest count bound')
    identities = set()
    for case in cases:
        for key in ('source_sha256', 'pdf_sha256'):
            require(isinstance(case[key], str) and re.fullmatch(r'[0-9a-f]{64}', case[key]), 'invalid identity')
        require(case['source_sha256'] not in identities and case['format'] in ('PDF', 'KDH', 'CAJ'),
                'duplicate source or unsupported family')
        identities.add(case['source_sha256'])
        require(type(case['pages']) is int and 0 < case['pages'] <= 100000, 'declared page count bound')
        for key in ('source', 'pdf'):
            case[key] = str(Path(case[key]).resolve())
    profiles = reviewed_profiles(notes)
    accounted_profiles = accounted.profiles(notes)
    output.mkdir()
    executable = shutil.which('qpdf')
    require(executable, 'qpdf is required for an explicit acquisition')
    tool = {'path': executable, 'sha256': digest(Path(executable)),
            'version': subprocess.check_output([executable, '--version'], text=True, timeout=10).strip()}
    results = []
    for case in cases:
        result = {'source_sha256': case['source_sha256'], 'pdf_sha256': case['pdf_sha256']}
        try:
            builder = None
            if case['source_sha256'] in accounted_profiles:
                builder = lambda c, d: accounted.build_reference(c, d, accounted_profiles[c['source_sha256']])
            elif case['source_sha256'] in profiles:
                builder = lambda c, d: build_reviewed_reference(c, d, profiles[c['source_sha256']])
            row = probe(case, output, build_reference=builder)
            if row['status'] == 'NOT_CONFIRMED':
                raise ValueError(row.get('reason', 'source acquisition not confirmed'))
            if case['source_sha256'] in accounted_profiles:
                proof = accounted.verify(row, accounted_profiles[case['source_sha256']])
            elif case['source_sha256'] in FIELD_SOURCES:
                proof = verify_fields(row, notes)
            elif 'prior_proof' in row:
                proof = verify_reviewed(row)
            elif case['format'] == 'CAJ':
                proof = verify_caj(row)
            else:
                proof = verify_pdf(row)
            result.update(proof)
        except (OSError, ValueError, KeyError, TypeError, StopIteration, RecursionError,
                subprocess.SubprocessError) as error:
            result.update(status='NOT_VERIFIED', reason=str(error))
        results.append(result)
        receipt = {'schema_version': 1, 'manifest_sha256': digest(manifest), 'qpdf': tool,
                   'scope': 'Selected-object/raw-stream and navigation checks. Reader recovery completeness, unverified profiles and full visual fidelity remain separate.',
                   'attempted': len(results), 'requested': len(cases),
                   'counts': dict(Counter(item['status'] for item in results)), 'results': results}
        (output/'verification.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(case['source_sha256'][:12], result['status'], result.get('reason', ''), flush=True)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--output', type=Path, help='new external artifact directory')
    parser.add_argument('--notes', type=Path, default=Path(__file__).resolve().parents[1]/'notes')
    args = parser.parse_args()
    if args.manifest is None and args.output is None:
        print(json.dumps({'status': 'NOT_RUN', 'attempted': 0, 'reason': 'No external manifest requested'}))
        return
    if args.manifest is None or args.output is None:
        parser.error('--manifest and --output are required together')
    result = run(args.manifest.resolve(), args.output.resolve(), args.notes.resolve())
    print(json.dumps(result['counts'], sort_keys=True))
    if result['counts'].get('NOT_VERIFIED'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
