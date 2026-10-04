# caj2pdf-samples

Real-document catalog and regression inputs for [caj2pdf-rust](https://github.com/rwv/caj2pdf-rust).

## Initial collection

57 distinct documents indexed: the 56 existing samples below plus a newly
collected 238,910,818-byte HN-A document from upstream issue 111 (738 pages,
1,450 bookmarks). Its complete native, Node and browser conversions are recorded
in [the research notes](RESEARCH.md); viewer comparison remains NOT_RUN.

56 distinct real documents from the pinned upstream CAJSamples collection:
17 CAJ, 22 HN, 5 C8, 3 KDH, 2 PDF and 7 TEB. All 56 local files were checked
against their SHA-256 and byte size during initial import. Aliases are retained;
identical content is not counted twice. These are existing samples, not 56 newly
discovered documents. Format labels are imported observations, not proof that
all layouts in a family are supported.

The public catalog records provenance, hashes and locations. Upstream has not
declared document redistribution permission, so its document bytes are not
mirrored here. Code and original documentation are MIT; that license does not
relicense third-party documents. Original or explicitly MIT-licensed contributed
real documents may be stored under `samples/` after provenance review.

## Use

Obtain the upstream corpus separately at revision
`7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07`:
https://github.com/caj2pdf/CAJSamples

```sh
python3 tools/verify.py /path/to/local-corpus
```

For the additional sample, obtain the document linked from upstream issue 111
and place it at `issue-111/56.caj` beneath the local corpus root.

The verifier reads in bounded chunks, checks every catalog entry and exits
nonzero for missing or changed files. It does not execute converters or count
integrity checks as compatibility passes. Store downloads in an external cache.

## Collection priorities

1. CAA and CAS: obtain authentic files; determine whether each is a document,
   link/descriptor or container before proposing a decoder.
2. NH: obtain files with their original extension and identify their bytes;
   do not assume the extension maps one-to-one to an HN layout.
3. New CAJ/HN/C8/KDH failures: prefer a new structure or reproducible failure
   over another copy of an already represented document.

The seven TEB files share one encrypted DRM container layout (see
[research notes](RESEARCH.md)); more TEB copies add no format evidence. The
CAA/CAS/NH search log is recorded there with the remaining sample gaps.

See [research notes](RESEARCH.md) and repository issues. Public issue reports
should contain a source URL and hash, not attachments with unknown rights.

## Checks

`python3 tools/check_catalog.py` validates `catalog.json` structure (fields,
hashes, unique paths and digests, status values, formatting) without the
corpus; CI runs it on every pull request. After a catalog change merges, the
main project re-pins the new commit and catalog SHA-256 in
`scripts/sample_catalog.py`.

## Adding a sample

Record source URL/revision, original path/extension, byte size, SHA-256,
observed format, and redistribution evidence. Deduplicate by SHA-256. For a
public binary contribution, include the author's explicit MIT grant and remove
personal or confidential material before submission. Do not call a renamed or
synthetic document a real historical sample.

For a regression result, record converter commit, options/resources, status,
page count and the exact failing page/error. Viewer comparisons also need the
viewer version, fonts, rendering settings and selected pages. Missing inputs
are `NOT_RUN`; successful opening is not pixel or text equivalence. Keep raw
renders/text external unless their redistribution is established. Reuse the
main project's existing runners; no second conversion or oracle framework.
