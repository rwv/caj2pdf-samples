# Indexed nested empty Form, 2026-10-08

[Rust #446](https://github.com/rwv/caj2pdf-rust/issues/446) and
[PR #447](https://github.com/rwv/caj2pdf-rust/pull/447) recover the remaining
66-page KDH by preserving indexed object identity. The
[metadata receipt](indexed-empty-form-20261008.json) contains the independent
xref/header/tail inventory, reference paths, diagnostics, all-page comparisons,
scoped original-viewer controls, runtime checks and native regression.
Parent [#406](https://github.com/rwv/caj2pdf-rust/issues/406) remains open.

Reviewed production head: `ce4ba751aa6088745a2311f8055c3f7e4e04cfb7`, based on
merged `df089aa0cc258974f1997a7c467d962393794c30` (#445). A clean locked rebuild
of that head reproduces both frozen binaries used by the external checks.
No release or external document bytes are included.

## Source and indexed identity

[ldp-1/caj2pdf-actions/file.caj](https://github.com/ldp-1/caj2pdf-actions/blob/81b21b895fd6082852a4868e4237b6e6cdd48484/file.caj)
has SHA-256 `ece0be828c95350ed2d48c83fb8a5255f13c935d91da5c7c99448ffec99287a9`,
4,719,676 bytes, 66 pages and no outlines. Applying the project's original
MIT wrapper observations independently yields a 4,719,411-byte PDF, SHA-256
`df77c36c2bc750d60c48b73579231f60a0a94fb65d1a974868549ee0c7db7372`.
Eleven trailing KDH bytes follow its complete PDF EOF. The xrefs select
**960 objects and 305 streams**; every stream has a direct Length.

Only object **485** fails the declared stream-tail check. It starts at decoded
offset **786401**, with a 129-byte header declaring an empty Form. Its data
starts at **786530** with a complete 110-byte empty-Form header labeled **754**.
Both complete endstream/endobj tails follow, ending the outer frame at
**786677**. The 276-byte frame has SHA-256
`f39ccae86cf0ea764a75756fa4dd210defa4813650b85acfc5a1c1fadd66bc5f`.

Both dictionaries have exactly BBox, Length, Matrix, Subtype and Type;
Type/Subtype are XObject/Form, generation and direct Length are zero. The
outer BBox `[0 0 8.63390 12.22000]` and Matrix `[8.33930 0 0 5.89180 0 0]`
match the inner values exactly after removing redundant fractional zeros.
No floating-point rounding is needed.

The **actual live xref for 754 points to 1078402**, where it is a shading
function. Selecting the embedded serialization as object 754 would change a
real object and leave references to 485 unresolved. This profile therefore
needs a separate indexed-PDF rule from #439's same-ID CAJ fragment recovery.
The graph has one direct incoming reference to 485: page-47 object 481's
`/Resources/XObject/Meta754`. Page 47 executes `/Meta754 Do`. Page 12 reaches
page 47 through an annotation destination; that path is navigation rather
than a second rendering invocation.

## Independent diagnostics and retained disagreements

A diagnostic appends an empty revision of **485** without altering original
bytes or other object IDs. The first diagnostic incorrectly set trailer Size
962 rather than 961 and produced a separate qpdf warning. Corrected v2 retains
source Size 961. These modified diagnostics remain distinct from production
conversion of the unchanged original.

The original qpdf scan warns about duplicate MediaBox and CR stream separators.
For malformed stream 485, qpdf infers **112** content bytes while MuPDF infers
**110**; the declared Length remains zero. Source Poppler warnings occur on
page 47 for the nested object/stream syntax. The receipt preserves all these
warnings and the earlier diagnostic's Size mistake. Original validation is
not presented as clean or unambiguous for general PDF stream recovery.

## Bounded implementation and review

The original MIT fix reuses existing bounded head, five-key profile and tail
parsers, dictionary repair serialization, sorted live-span validation and
append-only output. It appends an empty revision under the outer ID and leaves
the actual live inner ID unchanged. The different inner ID must have a
separate standalone generation-zero xref; every live object's span is checked
for overlap with the entire outer frame. No per-candidate scan of all xrefs
is added.

Each header is bounded to **256 bytes** and each of the four tail whitespace
gaps to **64 bytes**. Only redundant trailing fractional zeros and their dot
are normalized; signs, integer digits, token boundaries and arbitrarily long
distinct decimals remain exact. Additional/duplicate dictionary keys,
nonempty/indirect Lengths, same-ID nesting, incomplete/recursive framing and
missing/free/compressed/different-generation inner xrefs remain errors.

Both headers and tails are compared with a fresh complete bounded-frame read.
Retained proof bytes and the proof index are each capped at **64 KiB** or
one eighth of the caller's allocation limit, whichever is smaller. Replacement
bodies share the existing repair budget. Every proof byte is checked again
during sequential copying, before CR normalization. Shared chunk-boundary
comparison serves existing gap patches and these read-only proofs; only gaps
are blanked. There is no whole-file buffer, payload search or codec change.

Seven new original test groups cover both live-xref orderings, strict profiles,
exact 255/256/257-byte boundaries, aggregate proof limits, short reads/writes,
cancellation/allocation errors, and mutation of **every** proof byte both at
capture and during copying. Existing #439 controls remain passing.
[Self-review](https://github.com/rwv/caj2pdf-rust/pull/447#issuecomment-6063481735)
checks provenance, all acceptance criteria, identities and bounds. It is not
an independent approval. No foreign converter/vendor implementation, private
source migration, new dependency or external fixture bytes were used.

## Production content, runtime and viewer checks

The unchanged KDH produces the same **4,720,370-byte** PDF in native, Node and
Chromium, SHA-256
`6c32efe1fc0abf3b9f7f4737428b73dc3e0a82f2973ae6ac147564cf6300b2aa`.
Qpdf exits 0. All **960 canonical object values** and the other **304 raw
streams** agree with the independently decoded original. All **66 page IDs,
geometry, text, links and Poppler RGB72 renders** agree. Both outline
inventories are empty. Chromium's ranged OPFS input, sequential output and
temporary-file cleanup are verified. Source hashes remain intact.

Three fresh contained original-viewer sessions compare unchanged KDH,
production PDF and a control that paints only Form 485. The visually reviewed
1600×1200 full frames show page **47/66 at 50%**. The complete page crop
`[626,156,1023,718]` matches exactly between source and production; the
Form-content control changes **76 pixels**. Each session's 3/10/12-second
captures agree. Separate earlier diagnostic sessions produce the same scoped
result and are recorded separately.

The pinned viewer image runs without network, with read-only root/input,
non-root user, dropped capabilities, 2 GiB memory/swap, two CPUs, 256 pids and
a 90-second hard lifetime. All sessions retain source hashes, avoid OOM and
verify container removal. Other vendor-viewer pages were not run. This does
not establish whole-document vendor fidelity or resolve [#441](https://github.com/rwv/caj2pdf-rust/issues/441).

## Validation and scope

Local validation has **1,354 Rust passes**, **seven ignored optional-corpus
tests**, and **166 JavaScript passes with zero skips**. Ignored tests are not
compatibility evidence. Strict clippy, formatting, source inventory and
Markdown links pass. Initial local setup failures are retained: the test-only
patch helper lacked newly added fields; an intended long-header negative was
still under the bound; the first JS run lacked its hardcoded raw-WASM test
artifact. Corrected runs pass with the same frozen production binaries.

The fresh **1,277-original / 2,126-attempt** native regression has **1,248 PASS,
20 FAIL and nine UNSUPPORTED**, with qpdf PASS for all 1,248 conversions. Only
this KDH is newly accepted. All **2,096** previous successful attempt hashes
are unchanged; no refusal diagnostic changed. Source integrity and failed-output
cleanup pass for every attempt. Ancillary order checks are 286 PASS, 26 FAIL
and 936 NOT_RUN; source-outline checks are 297 PASS and 951 NOT_RUN. The new
KDH separately has a verified empty outline inventory above. The receipt
records exact-head required CI, every input, the unchanged 19-input extended
catalog, and the explicitly scoped baseline runtime run. Ancillary FAIL and NOT_RUN
states remain visible. Earlier independent bitmap/order evidence is reused
only after fresh output-hash equality checks; its decoders were not rerun.
CAA descriptors remain unsupported offline and no opaque target is resolved.
Other #406 refusals and content/viewer/outline limitations remain open; they
are not declared irrecoverable by this focused repair.

All **eight required CI checks** pass on the exact reviewed Rust head.
[Coverage](https://github.com/rwv/caj2pdf-rust/actions/runs/37802054847/job/113396516486)
is **98.60% (29,513 / 29,933 lines)** against a 90% workspace floor. The
native quality job's delayed dependency installation completed successfully;
no CI retry or code change was needed.

The separate full runtime run completed **1,247/1,247 Node and 1,247/1,247
Chromium** checks on reviewed #444 WASM `6b06130b8ffe8eb2328e7e569ed54b7e6838a194`,
SHA-256 `b6e6fdf31de274e1f67ea3134075b776702248795493d30cbcc7c121f1c982d7`.
Every output matches this candidate's native output; browser OPFS entries are
removed. A SIGTERM interrupted the initial run after 274 Node and 267 browser
results. The unchanged resumable harness preserved those passing rows and
completed the missing cases; no failed row was discarded. Its old summary
literal incorrectly says `277d4229931ce156e5d7b62159fdd6722fa0f1b6`. The receipt
retains that raw label and the independently verified actual package/WASM
identity. This is baseline runtime evidence, **not** a full-corpus run of
#446 WASM; the newly accepted KDH is tested separately on #446 as above.
