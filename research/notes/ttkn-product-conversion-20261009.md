# Explicit-response TTKN product conversion

The unchanged public source SHA-256
`074cb4d57181e92826c37b549f811008c58c7b66366f9045e8985c58178263d8`
now converts through the Rust product with its explicitly supplied matching
response. The [receipt](ttkn-product-conversion-20261009.json) pins original
control hashes, the reviewed product revision/artifacts and independent checks.
The [previous observed-IV report](ttkn-unaltered-wrapper-20261009.md) remains
historical evidence; its unresolved-initializer and production-refusal limits
are superseded for this profile only.

## Original initializer proof

Two wholly authored negative wrappers varied their file identifiers, responses,
seeds, IVs and XML, using an all-zero first-layer IV. Both public-API observations
used the same different 16-byte initializer. Independently applying AES to each
known control derived that same initializer from the first plaintext block;
only the first plaintext block differed from the zero-IV control. The format
constant is `200CFC8299B84aa9`, in ASCII. It is not a source-specific response,
IV or key.

A third entirely authored PDF used the measured initializer and displayed its
text, red/blue rectangles and outline in the isolated offline viewer. Both
wrapper plaintexts matched the original generator exactly. The positive PDF,
response and expected content are MIT test data in the
[reviewed product fixture directory](https://github.com/rwv/caj2pdf-rust/tree/f0cea0e715cdab70282199140dbe7b396b3651b1/crates/caj2pdf-core/tests/fixtures/ttkn).
Its OpenSSL-based generator also reproduces the first two negative input
hashes. No external document field or credential was used to invent these
controls. No vendor/converter implementation was read or translated.

The [product profile](https://github.com/rwv/caj2pdf-rust/blob/f0cea0e715cdab70282199140dbe7b396b3651b1/docs/ttkn-pdf.md)
records exact raw-XML hashing, CBC modes, ASCII key inputs and the standard
PDF AESV2 object-key rule. The response is supplied by the caller; production
code does not fetch or resolve embedded targets.

## Unchanged original-input checks

The source remains 1,891,106 bytes. Its matching response was deliberately
published by its author in the [original discussion](https://chaoli.club/index.php/2979/5)
and bound to this source before testing. Response values, document-specific
metadata, decrypted document bytes and credentials are not published here.
The response file used by the native CLI was temporary and removed after the
bounded run. The product used no live viewer or API observer.

Native CLI, Node and actual headless Chromium produce identical PDF bytes,
SHA-256 `c8e4e9dd1c377a8c704291ea4e8d2864fcf322c19e2fbf915a793fb5b5320a94`.
Qpdf exits zero without warnings. Every one of the 234 plaintext stream byte
sequences agrees with independent qpdf recovery. Every one of the 180 pages
matches in boxes, rotation, word positions and 72-dpi MuPDF pixels; all 97
outline entries and destinations agree. The existing identical duplicate
MediaBox repair still applies. The newly supported indirect local GoTo
references are preserved and validated, as tracked by Rust #505.

Wrong/missing responses in the original-input Node and Chromium runs fail
before any sink write or flush. The unchanged original also refuses in the
native CLI without leaving output or staged files. Required original MIT tests additionally cover Node
refusals, malformed/case-changed responses, CLI staged-output removal and
response-file overwrite protection, short reads, single-byte I/O chunks,
XML/crypto/bounds/cancellation errors and nonlocal/chained outline actions.
Failed development and harness attempts are retained in the receipt; they
are not counted as passes.

## Scope

This is a conversion pass with an explicit matching response. It is not a
claim that the file converts without credentials or that other TTKN profiles
are supported. Vendor-viewer evidence remains scoped to opening, page 1,
the 180-page counter and populated contents. The all-page comparison above
is against independent research recovery, not 180 vendor screenshots.

Rust [#506](https://github.com/rwv/caj2pdf-rust/pull/506) merged as
`a2e2ccbb56db780bbba29eb1363eea0c4e506b85`, with the same Git tree as the
reviewed revision and all 60 CI checks passing. An initial package-download
timeout and the subsequent failed-job retry remain documented in the receipt.
Only this sample's conversion row changes. The
other 1,384 rows keep their earlier revision-scoped evidence. The resulting
catalog contains 1,385 identities: 1,340 conversion PASS, 18 FAIL and
27 UNSUPPORTED, adding 180 verified pages. Adding these to the prior report's
36,288 pages yields a reported total of 36,468; this is not a fresh full-catalog
recount. Catalog `page_count` fields are incomplete: their explicit successful-
row sum changes from 34,535 to 34,715. The 54 absent fields account for 1,753 additional pages, independently
reconciled across native/Node/browser in the prior runtime receipt. The new
receipt keeps the catalog sum and reconciled total distinct.
There is no full-catalog rerun,
no newly established irrecoverable exception and no release. Other TTKN,
TEB/CAA, damaged sources and the broader fidelity criteria remain open.
