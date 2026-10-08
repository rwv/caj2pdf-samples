# CAA descriptors and an original-extension NH document

This resolves the new evidence in [#27](https://github.com/rwv/caj2pdf-samples/issues/27)
and supports [caj2pdf-rust#424](https://github.com/rwv/caj2pdf-rust/issues/424).
The [metadata receipt](caa-nh-discovery-20261008.json) and `external/formats/`
catalog rows record identities and pinned public source locations. Document,
descriptor, PDF and screenshot bytes remain external; redistribution is not
established. No vendor, Python/Go converter or private implementation was read
or copied for this investigation. Original notes and controls are MIT.

## Discovery and identity

GitHub code search `extension:caa` returned 34 indexed paths. Checking the
Chinese document paths yielded 21 downloads, 18 distinct SHA-256 identities,
across five repositories. Tree inspection of those repositories found
`DodgeV/energy-blockchain/data/中国能源统计年鉴1989.nh` at revision
`888c8690c20e7ce9caf0292c658f8362bc768ce4`. All 19 hashes are absent from the
1,277-entry catalog at `ae17dff5ce287fa37acbcfe189ad0ccf1ecf62c8`.

CAA acquisition was capped at 64 KiB per file; the NH download was streamed
in 256 KiB chunks with a 32 MiB cap. Sizes and complete SHA-256 hashes were
verified. Repository paths establish the hosted extension, not an authenticated
chain back to the vendor. Search results are not an exhaustive format inventory.

Upstream caj2pdf issue 29 is an excluded lead: its `HN_and_PDF.zip` contains a
`.caj` HN-A member already in the catalog, despite the issue's NH wording.
The PDF comparison member is not added as a new format sample.

## Observed CAA profile

All 18 files are ASCII text, 350–404 bytes, with this field order:

```text
[TARGET]
A1=...
A2=...
B1=0
B2=
C1=0
C2=
D1=...
D2=...
DOCTYPE=...
```

`A1` and `D1` contain decimal digits. `A2` and `D2` contain nonempty strings
using the Base64 alphabet; this observation neither decodes them nor assigns
semantics to their values or counts. Sixteen files declare `NH`, two `KDH`.
Both LF and CRLF occur. One file has additional trailing blank lines and a
space. No page records or embedded document payload were established.

The supported recognition profile should require the complete ordered fields,
the observed empty B/C pairs and NH/KDH type, within the existing 1 KiB probe.
Arbitrary `[TARGET]` INI files and partial fields are insufficient evidence.
Do not log, decode or resolve opaque A2/D2 values. Recognition is distinct from
conversion: callers need the actual document before offline conversion can run.
Other CAA profiles and historical link resolution remain unverified.

## Offline CAJViewer observations

Linux CAJViewer 9.0.0.24093 ran from the existing image
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`
(installer identity and setup: [viewer setup](../cajviewer/SETUP.md)). Containers
used `--network none`, a read-only root, dropped capabilities, 1 GiB memory,
256 PIDs, temporary home/runtime directories, read-only input/fonts and an
external capture directory. Xvfb/Openbox displayed the official `start.sh`
launcher; screenshots were taken after eight seconds. No link target was fetched.

The representative `03419f6f…` (NH) and `8b6ac101…` (KDH) descriptors both
produced the dialog "Unrecognized file type". In the same environment the
project's original `valid_out_of_order_objects.pdf` opened with two pages and
its two outline entries. These observations establish an offline refusal by
this viewer version, **not** successful link handling, a network requirement,
or behavior of historical Windows viewers. The initial missing-CJK-font run
is excluded; the recorded captures mount host fonts and show readable dialogs.

## NH conversion

The 8,527,548-byte NH sample has SHA-256
`16b1a3b1cb7177cc3d327f749f7f273d806b153ded5fe11d9261bac030ec66ac`.
Its first eight bytes are `48 4e 00 00 90 01 00 00`: existing HN-A. It has
433 pages and 365 bookmarks; no new NH signature or parser is needed.

The published v0.4.0 CLI fails on page 4 at source byte 246762 with text-region
flags `0x800c`. Current main `b02a6ece1e7e6c7c2c49c3abfa2ad72b5f8a7565`
already handles this profile. Complete CLI, Node and real Chromium conversions
with default bookmarks and no fonts produce the same 24,592,732-byte PDF:
`b12385a8a53a811ac245dd6f65b410a5c1b1be526292b42e94594a6b75c4add3`.
All three pass `qpdf --check` without warnings; Poppler reports 433 pages and
MuPDF lists 365 outlines. Node uses a seekable file path and sequential file
sink; Chromium uses a real local File and sequential OPFS writable stream.
No skipped optional test is counted. Source-viewer pixel comparison is NOT_RUN;
byte-identical output and structural validity do not prove visual fidelity.

## CAS gap

The vendor-authored [June 2002 KNS3.5 manual](https://staatsbibliothek-berlin.de/fileadmin/user_upload/zentrale_Seiten/ostasienabteilung/pdf/UserGuide35.pdf)
lists CAS, but no CNKI CAS bytes were authenticated. Web and GitHub searches
and their unrelated hits are preserved in the receipt. The gap remains open in
[#28](https://github.com/rwv/caj2pdf-samples/issues/28); it does not justify
recognizing a guessed `CAS` signature or advertising a decoder.
