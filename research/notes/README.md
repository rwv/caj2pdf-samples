# Research notes

The [2026-10-08 CAA/NH discovery](caa-nh-discovery-20261008.md) adds 18 descriptors and one
original-extension HN-A document, with offline viewer and complete
CLI/Node/Chromium results. It supersedes the earlier CAA/NH sample gaps;
CAS remains open in [#28](https://github.com/rwv/caj2pdf-samples/issues/28).

These notes record the format investigations, oracles and validation runs
behind the decoders. They are evidence, not user documentation: start with
the [README](../../README.md) and the [CLI reference](../cli.md). Each note
keeps its own provenance statement; the project-wide record is
[provenance](../provenance.md). "Historical" marks a closed investigation
whose result is summarized elsewhere.

See the [2026-10-07 GitHub corpus sweep](github-sample-sweep-20261007.md) for the expanded inventory and the [post-fix validation](github-sweep-fixes-20261007.md) for current conversion results, remaining refusals and fidelity limits.

## CAJ, KDH and PDF

| Note | Backs |
| --- | --- |
| [Font-free viewer raster controls](viewer-raster-stages-20261009.md) | samples #68 / Rust #441; ten retained sessions, font-free buffer differences, matching no-observer variants and unresolved readiness |
| [TTKN wrapper inventory](ttkn-wrapper-inventory-20261008.md) | Rust #415; 16 pinned encrypted originals, two wrapper families and unresolved credential semantics |
| [TTKN payload and viewer boundary](ttkn-payload-boundary-20261008.md) | Rust #415; all 16 readable offline errors, bounded single-Flate checks and unresolved recovery |
| [Nested duplicate empty Forms](nested-empty-forms-20261008.md) | Rust #439; three unchanged originals, full native regression and retained viewer disagreement |
| [Bounded issue-20 stream recovery](stream-substitution-recovery-20261008.md) | Rust #436; unchanged-original proof and full final regression |
| [CAJ container observations](caj-format.md) | `caj/`, `gb18030.rs`, CAJ tests |
| [Interrupted CAJ PDF objects](caj-interrupted-objects.md) | `caj/` recovery |
| [Indexed palettes: syntax repair is not color recovery](indexed-palette-boundary-20261008.md) | Rust #420; unresolved missing colors and cross-renderer behavior |
| [KDH PDF wrapper observations](kdh-format.md) | `kdh.rs` |
| [Forward-only PDF writer](pdf-writer.md) | `pdf/writer.rs`, `pdf/document.rs` |
| [Incremental native-text PDF output](pdf-native-text.md) | `pdf/font.rs`, native pages |
| [Streaming bilevel PDF compression](bilevel-compression.md) | `pdf/` image streams |

## HN/C8 container, text and outlines

| Note | Backs |
| --- | --- |
| [TEB certificate and opaque-field boundary](teb-credential-boundary-20261009.md) | Rust #468; public-certificate structure, bounded payload scans and remaining wrapping/credential uncertainty |
| [TEB container and damaged-tail boundary](teb-container-boundary-20261009.md) | Rust #468/#469; corrected framing/CRCs, eight intact containers and one damaged attachment, offline opens and remaining recovery limits |
| [Native glyph and ornament model verification](native-glyph-model-20261009.md) | samples #51; 83,432 glyphs and 212 ornament marks in both PDF sets; original-font/raster limits retained |
| [Normal native caller-font subsets](native-font-subsets-20261009.md) | samples #57; 6,140 resource/CID pairs and 83,644 draws match caller outlines/advances; viewer-font and hinting limits retained |
| [Native vector geometry and painting order](native-vector-geometry-20261008.md) | samples #51; all 327 paths on 60 pages, with font/ornament/raster limits retained |
| [Bounded HN/C8 container records](hnc8-container.md) | `hnc8.rs` reader |
| [Compact HN-B page index](hnb-compact-index.md) | `hnc8.rs` HN-B index |
| [Compressed HN-A/C8 text header](hnc8-compressed-text-header.md) | `hnc8/text.rs` |
| [Direct compressed HN/C8 page records](hnc8-direct-text.md) | `hnc8/text.rs` |
| [Uncompressed HN-A page text](hnc8-uncompressed-text.md) | `hnc8/text.rs` |
| [HN-A/C8 text framing and placement controls](hnc8-text-source.md) | `scripts/hnc8_text_frame.py` |
| [Expanded C8/HN-B outline sample search](hnc8-outline-sample-search.md) | #303; three new conversion failures |
| [HN-B magnesium article](hnb-magnesium-profile.md) | #381; original controls, type-3 layering and private-code preservation |
| [Additional C8 native profiles](c8-additional-profiles.md) | #380/#382; independent controls and conversion checks |
| [HN-A outline fields: observed profile](hnc8-outline-fields.md) | `hnc8/outline.rs` |
| [HN/C8 outline investigation and implementation proposal](hnc8-outline-observation.md) | `scripts/hnc8_outline_observation.py` |
| [Closed issue #119 Stage A observation report](hnc8-outline-stage-a-results.md) | historical |
| [HN outline field validation plan](hnc8-outline-stage-b-proposal.md) | `hnc8/outline.rs` |

## HN/C8 images

| Note | Backs |
| --- | --- |
| [GitHub sweep bitmap coverage](github-bitmap-oracles-20261008.md) | samples #23; missing source-image oracles under rust #406 |
| [HN/C8 type-0 image observations and pixel oracle](jbig1-oracle.md) | `scripts/jbig1_oracle.py` |
| [HN/C8 type-0 bitstream experiments](jbig1-bitstream-investigation.md) | historical |
| [HN/C8 type-0 row-model candidate](jbig1-row-model.md) | `qm.rs` |
| [Bounded HN/C8 type-0 rows](jbig1-type0-rows.md) | `jbig1.rs` |
| [T.82 arithmetic core](t82-arithmetic-core.md) | `qm.rs` |
| [HN/C8 type-0 pages to PDF](hnc8-type0-pdf.md) | `hnc8/convert.rs` |
| [HN/C8 type-0 PDF pixel diagnostic](hnc8-type0-pdf-parity.md) | type-0 parity test |
| [HN/C8 type-1 JPEG support (#224)](hnc8-type1.md) | `hnc8/jpeg.rs` |
| [Bounded HN/C8 type-2 JPEG marker profile](hnc8-type2-jpeg.md) | `hnc8/jpeg.rs` |
| [Selected HN/C8 type-2 JPEG PDF diagnostic](hnc8-type2-pdf.md) | `hnc8/convert_jpeg.rs` |
| [Selected HN/C8 type-3 JBIG2 PDF diagnostic](hnc8-type3-pdf.md) | `hnc8/convert_jbig2.rs` |
| [Bounded embedded JBIG2 directory](jbig2-directory.md) | `jbig2/directory.rs` |
| [Bounded JBIG2 segment-header reader](jbig2-segment-header.md) | `jbig2/directory.rs` |
| [External HN/C8 JBIG2 pixel oracle](jbig2-oracle.md) | `scripts/jbig2_oracle.py` |
| [External HN/C8 generic-only JBIG2 pixel oracle](jbig2-generic-oracle.md) | `scripts/jbig2_generic_oracle.py` |
| [Bounded JBIG2 generic-region template 2](jbig2-generic-template2.md) | `jbig2/generic.rs` |
| [External Rust generic-region pixel parity](jbig2-generic-parity.md) | `scripts/jbig2_generic_parity.py` |
| [External HN/C8 text-only JBIG2 pixel oracle](jbig2-text-oracle.md) | `scripts/jbig2_text_oracle.py` |
| [Observed HN/C8 full-page JBIG2 pixel parity](jbig2-page-parity.md) | `scripts/jbig2_page_parity.py` |
| [T.88 MQ arithmetic core](t88-mq-core.md) | `jbig2/mq.rs` |
| [T.88 MQ state-data provenance decision](t88-mq-rights.md) | `jbig2/mq/standard.rs` |
| [T.88 non-IAID arithmetic integers](t88-arithmetic-integer.md) | `jbig2/integer.rs` |
| [T.88 fixed-length IAID decisions](t88-iaid.md) | `jbig2/iaid.rs` |
| [Bounded direct-coded T.88 symbol dictionaries](t88-symbol-dictionary-direct.md) | `jbig2/dictionary.rs` |
| [Bounded T.88 template-1 generic refinement bitmaps](t88-refinement-template1.md) | `jbig2/refinement.rs` |
| [Bounded T.88 single-reference symbol dictionary](t88-refinement-dictionary.md) | `jbig2/refinement_dictionary.rs` |
| [Bounded T.88 text-region headers](t88-text-region-header.md) | `jbig2/text.rs` |
| [Explicit HN/C8 text-header compatibility](t88-text-header-compatibility.md) | `jbig2/text.rs` |
| [Bounded T.88 arithmetic text-instance stream](t88-text-instances.md) | `jbig2/text_instances.rs` |
| [Bounded T.88 text-region composition](t88-text-composer.md) | `jbig2/text_composer.rs` |
| [Observed HN/C8 JBIG2 page composition](t88-observed-page-composition.md) | `jbig2/page_compose.rs` |

## HN/C8 page composition and placement

| Note | Backs |
| --- | --- |
| [Bounded image-only HN/C8 page composition](hnc8-page-composition.md) | `hnc8/compose.rs` |
| [Repeated HN/C8 image groups](hnc8-repeated-groups.md) | `hnc8/compose.rs` |
| [HN/C8 source-page layout measurements](hnc8-layout-oracle.md) | `scripts/hnc8_layout_*.py` |
| [Additional-image placement experiments](hnc8-placement-experiments.md) | `scripts/hnc8_placement_*.py` |
| [Source-derived HN-A/C8 placement profile](hnc8-placement-rule.md) | `hnc8/placement.rs` |
| [Source-page composition evidence](hnc8-page-composition-evidence.md) | historical |
| [Issue #117: predeclared source-page composition validation](hnc8-page-composition-protocol.md) | `scripts/hnc8_page_composition.py` (hash-pinned) |
| [Issue #117: bounded dictionary-profile follow-up](hnc8-page-composition-dictionary-probe.md) | `scripts/hnc8_page_composition.py` (hash-pinned) |
| [Issue #117: explicit identity-parameter comparison amendment](hnc8-page-composition-identity-params-rerun.md) | `scripts/hnc8_page_composition.py` (hash-pinned) |
| [Issue #117: HN-B JPEG color interpretation investigation](hnc8-page-composition-hnb-color-probe.md) | historical |
| [Issues #117/#122: independent HN-B grayscale reference](hnc8-page-composition-hnb-corrected-reference.md) | historical |
| [Issues #117/#122: rational pixel dimensions and complete three-profile rerun](hnc8-page-composition-rational-rerun.md) | `scripts/hnc8_page_composition.py` |

## Native C8/HN-B pages

| Note | Backs |
| --- | --- |
| [Full native composition checkpoint](native-page-composition-20261008.md) | samples #51; all 60 pages, original marker controls, per-page differences and retained viewer uncertainty |
| [Native text feasibility (#223)](native-text-feasibility.md) | historical |
| [Observed C8 native records](c8-native-records.md) | `hnc8/native.rs`, `hnc8/native_page.rs` |
| [C8 encoded-string record framing](c8-encoded-prefix.md) | `hnc8/native.rs` |
| [Additional native C8 control framing](c8-native-controls.md) | `hnc8/native.rs` |
| [Native C8 image-reference records](c8-image-references.md) | `hnc8/native_page.rs` |
| [Native-text fidelity checkpoint (#269)](hnc8-text-fidelity.md) | native page tests |
| [C8 real-font checkpoint (#278)](c8-real-font-fidelity.md) | release checkpoint |
| [HN-B real-font checkpoint (#277)](hnb-real-font-fidelity.md) | release checkpoint |

## CAJViewer reference runs

| Note | Backs |
| --- | --- |
| [Displayed-contents observation protocol](viewer-outline-protocol-20261009.md) | samples #63; bounded public Qt tree counts and original controls |
| [CAJViewer vendor fixtures](cajviewer-fixtures.md) | `tools/cajviewer/` |
| [CAJViewer fixture snapshot](cajviewer-fixture-snapshot.md) | historical |
| [HN/C8 and KDH viewer checks](cajviewer-hnc8-kdh.md) | release checkpoint |
| [CAJViewer page-box fallback](cajviewer-page-boxes.md) | `caj/` page boxes |
| [CAJViewer capture pilot — 2026-09-29](cajviewer-capture-pilot.md) | `scripts/cajviewer_canary_fixtures.py` |
| [Original PDF controls and Linux startup canary](cajviewer-linux-startup.md) | `tools/cajviewer/run.py` |
| [CAJViewer Linux startup diagnostics: seventh proposed profile](cajviewer-startup-diagnostics-v7.md) | `scripts/cajviewer_canary.py` |
| [Safe public-module load diagnostics](cajviewer-source-loading.md) | `tools/cajviewer/run.py` |
| [Bounded inventory-helper diagnostics](cajviewer-inventory-diagnostics.md) | `tools/cajviewer/run.py` |
| [Original bounded capability protocol (#146)](cajviewer-capability-protocol.md) | `tools/cajviewer/run_capabilities.py` |
| [CAJViewer public runtime-view inventory: closed v11 phase](cajviewer-runtime-view-v11.md) | historical |
| [V14 public runtime-view report](cajviewer-runtime-view-v14.md) | historical |
| [External vendor fixture manifests](vendor-fixture-manifest.md) | `scripts/vendor_fixtures.py` |
| [Compare decoded vendor fixtures](vendor-fixture-diff.md) | `scripts/vendor_fixture_diff.py` |

The [PNG Up/object-stream follow-up](pdf-predictor-object-streams-20261007.md)
records #402/#404, original native/Node/Chromium parity and the complete native
regression rerun after that fix.

- [Identical fragment page boxes: four-original verification](fragment-mediabox-20261008.md) (#407/#408).
- [Correct the type-0 image oracle row convention](image-order-row-convention-20261008.md) (partial #12).

- [Native content checks for text-only and mixed pages](native-content-order-20261008.md) (#12).
- [Complete accepted-corpus Node and Chromium parity](full-runtime-parity-20261008.md) (#406).

- [Complete accepted native-glyph coverage](native-content-completion-20261008.md) (#19).

- [Interrupted live PDF object prefixes](live-object-prefix-20261008.md) (#410/#411).

- [Equivalent opacity resource references](equivalent-opacity-resources-20261008.md) (#412/#413).

- [Proved interrupted CAJ copies](interrupted-copies-20261008.md): three unchanged originals, 463 pages, complete object/stream and reference proof, scoped viewer controls, and a 1,277-original regression.
- [Indexed nested empty Form](indexed-empty-form-20261008.md): preserve the outer object identity in a 66-page KDH, with complete xref/stream proof, all-page comparisons, scoped viewer controls and a 1,277-original regression.
- [Truncated 134-page CAJ](truncated-caj-20261008.md): original Git-blob identity, missing stream/page spans, runtime refusal/cleanup, scoped viewer damage behavior and a distinct archived-PDF follow-up.

- [Named local destinations](named-destinations-20261008.md): a separate 139-page archived author PDF, bounded name-tree support, all-page/object/stream checks, scoped reader navigation controls and preserved baseline results.

- [Interrupted metadata and missing CAJ parents](interrupted-metadata-parents-20261008.md): one recovered 53-page original, complete object/stream/page/bookmark proof, scoped viewer negatives, preserved baseline hashes and a separately fixed browser cancellation race.

- [Retained CAJ catalog and incomplete page tree](retained-catalog-20261008.md): one recovered 78-page original, retained page labels, complete object/stream/page/bookmark comparisons, scoped viewer controls and unchanged prior-success hashes.

- [Missing Indexed colors and accepted-output audit](indexed-palette-loss-20261008.md): two incompatible completions of the same surviving source data, source-history identity, current refusal/cleanup and a bounded lookup-length audit of 1,252 accepted PDFs.

- [Current complete corpus runtime checkpoint](current-corpus-runtime-20261008.md): all 1,252 accepted inputs match the reviewed native output on Node and Chromium; all 45 remaining inputs receive explicit refusal/cleanup checks on all three runtimes.
- [Expanded C8/HN-B outline inventory](hnc8-outline-inventory-20261008.md): 849 structural inventories, six selected contents-panel observations and correction of the historical 132-page HN-A example; no verified C8/HN-B outline layout.
- [Source page and ordered image geometry](source-image-geometry-20261008.md): 973 accepted HN/C8/NH originals, 16,548 pages, independent bitmap/resource bindings and fresh NH bitmap evidence; native glyph/vector placement and complete rendering remain separate.

- [Original native viewer navigation controls](native-viewer-navigation-20261009.md): page-count/index controls reproduce differing completed rasters; index swaps distinguish preceding content from navigation position. No readiness or fidelity pass.

- [Complete displayed-contents sweep](viewer-outlines-20261009.md): all 849 C8/HN-B originals, three empty-model checkpoints each, populated controls before/after and retained attempts; no stored-layout absence or rendering claim.
