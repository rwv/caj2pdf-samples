<!-- SPDX-License-Identifier: MIT -->

# Complete accepted native-glyph coverage

Closes [samples #19](https://github.com/rwv/caj2pdf-samples/issues/19), part of
[rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). All ten native-text
originals in the accepted corpus now pass the independent source/PDF checker:
**60 pages, 50 with native glyphs, and 83,432 glyph identities in source order**.
The [receipt](native-content-completion-20261008.json) pins every input/output,
per-page glyph counts/order hashes and deliberate corruption checks.

The earlier eight-original checkpoint remains unchanged. The additional
12-page HN-B source contributes 20,693 glyphs; the ten-page mixed C8 source
contributes 1,977 glyphs on page 10. Both already converted and had exact
native/Node/Chromium byte parity. This follow-up fixes verification coverage;
it does not change the converter or its accepted-input count.

The checker now applies two already documented independent
[viewer measurements](c8-additional-profiles.md): terminal-only `e000` in a
length-delimited encoded string, and optional four-byte zero padding after an
aligned image-reference name. Embedded NULs, unknown words and invalid padding
remain rejected. Original tests exercise following-glyph framing and neighboring
invalid inputs. No foreign converter implementation is used.

All 30 deliberate glyph-affecting controls across the ten originals are
recognized: page swaps with distinct glyph sequences, glyph omissions and
Unicode-map corruption. For the mixed C8 input, swapping image-only pages 1
and 2 correctly leaves its empty native-glyph sequences unchanged; this is
retained as a scope limit, not reported as a detected glyph corruption. The
separate image-order checker detects that swap on both pages using all 17
source image descriptors. The glyph-affecting swap exchanges pages 1 and 10.

These checks do not prove placement, font outlines, vectors, full rendered-page
fidelity or source bookmarks. Ten empty native-glyph pages still require their
separate image evidence. Original source/PDF hashes remain intact. External
sources, derived PDFs, fonts and pixels stay outside Git; metadata and original
MIT controls only. No release is published, and #406 remains open.
