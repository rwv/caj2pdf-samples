# TEB container integrity, damaged attachment and diagnostic boundary

This follow-up to [Rust #468](https://github.com/rwv/caj2pdf-rust/issues/468)
and [#469](https://github.com/rwv/caj2pdf-rust/issues/469) inventories all nine
collected TEB identities. Eight have internally consistent container framing,
readable XML metadata and matching entry CRCs. One public attachment has a
verified zero-filled suffix. None has a newly decoded PDF. The older blanket
CRC-failure and irrecoverability claims in `RESEARCH.md` were incorrect.

The [machine-readable receipt](teb-container-boundary-20261009.json) records
full source identities, offsets, bounds, entry checks, redacted XML shapes,
acquisition proof, eleven fresh viewer sessions and native/Node/Chromium refusals.
Only metadata is committed. Source files, XML values, credentials, fonts,
captures and derived documents remain outside the repository.

## Corrected measured framing

All eight complete containers have the following profile. Integers are little
endian. These are observations of the pinned sources, not a universal TEB spec.

| Region | Observed layout |
| --- | --- |
| `0x00..0x20` | `TEB\0`, u32 `4`, then zero bytes |
| `0x20..0xA0` | Producer string followed by zero padding |
| `0xA0`, 16 bytes | `PK 08 08`, entry count `2`, central-directory byte length `110`/`111`, directory offset relative to `0xA0` |
| Local records, 28 bytes each | `PK 03 04`, version, flags, method, time/date, CRC, stored/plain lengths, name length; payload follows immediately, without filename bytes or an extra-length field |
| Central records, 40 bytes each | `PK 01 02`, versions, flags, method, time/date, CRC, lengths, name/extra/comment/disk fields and relative local offset; standard internal/external attributes are absent |
| Central names | Following bytes XOR their zero-based byte index; one metadata entry and one declared PDF entry |
| Rights trailer | XML declaration and `right-meta`, then whitespace and `startrights offset,length` |

The local spans are contiguous from byte 176 to the directory. Both directory
records agree with their local headers and account for the complete directory.
Entry order differs. `document.xml` uses method 8 and flags 2; its raw-deflate
stream terminates, matches its declared decoded length and decoded CRC. The
other entry uses method 0 and flags 0; its stored bytes match the declared CRC.
An encoded stream's raw CRC need not equal its decoded CRC.

The metadata names the declared PDF entry and declares 100 pages for each of
the original seven files, and 68 for the later intact GitHub source: **768
metadata-declared pages**, not recovered or verified document pages. Inflated
metadata is 1,006/1,007 bytes for the seven, and 812 bytes for the later source.
The declared PDF payloads lack a `%PDF-` header in their first 1,024 bytes.

Rights version is `2.1`. The four `meta/catalog/notes/content` encryption
attributes all equal `1`, even though `document.xml` is readable. These
attributes alone do not establish how each entry is protected. The declared
rights lengths include three trailing whitespace bytes after the closing XML
element: 2,397 bytes for the seven originals and 2,401 for the later source.
The report retains field names and text lengths only. Actual content wrapping,
key derivation and validated credential requirements remain unestablished.
No embedded endpoint was contacted and no credential supplied.

The public [ZIP APPNOTE](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)
provides the standard local/central-record and CRC baseline; the deviations
above come from independent byte observations. No foreign converter or vendor
implementation was read or copied.

## Source identities and damaged suffix

Full hashes and pinned origin revisions are in the receipt. Prefixes below
identify its nine rows; they are not substitutes for full download verification.

| Source | SHA-256 prefix | Inventory | Offline viewer |
| --- | --- | --- | --- |
| `issue-61/1.teb` | `760b0da02635` | Intact framing/CRCs | Validation-server connection error |
| `issue-61/2.teb` | `b7dfd1fbf5a6` | Intact framing/CRCs | Same error |
| `issue-61/3.teb` | `88efaaad1426` | Intact framing/CRCs | Same error |
| `issue-61/4.teb` | `84e6df33d3d0` | Intact framing/CRCs | Same error |
| `issue-61/5.teb` | `ba7efa391b92` | Intact framing/CRCs | Same error |
| `issue-61/6.teb` | `d5f87439a53c` | Intact framing/CRCs | Same error |
| `issue-61/7.teb` | `fc773e95124e` | Intact framing/CRCs | Same error |
| Uploaded `6.teb` | `8c406195b11f` | Directory/rights absent in zero-filled suffix | Unknown error, literal `Code=%d` |
| `ce-amtic/caj2pdf-actions/file.caj` | `d2ef9d7327b9` | Intact framing/CRCs | Connection error under both `.teb` and original `.caj` extension |

The separately uploaded `6.teb` is 5,702,269 bytes. Its first **4,194,304 bytes**
match the catalog's intact `d5f87439a53c...` candidate exactly; the remaining
**1,507,965 bytes are all zero**. There are 1,502,134 differing bytes in that
suffix; some original bytes were already zero. Missing data includes a large
payload suffix, the directory and rights wrapper. The checker refuses the
missing central signature, and the report retains that refusal explicitly.

A fresh download of the [public ZIP attachment](https://github.com/caj2pdf/CAJSamples/files/6020638/teb_samples.zip)
is identical to the cached 9,392,366-byte archive, SHA-256
`334d2d3cc586a9cafa18a8f8dedb6098bca34ee4d7abb03c406c14678d2136a1`.
Both members were read completely and their outer ZIP CRCs verified: damaged
`6.teb` has CRC32 1,826,993,174; `7.teb` has CRC32 1,201,373,713. The latter is
the already cataloged intact `fc773e95124e...` identity. This places the zero
suffix in the upstream attachment, rather than local extraction or download.

The intact candidate is separately pinned to CAJSamples revision
`7e1c35e7b6de34e21972fcd1752c2a7e99b4ad07`; its computed Git blob identity
`77f7d036ab61c1b785d0a1a426e510a9e5700944` matches the fresh GitHub metadata.
It is not automatically substituted or counted as recovery. The damaged bytes
alone do not determine their lost suffix; the complete candidate still has
unresolved content wrapping.

## Fresh offline viewer observations

Eleven isolated Linux CAJViewer 9.0.0.24093 sessions cover all nine identities,
a paired `.caj` extension for the later source, and an original MIT two-page
PDF positive control. The control visibly opens with two pages and two outline
entries. All complete TEB containers show a validation-server connection error;
the damaged identity shows the distinct unknown-error dialog. No TEB document
tab becomes available.

The existing image is pinned to
`sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de`.
A fresh vendor download-page fetch failed; this is not a latest-version claim.
Each session has no network, read-only root/input, unprivileged UID 1000,
dropped capabilities, no new privileges, a 2 GiB memory/swap limit, two CPUs,
256 PIDs and a 90-second hard lifetime. Font and source identities are recorded.
Captures occur at 5/10/20/25 seconds; every 20/25-second RGB pair is identical.
All four distinct final frame groups were inspected. No navigation or zoom
action is claimed. Every source remained unchanged; containers were removed
and none was OOM-killed.

These are readable open errors, not complete-document fidelity comparisons.
They do not prove that network access is the sole missing condition or resolve
viewer repeatability issue #441. Catalog `viewer: FAIL` has this narrow scope.

## Diagnostic correction and runtime checks

The old CLI inferred `drm-encrypted` from format detection alone, and CLI/JS
conversion claimed that content was encrypted and could not be converted.
That conclusion also applied to the original minimal/truncated TEB control.
[#469](https://github.com/rwv/caj2pdf-rust/issues/469) removes this overclaim:
TEB is recognized but conversion is currently unsupported. CLI JSON changes
`unsupported_reason` to `not-implemented`, an explicitly documented breaking
value migration. Page and outline information stays unknown.

Implementation commit `149c380f948fce9f7d56037378653152afb924f7` changes only
CLI reporting and the shared JavaScript error path. The new local CLI SHA-256 is
`db099654f5e7b6388a68550d7f2deba02f187026b251222ed25f690e6f64a3a9`.
WASM bytes remain identical to the previous reviewed build,
`7e8d90aef49fa4d15e3b95ccc0bc3b207e325b19d777548c81c5cc2665a5e77b`.
The receipt preserves both the freshly observed old diagnostic and the new one.

All nine sources were checked again with native, Node and real Chromium:
**27 expected refusals**, zero emitted PDF bytes, unchanged source hashes and
empty output/OPFS temporary storage. Native inspect succeeds with the new
reason and conversion exits 1; both JavaScript targets preserve the typed
`UNSUPPORTED_FORMAT` error. The frozen runtime package hashes also remain
unchanged. These are refusal checks, not successful conversions. CLI tests pass
95 cases with one optional external-corpus case ignored; the affected JavaScript
suite passes 44 with no skips.

## Original checker, controls and remaining work

[`teb_inventory.py`](../scripts/teb_inventory.py) and its
[controls](../conformance/test_teb_inventory.py) are original MIT code, using
only Python's standard library and independent observations. There is no new
production decoder, dependency or imported private/vendor implementation.
The inventory reads sequential payload chunks and bounded seekable metadata:
512 MiB maximum source, 64 KiB buffers/directory/inflated XML, two entries,
128 XML elements and a 512 MiB address-space cap. The final sequential run
reports VmHWM 60,828 KiB and VmPeak 79,480 KiB. SHA-256 is verified before and
after reading; no payload or XML value is extracted to disk.

Seven test groups cover both entry orders, raw/decoded CRC corruption,
local/central disagreement, span/storage limits, XML/footer/entity boundaries,
self/unknown content references, deflate completion/trailing data, source
identity/truncation, CLI failure output and zero-suffix comparisons. The selected
Catalog suite passes **103 tests with no skips**. Earlier failed hypotheses
and harness attempts remain in the receipt: standard ZIP framing, mistaken
extent/name assumptions, an overly strict final-newline control, the missing
local WASM test path and the incorrect native harness subcommand.

The parent corpus remains **1,252 PASS / 18 FAIL / 27 UNSUPPORTED**, with
35,587 accepted pages. This report satisfies container/damage evidence for
#468 and supports the diagnostic fix in #469. Actual PDF wrapping, required
credentials and recovery of complete TEB documents remain open under #468.
Native font/raster fidelity, unknown outlines and other exceptions also keep
#406 open. No general irrecoverability conclusion, release or compatibility
promotion follows from these measurements.

The [certificate follow-up](teb-credential-boundary-20261009.md) subsequently
identifies X.509/RSA public-key structure in the eight complete sources and
records bounded opaque-field/payload probes. Actual wrapping and usable
credentials remain unestablished; the earlier no-recovery boundary is unchanged.
