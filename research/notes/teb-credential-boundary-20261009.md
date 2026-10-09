# TEB certificate and opaque-field boundary

This continues [Rust #468](https://github.com/rwv/caj2pdf-rust/issues/468),
following the [container/damaged-tail report](teb-container-boundary-20261009.md).
The eight complete sources contain parseable X.509 certificates with RSA public
keys. They do not supply an established content-decoding recipe. No TEB source
is newly recovered and no general impossibility or credential-availability
claim is made.

The [per-source receipt](teb-credential-boundary-20261009.json), SHA-256
`4f3ac3d5205f9240c604abfcbee8fac39bd35d510fa538bd929a2001bef7d830`,
records unchanged source identities, structural checks, literal payload scans
and a specific negative public-operation hypothesis. The ninth source retains
its verified missing-directory/zero-tail status; its unavailable rights fields
are explicitly NOT_CHECKED. No source identity is substituted.

## Certificate and field observations

The inner `protect/auth/permit/cert/cert` text uses `CERTIFICATE` armor,
not a private-key container. Removing the armor yields DER that OpenSSL parses
as X.509 and emits byte-identically. This also rejects extra trailing bytes
that a permissive certificate reader might otherwise ignore.

| Measured field | Result on all eight complete sources |
| --- | --- |
| Certificate | Seven share one 564-byte DER certificate; the later source has a different 565-byte certificate |
| Public key | Two distinct RSA public keys, each 1,024 bits with exponent 65,537; the two distinct moduli have GCD 1 |
| `file-app` | Canonical base64, 80 decoded bytes |
| `password` | Canonical base64, 128 decoded bytes; the big-endian integer is below its certificate's modulus |
| `iv` | Canonical base64, 32 decoded bytes |
| `rights` | Canonical base64, 496 decoded bytes |

Each of those four decoded fields has eight distinct values across the cohort.
No values, certificate identities/subjects, key integers or rights URLs enter
this report. Parsing the certificate's public key does not validate its
signature, trust, validity, ownership or authorization. A certificate is not
itself a demonstrated document credential. Field names and encoded lengths
also do not establish the cipher, derivation or relationship between fields.

The standard interpretation of certificate armor and public-key structure
comes from [RFC 7468](https://www.rfc-editor.org/rfc/rfc7468) and
[RFC 5280](https://www.rfc-editor.org/rfc/rfc5280). Installed OpenSSL's
[x509](https://docs.openssl.org/3.5/man1/openssl-x509/) and
[pkey](https://docs.openssl.org/3.5/man1/openssl-pkey/) commands are used only
for local structural parsing, not network verification.

## Explicit hypotheses and their limits

For each 128-byte `password` field, an independently written bounded probe
applies the RSA public primitive with that source's certificate key and checks
the resulting 128 bytes for the tested type-1/type-2 padding shapes: leading
zero/type byte, at least eight padding bytes, delimiter, and type-1 all-FF
padding. Neither shape matches on any of the eight sources. No suffix or
candidate key bytes are exported. Original private-operation controls produce
both positive shapes and reject adjacent malformed cases, so the check is not
an always-failing parser.

This tests a direct publicly recoverable-block hypothesis. It does not show
that the field is necessarily RSA ciphertext, identify a required private key,
exclude another wrapping scheme or establish irrecoverability. The primitive
and padding terminology come from [RFC 8017](https://www.rfc-editor.org/rfc/rfc8017);
no standard's implementation code or private/vendor converter was copied.
The GCD observation is a two-key structural comparison, not a security audit.

All **61,126,169 bytes** of the eight declared-PDF payloads were also scanned
sequentially for literal `%PDF-`, ` obj`, `endobj`, `stream`, `%%EOF`, `/Type`
and ZIP-local-header tokens. None occur. Their lengths modulo 16 are 9, 3, 3,
2, 14, 10, 1 and 15 in receipt order. This is not enough to name an algorithm:
additional framing, transformations or compression remain possible. Absence
of recognizable syntax is not proof of encryption or missing credentials.

An inspected primary publication,
[CN104866983A](https://patents.google.com/patent/CN104866983A/zh), describes
compiling PDF content into TEB using DRM protection. It gives no byte-level
wrapping/key recipe applicable to these samples. Other inspected searches
for the wrapper markers and TEB/RSA descriptions did not establish such a
recipe; this is a scoped search result, not global absence of documentation.
No legal or patent-status conclusion is drawn.

## Bounds, controls and provenance

[`teb_credentials.py`](../scripts/teb_credentials.py) is original MIT research
code using the existing measured container checker, Python standard library
and installed OpenSSL CLI. It parses bounded metadata and streams payloads in
64 KiB chunks. Source size is capped at 512 MiB, XML at 64 KiB/128 elements,
DER at 8 KiB, each OpenSSL command at ten seconds, and accepted stdout at
128 KiB. The sequential report process and child commands inherit a 512 MiB
address-space cap. Python VmHWM is 17,272 KiB and VmPeak 29,740 KiB; these are
parent-process measurements, not a combined child peak. Python 3.13.5 and
OpenSSL 3.5.7 are pinned in the receipt.

Six [original test groups](../conformance/test_teb_credentials.py) cover:

- A complete original container, real generated certificate, CLI operation and
  absence of field/certificate values in output.
- Independent private-operation controls for both public padding shapes,
  malformed neighbors and invalid range/size/exponent inputs.
- Wrong/duplicated armor, trailing DER bytes, command refusal and timeout redaction.
- Noncanonical base64, wrong decoded sizes and ambiguous/missing XML fields.
- Every token split across the 64 KiB boundary, exact scan extents and short or
  oversized reads.

The generated control private key is temporary, original and never printed or
committed. All **109 selected Catalog tests pass with zero skips**. Review
adds an explicit scan-extent bound; the affected controls and all eight complete
sources rerun after that change. Earlier exploratory assumptions remain in the
receipt. The original single-base64 probe rejected the certificate text because
it still contained public armor; that attempt is retained.

No source document, decoded XML/credential value, font, pixel or derived PDF
is committed. There is no production dependency, parser, API, memory-bound,
conversion-output or release change. Previous #470 native/Node/Chromium refusal
evidence remains historical; it is not relabeled as a fresh runtime sweep.

The actual content wrapping, key derivation, validated credential requirements
and whole-document recovery remain open under #468. The corpus stays at
**1,252 conversion PASS / 18 FAIL / 27 UNSUPPORTED**, 35,587 accepted pages.
This narrows the available evidence; it does not complete #468 or #406.
