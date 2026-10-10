# Observed native font resources and legacy symbols

[Issue #106](https://github.com/rwv/caj2pdf-samples/issues/106) remains open.
The public FreeType calls recorded for **13 unchanged native originals / 77
pages** now have measured resource identities: **346,918 glyph API events**
bind to successful face constructors and their SHA-256 input hashes. This
closes the opened-resource gap for these recorded calls, not every source
character or cached draw. The catalog remains **1,408 identities: 1,361 PASS,
20 FAIL and 27 UNSUPPORTED**; no new conversion pass or product fix is claimed.

The [metadata receipt](opened-font-resources-20261009.json) retains source,
observer, library, resource and trace identities, session outcomes and explicit
limitations. Its SHA-256 is
`dd0bc48ae6217a37a2d3d122c27181300e41c515b6255433060e5ae05f89b4fa`.
External documents, derived PDFs, fonts, outlines, pixels and
viewer binaries remain outside Git. All new source is original MIT work.

## Binding calls to resources

[`ft_face_observe.c`](../cajviewer/ft_face_observe.c) forwards the public
`FT_New_Face`, `FT_New_Memory_Face`, `FT_Open_Face`, `FT_Reference_Face` and
`FT_Done_Face` APIs. It hashes successful nonnegative-index `_CNKI` face
inputs without exporting their bytes. These operations and reference counts
are documented by [FreeType](https://freetype.org/freetype2/docs/reference/ft2-face_creation.html);
hashing uses the documented [OpenSSL EVP API](https://docs.openssl.org/3.0/man3/EVP_DigestInit/).
No vendor implementation or FreeType private fields are inspected.

File inputs are streamed through a 64 KiB buffer, capped at 32 MiB, and checked
for size/mtime changes during hashing. Memory inputs are bounded and hashed
before the constructor returns to its caller. File hashes identify the
read-only resources in this pinned image. This is not a general claim that a
post-constructor hash proves historical consumption of a mutable file.
Custom streams are explicitly opaque; the observer does not call their read
callbacks. Failed opens, negative-index queries and other families are outside
the recorded scope. The observer suppresses nested constructors and records
disposal metadata before the face may be freed.

[`native_font_faces.py`](../scripts/native_font_faces.py) merges timestamped
face and glyph events, checks complete per-process counters, and tracks
reference lifetimes by process and address. It distinguishes address reuse
and same-family/different-file resources. Unknown hashes, opaque streams,
ambiguous timestamps, API errors, out-of-range GIDs, stale faces and trace-limit
markers prevent a successful binding. A family name or filename alone is
insufficient. The supplied inventory measures public face metadata and hashes
for all 84 resource files, each a single face; it does not inspect glyph shapes.

All 13 original sessions satisfy this binding check. Document calls use HGHT,
HGBZ, HGHZ, HGBX, HGB1 and HGFX resources. HGB1X is present in the separate
authored controls. Font-scanning child processes open additional resources;
an open without glyph calls is not evidence of document use. Live faces at
forced container shutdown remain reported. The 77 page observations are
STABLE in the existing sense of equal cached pixmaps, not a solution to
[Rust #441](https://github.com/rwv/caj2pdf-rust/issues/441)'s readiness problem.

## Original controls and the retained missing-size result

Six previously authored isolated controls were captured with both observers.
Their final RGB pages exactly match their earlier captures. Five Latin
controls also satisfy the previous strict five-size protocol. The HGHT control
records 5, 9, 19 and 20 ppem, with **6 ppem absent**. Its old protocol result
is **NOT_CONFIRMED**, despite agreement of the observed mapping and final
pixels. No retry or relaxation turns it into a five-size success. An initial
aggregation stopped on that strict failure; the final aggregation records it.
Resource hashing adds work, and absence of an intermediate call is a material
observation limit, not evidence that the source lacks that glyph.

The existing-model repertoire reveals 687 symbol draws in HN-B mode-0 source
`63870d12…`. Its observed resource is **HGFX_CNKI.ttf**, SHA-256
`4ef6bcbe9c48ebff552a57e0bca245554dcb4d5bb12d580b95e0babdd736036c`:
541,656 bytes, face 0, 3,206 GIDs. This resource was outside the previous
six-resource control experiment.

[`native_symbol_controls.py`](../cajviewer/native_symbol_controls.py) authors
one-symbol mode-0 pages for the **56 actual numeric contexts** in that source:
21 raw codes and 20 modeled semantic characters. It retains each measured
style, optional axes and optional `80ce/1`; `801d` and `8067` are absent.
Independent model traversal verifies one symbol per control. The committed
generator reproduces all 56 launched input hashes. It does not read source
text or font data, and no unobserved cross-product of states is inferred.

All 56 isolated controls have one consistent observed alias/GID across their
recorded sizes: **78,907 glyph API events and 279 outer render loads**. Fifty-five
record five sizes; raw `a1a3`, style `10a4`, records only 4, 7, 16 and 17 ppem.
That missing intermediate size remains explicit. All 21 raw-code mappings
agree across the actual contexts where they recur. Their 20 distinct alias/GID
pairs exactly equal the original document's observed outer HGFX cmap pair set;
this is set coverage, not an association for every cached source draw.

The data also preserves distinctions that semantic Unicode alone cannot express:
raw `a1af` and `a3a7` both have modeled U+2019, but select GIDs 671 and 374.
Raw `a1aa` and `a3ad` have modeled U+2014 and U+FF0D, but both select GID 481.
Different GIDs are not proof of different shapes, and these measurements do
not justify changing the semantic characters. Raw codes and resource context
must remain available for the subsequent shape/geometry investigation.

The isolated checker requires every observed outer render load to have its
immediately preceding outer cmap on the same thread and face, with matching
GID and size. Nested events cannot supply the association. There must be one
pair per observed size, no unmatched outer cmap, and one consistent alias/GID
across the control. This deliberately separate one-glyph protocol reports
**observed sizes**; it does not claim the previous fixed five-size coverage.
It must not be applied to arbitrary real cached text. The sole source code is
established by the original generator/model check, not by a nearest-call guess.

## Bounds, validation and reproduction

All viewer sessions use the existing immutable offline image, read-only inputs,
UID 1000, dropped capabilities, no new privileges, 2 GiB memory/swap, two CPUs,
256 PIDs and capped temporary files. Lifetime limits are 90 seconds per control
and 600 seconds per original. Each process permits 2,000 face records and
100,000 glyph records with explicit limit markers. Analysis caps each trace
at 64 MiB and the combined face/glyph counts at 10,000/100,000; measured
aggregate analysis has a 512 MiB address-space cap. No limit marker is ignored.
All **75 sessions / 139 page observations** finish with unchanged sources and
removed containers; the two original and six symbol process groups exit zero.
The final analysis records `/proc` VmHWM 52,480 KiB and VmPeak 65,436 KiB.
Its `getrusage` high-water value is anomalously 2,452,676 KiB, as in the earlier
original-only analysis. Both raw readings are retained; their origin is
unresolved, and they are not treated as evidence of bounded peak RSS.

Original same-family geometric fonts test file, memory, public Open_Face and
opaque-stream inputs, reference lifetimes, bitmap/advance preservation and
the actual event cap. Synthetic traces exercise multiple processes, address
reuse, missing events, invalid resources, errors, ambiguous ordering and
isolated-code probe/extra-glyph rejection. Eight new tests and the relevant
existing checks run without corpus or viewer downloads: **36 tests pass,
zero skipped**. The CI dependency
addition is `libssl-dev` for this research observer, not a product dependency.
OpenSSL and FreeType remain external research libraries; neither their source
nor binary is added. The interposer, lifetime parser, symbol generator and
tests are independently authored MIT source using public API contracts and
this project's existing MIT framing/model code. No differently licensed
converter code, vendor implementation or private HN/JBIG module was consulted,
copied or translated. These new observations supplement the historical
[provenance archive](provenance-archive.md); they do not relabel font data MIT.

With permitted external resources and the existing Qt observer:

```sh
gcc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Werror \
  $(pkg-config --cflags freetype2 openssl) \
  research/cajviewer/ft_face_observe.c research/cajviewer/ft_glyph_observe.c \
  -ldl -lcrypto -o /external/observe.so
python3 research/cajviewer/native_symbol_controls.py /external/profiles.json \
  /external/new-symbol-controls
python3 research/cajviewer/native_page_capture.py \
  /external/new-symbol-controls/cases-0.json /external/new-capture \
  --observer /external/qpaint-observe.so --font-observer /external/observe.so \
  --lifetime-seconds 90 \
  --image sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de
python3 research/scripts/native_font_faces.py /external/session/ft-faces.tsv \
  /external/session/ft-events.tsv /external/resources.json --isolated-glyph
```

Extract `symbol_profiles` and `resource_inventory` from the receipt for the
two JSON manifests. Run all six generated case manifests into distinct new
directories. Omit `--isolated-glyph` for original documents. The tool neither
downloads nor distributes external fonts.

The issue's bounded protocol and resource-inventory criteria advance within
these explicit scopes. Full repertoire/state mapping, repeated-text cache
coverage, original glyph shapes, font/PDF geometry, semantic preservation and
ornaments remain unverified. Equality of GIDs or aggregate sets is not shape
or per-draw identity. No font license grant follows from metadata or public
availability. No converter defect is demonstrated by these observations;
[Rust #475](https://github.com/rwv/caj2pdf-rust/issues/475) remains research-only.
There is no native/CLI/JS API, PDF output, format support or release change.
