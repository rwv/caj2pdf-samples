# TTKN payload and offline viewer boundary, 2026-10-08

Follow-up to [Rust #415](https://github.com/rwv/caj2pdf-rust/issues/415) and the
[16-original wrapper inventory](ttkn-wrapper-inventory-20261008.md).
All 16 originals now have readable offline viewer observations. Removing
handler selection does not recover their PDF contents. None becomes a
conversion pass or a proved unavoidable exception. The actual wrapper,
credential requirements and recovery outcome remain unresolved.

The [metadata receipt](ttkn-payload-boundary-20261008.json) contains all 16
source identities, per-source stream counts and warnings, diagnostic hashes,
21 viewer sessions and retained failed attempts. Original source URLs are
pinned in the earlier inventory. Document, XML, credential, font and pixel
bytes remain external.

## Bounded payload diagnostic

The original MIT [probe](../scripts/ttkn_payload_boundary.py) verifies each
source hash, copies its logical PDF prefix sequentially, and changes the final
trailer key `/Encrypt` to `/Xncrypt`. This changes exactly one byte, omits the
non-PDF wrapper and preserves every object/xref offset. An independent complete
prefix comparison verifies the one-byte difference for all 16 copies. Source
hashes remain unchanged. This is an intentionally modified diagnostic copy,
not decryption or converter output.

The tool accepts only the measured classic-xref, single-trailer profile, with
no `/Prev` or `/XRefStm`. Bounds are 512 MiB per source, 64 KiB copy/tail
buffers, a 4 KiB trailer, 100,000 objects and 16 MiB per raw stream and decoded
Flate output. The parent has a 1 GiB address-space limit. Each qpdf child has
1 GiB address space, 40 CPU seconds, 50 wall seconds and an 8 MiB log cap.
pikepdf 10.5.1 reads raw streams; the standard-library zlib decoder separately
tests only a single `/FlateDecode` filter. Other filters and unfiltered bytes
are explicitly NOT_CHECKED. This Unix research utility is not a production
conversion API or a JavaScript dependency.

| Measured result | Count |
| --- | ---: |
| Diagnostic PDFs with qpdf exit 2 | 16 of 16 |
| Raw streams inventoried | 16,863 |
| Single-Flate streams rejected as invalid zlib | 11,162 |
| Other/unfiltered streams NOT_CHECKED | 5,701 |
| Page entries in the object graph, not decoded pages | 2,647 |
| Retained parser warnings | 17 |

The unchecked streams comprise 4,647 unfiltered, 407 DCT, 353 JBIG2, 292 CCITT
and two JPX streams. All 16,863 raw lengths are divisible by 16. That is
compatible with block-aligned data, but does not identify encryption mode,
padding, keys or derivation. No stream successfully decoded in the measured
Flate subset. This rules out treating these unchanged stream bytes as ordinary
zlib data after merely dropping handler selection.

Each diagnostic retains a duplicate `/MediaBox` warning in object 1. Source
`64d3145cba37` also has an unknown token treated as a string in object 735 at
offset 2,623,388. These warnings remain unresolved; the parser's object/page
inventory is not a clean-PDF or content-correctness assertion. The JSON retains
all warning text with local directory names removed. The full external
per-stream receipt is pinned by file hash; each public source row also pins
its stream array using SHA-256 of sorted-key compact JSON.

Production behavior is unchanged: the reviewed #457 build refuses all 16
originals with `AMBIGUOUS_PDF_REPAIR` for bytes after the PDF EOF. The earlier
logical-prefix probe reaches the unsupported TTKN encryption filter. Neither
diagnostic is a successful original conversion.

## Readable offline viewer observations

A read-only Noto Sans CJK font mount makes the previously unreadable error
text visible. All 16 unchanged originals were opened under `.pdf` filenames;
three were also opened under `.caj`. A single derived unencrypted 78-page PDF
was opened under both extensions as a control. These are 21 fresh sessions,
not 21 original identities or conversion passes.

| Original outcome | Distinct originals |
| --- | ---: |
| “Error connecting to the validation server.” | 11 |
| “Unknown error Code=%d” with literal placeholder | 5 |

The two server-wrapper originals both show the connection error. The 14
certificate/PFX originals split nine connection errors and five unknown
errors. All three paired extensions have the same outcome. The positive
control visibly opens at page 1/78 and 48% zoom in both sessions. Inherited
page/zoom request fields in launch metadata were unused: this probe performs
no page navigation or zoom action.

The pinned viewer image, font hash and container limits are in the receipt:
network disabled, read-only root and input, unprivileged user, capabilities
dropped, 2 GiB memory/swap, two CPUs, 256 PIDs and a 90-second hard lifetime.
Captures have actual monotonic elapsed times. Every final 20/25-second pair
has identical RGB bytes. All six distinct final full-frame groups were
visually inspected; remaining frames match those groups byte for byte.
Sources remain intact, no OOM occurred and all containers were removed.

These are observed messages, not proof that connectivity or credentials alone
would make a document readable. The five unknown errors have no established
cause. No endpoint was contacted or credential supplied. Stable frame pairs
do not resolve [#441](https://github.com/rwv/caj2pdf-rust/issues/441), establish
general viewer readiness, or provide whole-document fidelity evidence.

## Controls, retained failures and provenance

Five original MIT [test groups](../conformance/test_ttkn_payload_boundary.py)
cover an authored plaintext PDF with a decorative handler, a known AES control
that decrypts to the authored content before the diagnostic, opaque/unfiltered
streams, zlib completion/limit/trailing-data boundaries and source/extent/
existing-output/trailer guards. No corpus or foreign implementation bytes are
used. The known AES control does not establish TTKN's encryption semantics.
CI runs the controls with the already pinned pikepdf research dependency.

The catalog check and all 57 synthetic tests selected by the Catalog workflow
pass locally, without skips. An additional broad archive discovery fails:
these archived harnesses require the historical Rust directory layout, as
documented in the [research README](../README.md#running-the-python-harnesses).
A controlled comparison against unchanged head `9b4e708` has exactly the same
26 failing and 51 erroring test identifiers on both trees (569 versus 574
tests, including the five new passing groups). The receipt also retains the
first broad invocation's counts. These failed archive invocations are not
passing validation or corpus compatibility evidence.

The first exploratory three-source probe incorrectly conflated unsupported
image-filter decoders with content failure, and raw unfiltered reads with
successful decoding. Those counters are not ciphertext/plaintext evidence.
The first bounded run stopped on an unlisted CCITT filter in the second input;
it remains a failed attempt. CCITT was added only as NOT_CHECKED with an
original control. The second complete run was superseded by a third complete
run to retain warning strings. The final run exited zero as a measurement;
all 16 qpdf checks still exited two. No failed attempt is relabeled a pass.

Reproduce with the earlier inventory and external originals:

```sh
python3 research/scripts/ttkn_payload_boundary.py \
  /external/ttkn-inventory.json /external/documents /external/new-diagnostics
python3 -m unittest discover -s research/conformance \
  -p 'test_ttkn_payload_boundary.py' -v
```

Only data/behavioral evidence and original glue/fixtures were used. No foreign
converter, vendor implementation or private HN/JBIG source was read or copied.
pikepdf/qpdf and zlib are black-box research tools; no production dependency,
API, format-support, output or release change occurs. #415's inventory
criterion remains satisfied; criteria 2–4 remain unmet. The parent #406
correctness work and full-corpus status totals are unchanged.
