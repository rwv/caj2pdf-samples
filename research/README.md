# Research tooling archive

This directory holds the research apparatus that used to live in
[caj2pdf-rust](https://github.com/rwv/caj2pdf-rust): format investigations,
black-box oracles, layout and placement probes, viewer automation and the
conformance harnesses around them. It moved here in
[rwv/caj2pdf-rust#360](https://github.com/rwv/caj2pdf-rust/issues/360) so the
converter repository carries only the product, its own fixtures and its
required checks. Everything here is MIT, like the code it came from; the
external documents it measures stay outside Git, as before.

All material is pinned to caj2pdf-rust commit
`0abee3862f01756ee15f69a1b174a35208fc1e41`, the last commit that contained it.

| Directory | Moved from (caj2pdf-rust) | Content |
| --- | --- | --- |
| [`scripts/`](scripts/) | `scripts/` | JBIG1/JBIG2 and HN/C8 oracles, parity and layout/placement probes, `conformance.py`, `current_formats.py`, `vendor_fixture_diff.py`, `sample_catalog.py`, the CAJViewer canary and installer fetcher. |
| [`conformance/`](conformance/) | `tests/conformance/` | Unit tests for those scripts, committed oracle manifests and baselines (JSON/TSV), and the [corpus matrix](conformance/matrix.json) with its [provenance note](conformance/README.md). |
| [`cajviewer/`](cajviewer/) | `tools/cajviewer/` | Docker/X11 automation of the proprietary CAJViewer, its original control fixtures, the former [setup guide](cajviewer/SETUP.md) and the former manual installer workflow ([`cajviewer-installer.yml`](cajviewer/cajviewer-installer.yml), archived, not active here). |
| [`examples/`](examples/) | `crates/caj2pdf-core/examples/` | Rust parity and diagnostic harnesses (`jbig2_*`, `hnc8_*`, `native_kdh_probe`, `support/`). |
| [`notes/`](notes/) | `docs/research/` | The investigation and measurement notes ([index](notes/README.md)), plus the [provenance archive](notes/provenance-archive.md) and the [conformance command archive](notes/conformance-commands-archive.md). |

`scripts/`, `conformance/`, `cajviewer/`, `examples/` and `notes/` were added
with `git subtree`, so `git log -- research/<dir>` shows their caj2pdf-rust
history (for `notes/`, only since the `docs/research/` split in caj2pdf-rust
#322; earlier history is under `docs/` there). The scripts that caj2pdf-rust
still runs in CI or release workflows (`check-*`, `package-native.py`,
`build-bsd-cross.py`, `prepare-docker.py`, `test-docker.sh`, `install-*`,
`android-*`) were removed from this copy and stay there; `generate_fixtures.py`
is in both because `conformance/test_hnc8_outline_observation.py` imports it.
`native_caj_to_pdf.rs` and `native_kdh_to_pdf.rs` remain caj2pdf-rust's
examples and are not repeated here. `conformance/test_cajviewer_canary_fixtures.py`
was `tests/fixtures/test_cajviewer_canary_fixtures.py` there (plain copy).

## Rust examples are archived source

The files in `examples/` are not built by anything in this repository and are
not maintained against newer caj2pdf-core APIs. They compile only as
`crates/caj2pdf-core/examples/` of caj2pdf-rust at the pinned commit. To run
one, check that commit out, where they are still in place:

```sh
git clone https://github.com/rwv/caj2pdf-rust
cd caj2pdf-rust
git checkout 0abee3862f01756ee15f69a1b174a35208fc1e41
cargo build --locked --release -p caj2pdf-core --example jbig2_page_parity
```

## Running the Python harnesses

Most harnesses use only the Python standard library (3.11+), plus the external
black-box tools each one names (qpdf, MuPDF `mutool`, Poppler, libjpeg-turbo).
They resolve paths from the caj2pdf-rust layout (`scripts/`,
`tests/conformance/`, `tools/cajviewer/`), so run them from a caj2pdf-rust
checkout: either the pinned commit above, where everything is still in place,
or a current checkout with this directory overlaid at the original paths:

```sh
cd /path/to/caj2pdf-rust
cp -r /path/to/caj2pdf-samples/research/scripts/. scripts/
mkdir -p tests/conformance tools/cajviewer
cp -r /path/to/caj2pdf-samples/research/conformance/. tests/conformance/
cp -r /path/to/caj2pdf-samples/research/cajviewer/. tools/cajviewer/
python3 -m unittest discover -s tests/conformance -p 'test_*.py'
```

Corpus-backed runs read the external
[CAJSamples](https://github.com/caj2pdf/CAJSamples) checkout at revision
`7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07` (see the [catalog](../catalog.json)
and `tools/verify.py`) from `--corpus-dir` or `CAJ2PDF_CORPUS_DIR`. Without
it they report `NOT_RUN`, which is never a compatibility pass:

```sh
# Inventory, then compare PDFs a converter wrote to an external directory.
CAJ2PDF_CORPUS_DIR=/path/to/CAJSamples python3 scripts/conformance.py --json
CAJ2PDF_CORPUS_DIR=/path/to/CAJSamples python3 scripts/conformance.py \
  --pdf-dir /path/to/output --json

# Run a caj2pdf CLI binary over every pinned input.
python3 scripts/current_formats.py \
  --corpus-dir /path/to/CAJSamples \
  --candidate /path/to/caj2pdf \
  --output-dir /path/to/new-run-dir > /path/to/report.json
```

`--candidate` takes any caj2pdf CLI executable (a release download or
`target/release/caj2pdf`); outputs must go to a new directory outside both
checkouts. The JBIG/HN parity scripts (`jbig2_*_parity.py`,
`hnc8_page_composition.py`, `jbig2_directory_inventory.py`) build the archived
Rust examples with `cargo`, so they need the pinned caj2pdf-rust commit.
Oracle-specific inputs (`CAJ2PDF_JBIG1_ORACLE_LIB`,
`CAJ2PDF_T88_H2_FIXTURE_FILE`, the CAJViewer installer) are described in each
script's `--help` and in the [notes](notes/README.md).

caj2pdf-rust keeps its own `#[ignore]`d corpus tests (`cargo test -- --ignored`
with `CAJ2PDF_CORPUS_DIR`), the JavaScript corpus runner and the three
metadata files those read (`tests/conformance/matrix.json`,
`jbig1_oracle.json`, `hnc8_type2_jpeg_inventory.tsv`).

`native_text_order.py` additionally uses optional PyMuPDF (measured with 1.27.2.2)
to open PDF objects. Missing PyMuPDF yields NOT_RUN in the integrated native-text
check. Its parser unit tests use only the standard library. See the
[native content verification note](notes/native-content-order-20261008.md).

`github_bitmap_oracle.py` runs directly from this samples checkout and compares
a pinned source/PDF pair through the existing external image oracles. Its
[coverage note](notes/github-bitmap-oracles-20261008.md) explains the required
external tools, source hashes, row conventions and evidence limits. Generated
PDFs and pixels stay in external temporary directories.

`indexed_lookup_audit.py` audits decoded palette lengths in a hash-pinned
external output manifest, using pikepdf and bounded POSIX child processes.
`indexed_palette_loss_probe.py` demonstrates missing-color ambiguity in one
exact source; its diagnostic PDFs and pixels must remain outside Git. See the
[Indexed palette report](notes/indexed-palette-loss-20261008.md) for commands,
synthetic controls, dependencies and limits.

`hnc8_outline_inventory.py` inventories measured C8/HN-B index boundaries
and bounded explicit application-info packages. Its
[849-source report](notes/hnc8-outline-inventory-20261008.md) records structural
and selected viewer evidence without inferring missing outlines. It uses
only Python's standard library; seven original control groups run in CI.
