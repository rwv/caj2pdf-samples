# Native caller-font subset audit

[Issue #57](https://github.com/rwv/caj2pdf-samples/issues/57) checks the remaining
normal-font subset gap from [#51](https://github.com/rwv/caj2pdf-samples/issues/51).
All ten unchanged native originals, **60 pages and 83,644 glyph draws**, match
the pinned caller fonts in used CID mapping, unhinted outlines, embedded font
advances and PDF widths. This is **not original-viewer font or raster fidelity**.
No converter defect or additional conversion pass is established.

The [per-page receipt](native-font-subsets-20261009.json) has SHA-256
`550878e3a3f9de20fa0b163f80400fc9e6a6d47c6686ef15ea58bc822b6bd205`.
It retains every source/PDF hash, caller font/face identity, checker dependency
hash, process measurement and failed local validation attempt. These are the
unchanged normal PDFs from production implementation
`5f3cf7fb08297ddadfb1cff05e8dcdfe17c037dc`, CLI SHA-256
`d213898ee16a32f0d5304dc96438ffde2402d8135af3b0728a764c1ae8ea41a0`.
The later TEB diagnostic change does not alter these supported outputs.

| Source SHA-256 prefix | Pages | Used resource/CID pairs |
| --- | ---: | ---: |
| `03770ea1cdeb` | 5 | 462 |
| `166d00147923` | 12 | 878 |
| `1b9aa912e0bc` | 4 | 428 |
| `3f3b9b57d692` | 4 | 696 |
| `63870d12f206` | 4 | 583 |
| `7e3f2c0faebb` | 10 | 319 |
| `90e7b47716c3` | 6 | 519 |
| `b9a64bf99e4b` | 4 | 694 |
| `d6a23a9cfd0f` | 5 | 762 |
| `e1b17805a87f` | 6 | 799 |

## What is checked

[`native_font_subsets.py`](../scripts/native_font_subsets.py) reuses the bounded
source record model and PDF content visitor from the
[glyph-model audit](native-glyph-model-20261009.md). Expected roles follow those
published controls and the documented native API's default fallback; original
MIT Rust was consulted. This is not independent discovery of source font roles.
The measured baseline supplies only CJK and Latin fonts; optional roles are
absent. Each glyph selects the requested available resource, then the documented
character-class fallback when necessary.

The external caller resources are NotoSerifCJKsc-Regular, TTC face 2, SHA-256
`5d9c31a059600193c9d7968a998bde886ccdc77e934006ad243b41794c496a7d`,
and FreeSerif, SHA-256
`c1dd2270ff624d66a7f1cd23075b5ce05a662f560be06a70a9599065ce008355`.
Their licenses remain SIL OFL 1.1 and GPL-3+ with Special Font Exception,
respectively. They are external resources, not project MIT source or inferred
CAJViewer fonts. No font files or outlines are redistributed here.

For every painted CID, the checker resolves the actual TrueType CID-to-GID map
or CFF CID charset. fontTools decodes both the selected caller glyph and the
embedded glyph independently of the Rust subsetter. Composite glyphs are
decomposed; normalized path operations must match exactly. No visual tolerance,
registration or fitted correction is used. Advances from the actual embedded
program must equal the caller's advance. PDF widths use the existing `1/20000`
serialization tolerance, not a threshold derived from these samples. CFF matrix
profiles are checked explicitly. PDF resource names are not identity evidence.

All **6,140 resource/CID pairs**, in ten CFF and ten TrueType programs, pass.
They supply 65,996 CJK-resource draws and 17,648 Latin-resource draws. The total
includes 83,432 ordinary glyphs and 212 nonsemantic ornament marks. One existing
E6C7 private-use glyph still displays the U+0403 approximation with the original
code in ActualText. The ornaments still use the U+25BA alias. Successful subset
verification does not make either alias source-faithful.

Equivalent used shapes/advances cannot distinguish otherwise different font
resources. Hint programs, every font metadata field and rasterizer behavior are
outside this check. No CAJViewer font program/outline or implementation was
inspected. The separate source-viewer cold disagreement remains under
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441).

## Controls, bounds and reproduction

Six original MIT control groups include complete independently authored
source/PDF pairs, generated TrueType and CID-keyed CFF fonts, decoration and the
public CLI. Deliberate resource, CID, character, outline, advance and PDF-width
changes fail. Changed CFF matrices, missing CIDs, partial/overlapping width
ranges, mismatched input hashes, excessive path commands and recursive glyph
components are refused. No external corpus or font is required by these tests.
All **115 selected Catalog tests pass, zero skipped**. Initial driver quoting
and missing-host-SciPy failures are retained in the receipt; neither is counted
as a pass. The corrected full suite uses the existing pinned dependencies.

Source and PDF processing remain per page using the existing bounded visitors.
Caller fonts are at most 64 MiB each, subsets 4 MiB, used font resources 64 per
document, and CID/width domains 65,536. Glyph paths allow at most 16,384 commands
and points, with component recursion capped at 16. CFF font dictionaries are
capped at 256. Hashes are checked before and after each document. The measured
one-process run had a 2 GiB address-space cap, VmHWM 230,576 KiB and VmPeak
292,868 KiB; all ten pairs took 35.51 seconds. These are research-process limits,
not new converter memory claims. Use a process time/address-space cap when
examining untrusted inputs; the tool does not replace a process sandbox.

The tool reuses pikepdf 10.5.1, PyMuPDF 1.27.2.2 and fontTools 4.62.1. Supply a
small external JSON object with exactly `cjk` and `latin`, each containing
`path`, `face` (`-1` for a standalone font) and `sha256`. In a bounded research
process, run:

```sh
python3 research/scripts/native_font_subsets.py /external/source.caj \
  /external/reviewed.pdf /external/caller-fonts.json \
  --source-sha256 SOURCE_SHA256 --pdf-sha256 PDF_SHA256
```

The original tool uses documented [fontTools font loading](https://fonttools.readthedocs.io/en/latest/ttLib/ttFont.html)
and [recording-pen APIs](https://fonttools.readthedocs.io/en/latest/pens/recordingPen.html).
No external implementation is copied or translated. No production dependency,
API, conversion behavior, PDF output or release changes. This closes the scoped
caller-subset audit only: #51 and Rust #406 remain open for original fonts,
ornament appearance, full rendering, unknown outlines and recovery boundaries.
Corpus totals remain **1,252 PASS / 18 FAIL / 27 UNSUPPORTED**.
