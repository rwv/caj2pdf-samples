<!-- SPDX-License-Identifier: MIT -->

# Native content checks for text-only and mixed pages

This completes the profile classification and applicable ordering checks in
[issue #12](https://github.com/rwv/caj2pdf-samples/issues/12), following the
[type-0 row-convention correction](image-order-row-convention-20261008.md).
The [receipt](native-content-order-20261008.json) preserves original results and
records 26/26 passing applicable source/PDF ordering checks. It includes the
complete text results and deliberately damaged-output controls.

Eighteen originals were bitmap orientation false alarms. Seven more failed only
on zero-image pages. The final source used the already measured [compact HN-B
index](hnb-compact-index.md); the old research reader incorrectly assumed a 20-byte
row. The reader now selects 12/20 bytes from the explicit marker at 136, refuses
unknown markers/nonzero compact reserved words, and rejects compact text that
overlaps the index. Absent compact raw fields are null, not invented source bytes.
No parser retries another index width after malformed input.

## Applicable checks and limits

The new original MIT `native_text_order.py` independently traverses the measured
record framing and maps character identities using Python's standard codecs and
the documented mode-specific controls. It compares all **60,762 semantic glyphs
on all 38 pages of eight unchanged sources**, preserving source order per page.
Unicode map intervals and Identity-H font encodings are checked before interpreting
PDF text operands. ActualText preserves semantic identity for visual substitutes;
nonsemantic Artifact decorations are excluded. HN-B terminal tails and bare end
tags follow the existing independent viewer controls; C8 retains exact termination.

The source record grammar and mappings come from [native C8 records](c8-native-records.md),
[additional controls](c8-native-controls.md), [encoded strings](c8-encoded-prefix.md),
[image-reference records](c8-image-references.md), [HN-B controls](hnb-compact-index.md)
and the prior #391 independent glyph check. No foreign converter implementation,
private HN/JBIG code, vendor glyph outlines or document text was copied.

This is a semantic identity/order check. State records are framed without claiming
to validate their geometric/resource effects. It does not prove font shape,
placement, vector fidelity or rendered-page parity. Image-bearing pages still
require the pinned independent image oracles. Zero-image pages report bitmap
NOT_APPLICABLE with a reason, and only pass the overall order check when the
separate whole-document native text check passes. A missing optional research
dependency or unmeasured text profile yields NOT_RUN, never a compatibility pass.

Per-source SHA checks bracket each run; the output PDF is also hashed before/after.
The source reader uses ranged bounded reads. Native text is capped at 1 MiB and
65,536 records per page, PDF content at 4 MiB and each Unicode map at 64 KiB.
Flate decoding checks EOF, trailing bytes and output ceilings. Metadata-only
receipts include page counts and sequence hashes; source text, extracted pixels,
fonts and derived PDFs remain external.

## Negative controls and validation

All eight complete positive sources pass. For each source, a derived PDF with
pages 1/2 exchanged fails their source-order checks; removing one semantic glyph
fails page 1; changing a Unicode mapping is refused. These **24 controls** retain
the unchanged source hash and original output hash. The received source files
and original PDFs are never rewritten.

Local original tests cover atomic drawing/image/extended payloads, variable
strings, HN-B/C8 end rules, mode-specific mappings, missing/reordered/extra glyphs,
Artifacts/ActualText, conflicting/incomplete Unicode maps, bounded Flate input,
compact index discrimination and short reads. The 31 focused tests pass.
Catalog validation and the three catalog tests are separate.

PyMuPDF 1.27.2.2 is an optional external research dependency used only to open PDF
objects; the new checker inflates bounded streams with Python zlib itself. It is
not included in the converter or its dependencies. The standard-library parser
unit tests do not require PyMuPDF. Overlay the research scripts/tests as explained
in [the research guide](../README.md), then run:

```sh
python3 scripts/native_text_order.py /external/source.caj /external/output.pdf --sha256 SOURCE_SHA256
python3 -m unittest discover -s tests/conformance -p 'test_native_text_order.py'
```

All applicable tests here are against native PDFs. Node/Chromium output parity
is recorded separately in this note's final runtime checkpoint; it is not a
new independent render oracle. The broader correctness goal remains open under
[rwv/caj2pdf-rust#406](https://github.com/rwv/caj2pdf-rust/issues/406).

## Final runtime checkpoint

All 26 unchanged originals also pass Node and Chromium using the exact #407 WASM,
with byte-identical outputs to native (page counts, lengths and SHA-256). Native-text
cases use the same NotoSerifCJK face 2 / FreeSerif configuration selected by the CLI;
font/WASM hashes and per-source results are in the receipt. Browser OPFS cleanup
passes for every case. This is cross-runtime output parity, not an additional
independent renderer. Initial probes without required fonts were configuration
refusals and were rerun with the documented fonts; they were never counted as passes.

The new 31 focused parser/integration controls also run in Catalog CI without
corpus downloads. The qpdf-dependent original PDF page-order control explicitly
skips if qpdf is unavailable; local validation ran it successfully. Optional or
skipped tests remain separate from the actual 26-source compatibility results.
