<!-- SPDX-License-Identifier: MIT -->

# Public TTKN attachment and disclosed-response observation

Historical checkpoint. The [unchanged-source follow-up](ttkn-unaltered-wrapper-20261009.md)
now demonstrates viewer opening and reproduces the rights wrapper. The
URL-edited failure below remains scoped to that modified copy; production
conversion and independent full-document recovery are still unresolved.

One [public forum research attachment](https://chaoli.club/index.php/2979/5)
adds a seventeenth distinct TTKN original, under
[Rust #501](https://github.com/rwv/caj2pdf-rust/issues/501),
[Rust #415](https://github.com/rwv/caj2pdf-rust/issues/415) and
[samples #85](https://github.com/rwv/caj2pdf-samples/issues/85).
It still fails conversion. The author's disclosed response did not open an
offline diagnostic copy. Neither result proves irrecoverability.
The [metadata receipt](public-ttkn-response-20261009.json) retains acquisition,
structure, controls, observations, runtime outcomes and search limits.

## Acquisition and measured structure

The attachment is 1,891,106 bytes, SHA-256
`074cb4d57181e92826c37b549f811008c58c7b66366f9045e8985c58178263d8`.
Its public HTTP download succeeded within a 32 MiB streaming cap and does not
match any of the previous 1,384 catalog identities. An initial plain request
to the forum page returned 403; a subsequent request with an explicit research
User-Agent succeeded. Both observations remain recorded; no account was used.
Only metadata is redistributed, not the document or forum text.

The existing original `ttkn_inventory.py` finds PDF 1.6 through offset
1,889,611, a classic xref with 859 entries, and encryption object 858 0.
The live dictionary selects `TTKN.PubSec`, `TTKN.PubSec.s1`, `AESV2` and the
fixed eight-byte `AppendCA` recipient marker. The `WebFastLoad` suffix has a
1,459-byte rights XML at [1,889,623, 1,891,082), followed by its exact
`startrights` offset/length declaration. This third server/authentication
profile has no certificate/PFX; its base64 fields decode to 48 password,
32 IV and 704 rights bytes. These field names and dictionary labels do not
establish the actual cipher recipe or key derivation.

A bounded, value-redacted comparison confirms that the attachment author's
published request identifier matches this source, and the post contains one
deliberately disclosed response with a 32-hex-digit password field. The
response is not established as a PDF key or a presently valid credential.
The author's Adobe.PubSec/AES interpretation remains a hypothesis. Linked
foreign decryption implementations were not opened or used.

## Offline observations and original controls

Three fresh viewer sessions use the previously pinned opaque Linux viewer
image, with no external network, a read-only root/input, UID 1000, dropped
capabilities, no new privileges, 2 GiB memory/swap, two CPUs, 256 PIDs and a
75/90-second container deadline. The unchanged Noto UI font is mounted as an
opaque resource. Captures at 10, 25 and 45 seconds are identical within each
session; this does not establish a general viewer readiness criterion.

| Input | Observation |
| --- | --- |
| Unchanged public attachment | Validation-server connection error; no document opened |
| Diagnostic copy and matching disclosed response | One identity-matching POST received HTTP 200; rights-file error; no document opened |
| Original two-page PDF control | Both authored rectangles and the two outline nodes are visible |

The diagnostic copy changes only the authentication URL to an owned
`127.0.0.1` responder and updates the declared XML length. An independent
comparison verifies the exact PDF/prefix, every non-URL XML byte and the final
framing. The original is never modified. The responder runs inside the
network-disabled container, uses this one publicly disclosed response only
for its matching attachment, caps the request at 4 KiB and the response at
1 KiB, rejects DTDs and unexpected requests, and logs only booleans/counts.
Its private 0600 configuration is temporary and removed after the session.
No embedded external endpoint is contacted; no password search is performed.

Six original synthetic protocol controls pass: matching POST, wrong identity,
malformed XML, oversized body, wrong path and GET. Generated identifiers and
responses do not appear in control logs. All three viewer sessions end with
unchanged source/copy hashes, no OOM, and removed containers. Every attempt is
retained. Source field values are absent from retained logs; the disclosed
response value is also absent from replay logs. Screenshots, viewer logs,
source fields and response values remain outside Git.

The two different error messages establish observed behavior only. They do
not identify an invalid credential, expired right, cipher implementation or
successful decryption. No content, page count or recovered output is claimed
for the protected source. Actual wrapping, credentials and whole-document
recovery remain open in #501/#415.

## Converter results and continued search

The same frozen CLI/WASM artifacts from reviewed Rust commit
`7c13b4052dc7a20fa143c710cfba572d1543e2ab` (merged as `d2bf82e8`) reject the
unchanged attachment at byte 1,889,611: the suffix is not a recognized CAJ
footer. Native publishes no PDF. Node and a real Chromium DedicatedWorker
both report `AMBIGUOUS_PDF_REPAIR` with zero output bytes; the browser's final
OPFS inventory is empty. Original hashes remain unchanged. These are expected
refusal/cleanup checks, not conversion compatibility passes. Recognizing the
footer alone would not supply the missing TTKN handler or key derivation.

The public-web search also continues the previous Nanjing University frontier:
300 additional observed pages all return HTTP 200, with no further CAJ-family
or archive attachment links. The combined crawl has visited 700 pages;
201 discovered URLs remain unvisited at this pass's cap. A targeted Wayback
CDX lookup for a previously observed Shenzhen University attachment times out;
the exact historical-URL availability request returns HTTP 429. No additional
Wayback document is acquired, and no absence of snapshots is inferred. These
failures are preserved separately from the earlier requests. Internet Archive
item-file downloads in the previous 87-original cohort remain a separate
successful acquisition path. Search-engine results continue to yield mostly
reader/help pages; they are not counted as acquired samples.

## Reproduction and provenance

The source URL/hash and complete structural inventory are in the JSON. Reuse
`research/scripts/ttkn_inventory.py` from samples commit `c3d14a9`, with the
external source path and pinned SHA-256. Runtime artifacts and all original
external driver hashes are pinned in the receipt. The viewer protocol uses
the existing original `414-viewer` start/UI apparatus and the containment,
input modification and timed observations described above. Repeat experiments
must preserve attempts and distinguish originals from diagnostic copies.

Research scripts use original MIT code and bounded reads; the replay streams
its source prefix in 64 KiB chunks. No vendor implementation, font program,
foreign converter or private HN/JBIG source is inspected or migrated. Only
original MIT prose and metadata enter this change; there is no production
code, dependency, API, CLI, JavaScript, output, memory or supported-format change.
No release is proposed.

The catalog now has **1,385 identities: 1,339 conversion PASS, 19 FAIL and
27 UNSUPPORTED**. Accepted pages remain 36,288. The previous 1,384 rows and
revision-scoped outcomes are unchanged, including seven source-content warning
cases that are not full compatibility passes. This report adds one unresolved
protected input, not a recovered or proven unavoidable exception; #406 and
its other correctness/fidelity obligations remain open.
