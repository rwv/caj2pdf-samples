# Complete displayed-contents sweep (2026-10-09)

The sweep for [samples #63](https://github.com/rwv/caj2pdf-samples/issues/63) is complete:
all **849 unchanged originals** in the frozen C8/HN-B inventory were attempted
once under the [fixed public model/view protocol](viewer-outline-protocol-20261009.md).
Every selected contents panel had an empty model and the measured empty caption.
The [per-source receipt](viewer-outlines-20261009.json) retains all input,
observer, screenshot, model-trace and cleanup identities. Its SHA-256 is
`03887247a96d3155c56d2efe3efca900a8886fa6eb6b7269fc5ede713e3882c2`.

| Original variant | Unique sources | Observed empty | Observed populated | Unconfirmed |
| --- | ---: | ---: | ---: | ---: |
| C8 | 845 | 845 | 0 | 0 |
| HN-B | 4 | 4 | 0 | 0 |
| Total | 849 | 849 | 0 | 0 |

The cohort declares 2,855 pages. Each session verifies the first-page indicator
and declared total; this is not an observation of every rendered page. Three
separated contents checkpoints per source and every intervening timer sample
agree, with 16–17 consecutive samples per source. All 849 original and copied
input hashes remain unchanged. Every container is removed, with no OOM or
cleanup failure; measured peak memory spans 269,271,040–706,736,128 bytes.
There are no automatic retries or excluded corpus attempts.

## Controls and retained attempts

Fresh runs of the known 132-page HN-A control bracket the entire sweep. Both
show 81 nodes, 13 root rows and depth three, including collapsed children.
This control is not C8/HN-B and adds no corpus coverage. The three-source pilot
also has empty selected contents; those identities are repeated in the full
sweep and are not counted twice.

All four preliminary real-viewer calibration sessions are retained separately:
each of the initial and enhanced observers measured the HN-A populated model
and the 53-page C8 empty model. The first original Qt control failed before its
test ran because the pinned image lacks the requested offscreen plugin. Its
corrected X11 run observes the authored delayed transition from zero to six
nodes. The original lazy-model test initially assumed zero fetch calls, then
was corrected to compare with an unobserved Qt baseline because the view itself
may fetch rows. Neither failure is a corpus pass or silently discarded retry.
The first prototype source was edited before archival, so its original source
hash is unavailable. The enhanced source and both prototype binaries/logs are
retained separately from the frozen final observer and runner.

The final tool has original MIT Qt and receipt controls for nested/empty/lazy/
limited models, requested stop, incomplete/stale/ambiguous observations,
source bounds/identity and container cleanup. CI needs distro Qt and original
fixtures only. Before report generation, a separate receipt audit rehashes
all 849 inputs and captures, reproduces the three checkpoint selections and
every intervening sample, verifies stop acknowledgements and cleanup, checks
both populated controls, and compares frozen and published tool sources.

## Scope and provenance

This completes the available contents-panel observation gap left by the
[earlier structural inventory](hnc8-outline-inventory-20261008.md). It does
not establish that another stored outline representation is absent, verify
titles/destinations that were never displayed, or exclude later asynchronous
changes or different viewer behavior. [Rust #303](https://github.com/rwv/caj2pdf-rust/issues/303)
remains open for an actual positive original and independently established
layout; the unknown-outline diagnostic remains appropriate.

The observer uses public Qt5 model/view calls and fixed numeric UI metadata.
It reads no item text/private roles, changes no model and inspects no vendor
implementation or font program/outline. The pinned viewer is an external,
offline, read-only, nonroot research process. All document, screenshot, font,
generated fixture and binary bodies remain outside Git. See the protocol for
the original MIT source provenance, public headers, hard bounds and commands.

There is no production change, new conversion sweep or release. The existing
ledger remains 1,252 conversion PASS / 18 FAIL / 27 UNSUPPORTED. This observation
does not resolve source fonts/ornaments, raster readiness (#441), remaining
refusals or the broader correctness criteria in
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).
