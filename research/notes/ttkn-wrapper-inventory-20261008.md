# TTKN wrapper inventory, 2026-10-08

Research for [caj2pdf-rust #415](https://github.com/rwv/caj2pdf-rust/issues/415).
All 16 unchanged originals have a live custom encryption dictionary. None is
newly converted or proved irrecoverable. The [per-source receipt](ttkn-wrapper-inventory-20261008.json)
pins origins, hashes, PDF extents, xref-selected encryption objects, XML
structure, tool versions and scoped offline viewer observations. This satisfies
the inventory criterion; wrapper/key semantics, recovery and exception proof
remain open.

## Measured PDF profile

The new original MIT [inventory tool](../scripts/ttkn_inventory.py) follows each
actual `startxref`, reads the classic xref entries sequentially and verifies the
live encryption object's identity. All 16 logical PDF hashes independently
match the earlier extracted prefixes. Fresh qpdf 12.2.0 checks of those exact
prefixes reject the encryption filter. The complete reviewed #457 corpus run
also retains all 16 as FAIL; no status is promoted by these observations.

All 16 dictionaries have the same profile: `TTKN.PubSec`, `TTKN.PubSec.s1`,
`Length=40`, `R=2`, `V=2`, `EncryptMetadata=true`, with both string and stream
filters selecting `DefaultCryptFilter`. That filter declares `CFM=AESV2` and
one eight-byte recipient, the fixed marker `AppendCA`. It is not a PKCS#7
recipient envelope. The dictionary contains no actual recipient certificate,
encrypted recipient key or permissions envelope in that field.

[ISO 32000-1:2008](https://raw.githubusercontent.com/adobe/dc-acrobat-sdk-docs/master/docs/standards/pdfstandards/pdf/PDF32000_2008.pdf)
§§7.6.2, 7.6.4–7.6.5 distinguish handler selection, public-key recipients and
crypt filters. Standard public-key access requires the matching private key;
the standardized SubFilter values and recipient envelopes differ from these
sources. `AESV2` alone does not specify this custom handler's key derivation or
rights-wrapper processing. Rewriting its name to an Adobe or Standard handler,
or dropping the live Encrypt reference, is not an established recovery.

The earlier footer-reconstruction probe that reported Standard R2 remains an
invalid interpretation, not evidence of an empty password. The new inventory
does not use that reconstructed dictionary.

## Two rights-wrapper families

Each logical PDF is followed by `WebFastLoad` and NUL, XML `right-meta`, a
`startrights` record and sometimes HTML residue. The declared offset agrees
with the observed XML start in every source. Declared lengths are not reliable
XML extents: nine pairs are actual/declared 5,607/5,609; three 5,667/5,609; two
5,671/5,613; two 1,459/1,459. The tool measures through the closing XML element
and records both lengths, without altering the source or following any URL.

| Family | Sources | Available structure |
| --- | ---: | --- |
| Embedded certificate and opaque PFX | 14 | PEM X.509 RSA public certificate, 1,024-bit key, SHA-1-with-RSA certificate signature OID; base64 password field decodes to 128 bytes; PFX decodes to 2,248 bytes in 12 sources and 2,252 in two; IV field decodes to 32 bytes; rights field to 640 bytes. |
| Server/authentication wrapper | 2 | `server/url` and password fields; no certificate or PFX field; password decodes to 48 bytes, IV to 32, rights to 704. The identities start `d6599518310e` and `e4a1064cb83e`. |

Certificate parsing establishes public-key structure, not private-key
availability, trust or current certificate validity. The field named password
is not established plaintext. The decoded PFX bytes do not start with the
ASN.1 sequence required by [PKCS#12, RFC 7292 §4](https://www.rfc-editor.org/rfc/rfc7292.html#section-4),
and are not another ASCII-base64 wrapper. The prior OpenSSL 3.5.7 structural
probe rejects all 14 before a meaningful password check; the receipt preserves
those diagnostics without credential values.

One additional narrow hypothesis was tested offline: whether the 128-byte
password field is a PKCS#1 v1.5 signature block recoverable with the embedded
public key. All 14 reject that interpretation. An original generated RSA
signature is accepted and its single-bit mutation is rejected by the same
operation. This does not identify an encryption algorithm or prove that a
usable credential cannot be recovered by another documented mechanism.

The fixed eight-byte marker also lacks the envelope structure described by
[PKCS#7, RFC 2315 §§7 and 10](https://www.rfc-editor.org/rfc/rfc2315.html).
The tested standard interpretations therefore do not establish TTKN semantics.
Public searches for the exact handler names did not locate an authoritative
TTKN wrapper specification in the consulted results. This is a search limit,
not a claim that no specification exists. No foreign converter or vendor
implementation source was read or copied.

## Offline viewer observations

Three originals were opened in separate fresh sessions of the pinned viewer:
`868dfadd1cc5` (2,248-byte PFX), `fa994a734d33` (2,252-byte PFX), and
`d6599518310e` (no PFX). Each showed a modal red-cross error and no document tab
or page. Some message glyphs are unavailable in the viewer font environment,
so the error cause is not inferred. A fourth fresh session opened the known
unencrypted #456 PDF, visibly showing its title page and 1/78 page indicator.

Captures at 5, 10, 20 and 25 seconds are retained externally; every 20/25-second
full-frame pair is identical and all four final frames were visually examined.
The receipt records image hashes, source integrity, memory peaks and cleanup.
Containers used no network, read-only root/input mounts, user 1000, dropped
capabilities, no-new-privileges, 2 GiB memory/swap, two CPUs, 256 PIDs and a
90-second hard limit. No OOM occurred; all containers were removed and verified
absent. No credential was supplied or endpoint contacted.

These are three scoped open failures, not pixel comparisons or evidence that
network access/credentials are necessarily the sole missing condition. The
other 13 TTKN originals are viewer NOT_RUN, and general viewer-readiness issue
[#441](https://github.com/rwv/caj2pdf-rust/issues/441) remains open.

## Reproduction and remaining work

Use Python 3.11+, pikepdf 10.5.1 and cryptography 44.0.3 as external research
tools. The tool adds no converter dependency. Source files must be outside Git,
named `<sha256>.caj`; use the 16 full identities in the JSON receipt:

```sh
python3 research/scripts/ttkn_inventory.py --source-dir /external/documents \
  --catalog catalog.json --sha256 SOURCE_SHA256
python3 -m unittest discover -s research/conformance -p test_ttkn_inventory.py -v
```

Repeat `--sha256` for multiple identities. Six original synthetic test groups
pass, covering identity/xref selection, exact PDF boundaries, conflicting
trailers, unproved revisions, unknown handlers/recipients, XML/value redaction
and resource limits. The script caps reads/tail/XML at 64 KiB, object values at
4 KiB, xref entries at 100,000 and XML elements at 64. Each source is hashed
before and after inspection. Initial development refusals are retained in the
receipt; all 16 were rerun after simplifying the line-boundary handling and
completing the measured tag allowlist.

For both families, the next required evidence is the custom wrapper's actual
semantics, the mapping from `AppendCA` to key material, validated credential
unwrapping and file-key derivation. The embedded family additionally needs the
PFX/password/IV/rights wrapping rules; the server family needs the documented
authentication mechanism and an available credential source. Their absence
from this investigation is not proof of absence from the source ecosystem.
Whole-document recovery and independent content/runtime verification remain
unmet. No production recovery, API/support change or release is justified by
this inventory. No document, XML value, certificate, key, password, PFX, pixel
or font bytes are committed.
