<!-- SPDX-License-Identifier: MIT -->

# Expanded C8/HN-B outline inventory

Follow-up to [Rust #303](https://github.com/rwv/caj2pdf-rust/issues/303) and
[sample collection #5](https://github.com/rwv/caj2pdf-samples/issues/5), under
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). The
[per-source receipt](hnc8-outline-inventory-20261008.json) expands the structural
inventory to **845 C8 and four HN-B originals, 2,855 pages**. No positive
C8/HN-B stored-outline example is established. Unknown outline metadata and
the converter's omission warning remain unchanged; #303 stays open.

## Corrected historical example

The earlier #303 body incorrectly called `issue-90/5-[4].caj` a 132-page
HN-B document without contents. Its unchanged SHA-256 is
`1373e97a8598258c5ee9f8a2191f9efa189c5d62d5b663cfa6ec4aa7f7418735`.
Independent header reads show HN-A marker 400, 132 pages at `0x90` and
81 bookmarks at `0x158`; fresh CLI inspection agrees. A fresh original-viewer
session visibly shows populated nested contents. This file was already
correctly classified as HN-A in the catalog and is excluded from the 849.

Its prior reviewed native output passed the source-outline comparison.
That existing check is pinned separately; this follow-up did not enumerate
all viewer titles or navigate all destinations. The auxiliary 45-page,
42-bookmark HN-A positive control from the earlier university-source search
also displays populated contents. It is outside the frozen 1,297-input
conversion ledger and is not counted as a new corpus conversion pass.

## What the expanded bytes establish

The original MIT [inventory script](../scripts/hnc8_outline_inventory.py)
hashes each source before and after reading. It uses the measured C8 page
index at `0x50` and HN-B index at `0xd8`, with the established 12/20-byte
HN-B row distinction. In all 849 inputs, the first text starts immediately
after the page index. There is no intervening HN-A-style outline table in
that span. This does not exclude an unknown layout elsewhere in the file.

Of the C8 files, 770 have 1–6 pages, 31 have 7–12, 38 have 13–50 and six
have more than 50 pages; the maximum is 118. The four HN-B files have
12, four, four and six pages. Consequently the earlier short-article sample
description must not be applied to this expanded corpus.

There are **844 inputs without the exact final `APPINFOSIGN` marker** and
five with a completely framed zlib/XML package. All five decode within the
1 MiB bound and contain only the measured Link/UrlLink structural types:
1, 3, 23, 35 and 75 pairs, respectively. No outline-named element or attribute
is observed in those packages. Searching structural names cannot prove
that another representation contains no outline. XML text, link values,
authors and other attribute values are not exported.

## Selected original-viewer observations

Fresh isolated CAJViewer 9.0 Linux sessions show an empty **contents** panel
for four C8 originals with 53, 118, 78 and 73 pages. The two HN-A controls
show populated panels. The receipt records each source identity, expected
and visible page count, selected-tab observation and capture hashes. All
six final full frames were visually inspected; the last two RGB frames in
each session agree. Other originals' viewer panels were not checked here.

The viewer image is pinned by SHA-256. Each session has networking disabled,
a read-only root and source, UID 1000, dropped capabilities, no new privileges,
2 GiB memory/swap, two CPUs, 256 PIDs and a 90-second hard lifetime.
Xvfb is 1600 × 1200 at 96 DPI, with a hash-pinned read-only CJK UI font.
Source hashes remain unchanged; no OOM occurs and every container is removed.
Stable captures do not settle the general readiness issue #441 or establish
whole-document visual fidelity.

The initial unmaximized C8-53 capture selected the annotations tab. It is
retained as an unsuccessful contents observation, not relabeled as evidence.
The corrected sessions maximize the window and explicitly verify the
contents tab. The initial HN-A control did display populated contents.

## Reproduction and limits

Use Python 3.11+ and a manifest array of `source_sha256`, `source_id`,
`variant` and `pages`, with external originals named `SHA256.caj`:

```sh
python3 research/scripts/hnc8_outline_inventory.py manifest.json /external/documents /external/new-receipt.json
python3 -m unittest discover -s research/conformance -p 'test_hnc8_outline_inventory.py' -v
```

The receipt's structural rows contain the manifest fields. The script
requires an exact terminal marker, bounded offsets and encoded/decoded
lengths, one complete zlib frame, UTF-8 XML without NUL/DTD/entity declarations,
and at most 100,000 XML nodes. An unmeasured boundary is `UNRESOLVED` and
causes a nonzero exit. The fixed header and final 64 bytes are ranged reads;
hashing streams the source. These are read-only research checks, not a
production outline parser.

Seven original synthetic control groups cover both HN-B index widths,
HN-A rejection, source identity, bounds, framing, encoding, malformed XML,
nonfinal markers, concatenated zlib frames, and deliberate outline-named
structure without manufacturing extracted bookmarks. CI runs these controls
without downloading documents. No foreign converter, private HN/JBIG or
vendor implementation was inspected or copied. Documents, XML, screenshots
and fonts stay external. No API, support, dependency or release change follows.
