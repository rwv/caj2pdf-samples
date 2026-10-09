<!-- SPDX-License-Identifier: MIT -->

# TTKN research recovery reproduces the wrapper and all 234 PDF streams

The public attachment from [the author's research post](https://chaoli.club/index.php/2979/5)
now opens in the isolated Linux viewer with its author-disclosed response.
The source stays byte-identical. The first page renders, the counter shows
180 pages, and the contents pane is populated. This supersedes the earlier
response-validity uncertainty for this specific replay, but **production
conversion still fails**. External research recovery now preserves all 234
stream byte sequences, renders all 180 pages and retains 97 valid outline
entries. Its first wrapping IV was obtained through public API observation;
recovery solely from independently understood input fields is not yet established.
See [samples #87](https://github.com/rwv/caj2pdf-samples/issues/87),
[Rust #501](https://github.com/rwv/caj2pdf-rust/issues/501), and the
[value-redacted receipt](ttkn-unaltered-wrapper-20261009.json).

## Why the earlier diagnostic copy failed

The [previous checkpoint](public-ttkn-response-20261009.md) changed the
embedded authentication URL to loopback. That copy received the matching
response but reported a rights-file error. Public OpenSSL API observations
now establish that the original XML, including this URL, participates in
the rights decryption key. Editing the URL changes the key. The earlier
observation remains correct for its modified copy; it did not test the
unchanged source with the disclosed response.

An original MIT `connect()` interposer now redirects only the exact source
IPv4/port to an owned responder at `127.0.0.1:8123`, inside a container with
`--network none`. It preserves the HTTP path/query and every document byte.
The responder accepts only the matching request and logs booleans/counts.
Five generated routing controls pass: unmodified-network failure, matching
request success, wrong-identity refusal, wrong-path refusal and unmatched-port
failure. No external embedded endpoint is contacted and no network capability
is added. The disclosed response is used only for this matching public source.

The unchanged input is 1,891,106 bytes, SHA-256
`074cb4d57181e92826c37b549f811008c58c7b66366f9045e8985c58178263d8`.
Repeated fresh sessions show the same first page, 180-page counter and
populated contents pane. These observations establish opening, not all-page
rendering or complete outline fidelity. The catalog viewer PASS has exactly
that scope; the original offline and URL-modified failures remain recorded.

## Independently measured wrapper behavior

Original observers wrap public OpenSSL AES/SHA-256 API calls; they do not
inspect the vendor's implementation. Equality controls, observed/unobserved
output checks, bounded cross-buffer location controls and an independent
`cryptography 44.0.3` comparison support these measured rules:

1. The 48-byte decoded password field is decrypted using AES-256-CBC and
   exactly the 32 ASCII bytes of the disclosed response. Its initial 16-byte
   IV was observed privately; its initialization rule is **still unknown**.
2. The rights key is SHA-256 of the first 32 password-plaintext bytes followed
   by the original raw XML with only the rights element's base64 text removed.
   This is an exact byte operation, not generic XML canonicalization. Nine
   recorded original-source comparisons agree on all 519 bytes. The modified
   URL copy supplied 488 bytes instead.
3. That digest keys AES-256-CBC over the 704-byte decoded rights field, using
   the first 16 bytes of the decoded source IV. The result is 700 bytes of
   well-formed rights XML followed by four zero bytes. It has no PKCS#7 tail.

Using the privately observed initial IV, the independent library reproduces
all 48 password-plaintext bytes and all 704 rights-plaintext bytes exactly.
Thus two CBC layers are reproduced, but the first layer is not yet derivable
solely from independently understood format inputs. No source IV, plaintext value,
password, response, key, identifier, endpoint or rights value is published.
Temporary 0600 capture/configuration files are deleted with their containing
temporary directory. Generated controls verify those captures independently.

Earlier comparisons against source fields, six declared constant IVs, UTF-8
replacement encodings, plaintext windows and 56 additional IV derivation
candidates found no initial-IV rule. These are finite negative observations,
not proof that a derivation is absent. Each process caps comparison events at
128; later calls may be unrecorded. No complete crypto trace is claimed.

## All-stream research recovery

The rights XML has a 32-character hexadecimal `encrypt` field. Its **ASCII**
bytes, followed by the measured eight-byte `AppendCA` recipient marker, are
hashed with SHA-1; the first 16 digest bytes form the PDF file key. Standard
AESV2 object-key derivation then passes every one of 234 padding checks.
All 234 independently decrypted stream byte sequences, including trailing
bytes, exactly match the qpdf recovery as a multiset. This comparison does
not by itself establish an object-by-object graph mapping.

All 232 Flate streams reach their end. Of these, 190 have no extra bytes and
42 have one trailing whitespace byte. Those bytes remain preserved. The two
non-Flate streams are included in the byte comparison, but not mislabeled as
Flate passes. Before decryption, none of the 232 original Flate streams
completely inflates.

An explicitly modified Standard R4 diagnostic dictionary and qpdf's documented
raw-key option recover a 1,884,986-byte external PDF. Decryption exits 3 because
source object 1 repeats `/MediaBox`; both arrays are exactly `[0 0 612 792]`.
The warning is retained. The output's qpdf check exits 0. All 180 pages render
with PyMuPDF, all are nonwhite, and no MuPDF warning is recorded. All 97
outline entries have nonempty titles and in-range destinations. Pages 1, 90
and 180 were visually inspected. The two independently generated recovery
outputs have identical all-page pixels, boxes and extracted word counts.
This is not all-page equivalence with the vendor viewer.

The recipe was found through retained, limited comparisons, not a password
search. Direct hex decoding fails all 234 stream checks. A further 36 declared
combinations compared three field representations, four file-key recipes and
three object-key rules on three streams. Initially one recipe passed one
stream, while strict no-trailing-data checks rejected the other two. That
partial success was retained and investigated; the full-source follow-up
established the whitespace tails and all-stream agreement. The earlier invalid
outputs remain separate and are never counted as recovered PDFs.

An original one-page PDF control passes the same qpdf raw-key / replacement-
dictionary path, preserves its content exactly and passes qpdf check. The
PDF reference supplies the standard public-key seed/recipient and AESV2
object-key recipes; the TTKN ASCII-field adaptation above is an independent
observation of this one source. Other TTKN profiles remain unverified.

## Attempts, provenance and remaining criteria

The receipt covers 18 terminal viewer sessions from this investigation,
including the earlier URL-modified probes and the later unchanged-source
probes. Every source/copy hash remains unchanged relative to its own recorded
input; all containers are removed, no OOM is recorded, and all private mounts
are gone. Containment retains read-only root/input, UID 1000, dropped
capabilities, no new privileges, 2 GiB memory/swap, two CPUs, 256 PIDs and a
90-second deadline. Source copying uses 64 KiB chunks, XML/capture reads are
bounded, and the stream probe caps individual objects and inflation.

Retained failures include the initial observer compile/control failure,
a driver syntax error, two public-page TLS fetch failures, two overly strict
xref-header assumptions in the diagnostic script, and the failed/intermediate PDF-key
probes. None is relabeled as passing or discarded. The source's legal
same-line `xref 0 859` header now parses in the external probe.

The receipt pins original external MIT observers/drivers, control receipts,
opaque viewer image, selected captures and session cleanup evidence.
[OpenSSL public API documentation](https://docs.openssl.org/1.1.1/man3/EVP_EncryptInit/),
[cryptography documentation](https://cryptography.io/en/44.0.3/hazmat/primitives/symmetric-encryption/),
[qpdf's raw-key option](https://qpdf.readthedocs.io/en/12.2/cli.html#option-password-is-hex-key),
and the [PDF 1.6 reference](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/pdfreference1.6.pdf)
are specification/API sources. No vendor/foreign converter implementation or
private HN/JBIG source is inspected, copied or migrated. Documents, renders,
credential-bearing data and invalid diagnostic outputs remain external.
Only original MIT prose and metadata enter this change.

The collection remains **1,385 identities: 1,339 conversion PASS, 19 FAIL,
27 UNSUPPORTED and 36,288 accepted pages**. No new conversion pass is claimed.
Initial-IV initialization, complete vendor-viewer content / outline
equivalence, other TTKN profiles, and bounded native/Node/Chromium
implementation remain unmet
in #501/#415/#406. No production behavior, dependency, API, CLI, JavaScript,
output, memory policy or supported-format change is proposed. No release.
