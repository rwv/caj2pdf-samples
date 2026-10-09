# Historical Windows CAA observations

This completes the bounded offline investigation in
[#79](https://github.com/rwv/caj2pdf-samples/issues/79), supporting
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406).
The [metadata receipt](caa-windows-boundary-20261009.json) records all 18
unchanged originals, controls, attempts and environment limits. It adds no
successful conversion: the corpus remains **1,252 PASS / 18 FAIL / 27
UNSUPPORTED**, 1,297 identities and 35,587 accepted pages.

## What the evidence establishes

The [Wuhan Textile University library FAQ](https://lib.wtu.edu.cn/info/5663/7723.htm)
dated 2017-07-27 describes CAA as a link used through an Internet-connected
CAJViewer. The vendor-authored
[KNS3.5 manual](https://staatsbibliothek-berlin.de/fileadmin/user_upload/zentrale_Seiten/ostasienabteilung/pdf/UserGuide35.pdf)
and [institution-hosted guide](https://www.ckgsb.edu.cn/uploads/report/file/201602/01/1454297297921320.pdf)
list CAA among viewer formats and describe online reading. These establish
historical product behavior, not a byte-level recipe for opaque CAA fields or
the present availability of any specific target.

Under the frozen offline Windows-viewer protocol, all 18 originals produce
visible static controls containing the fixed **network, server and error**
keywords at 10, 30 and 60 seconds. An independently authored invalid `.caa`
instead produces CAA-information/open-file-error dialogs without the network
keyword. This is stronger evidence of historical CAA handling than the
[previous Linux 9 refusal](caa-nh-discovery-20261008.md), and supports a
distinction between target descriptors and locally available document pages.
The observer records keyword presence, not the complete error message, its
parameters or a decoded target. It does not establish a successful request.

No referenced endpoint is contacted. These observations do **not** prove that
the referenced document is lost, that a particular credential is required, or
that a native Windows installation would give the same result. Correct offline
conversion still requires the actual document; an unsupported CAA result is
not an irrecoverability verdict. The existing native/Node/Chromium expected
refusals remain separate from successful conversions.

## Installer and compatibility environment

The vendor's [download metadata](https://cajviewer.cnki.net/caj9.0/config/indexExe.js),
linked by its [older-versions page](https://cajviewer.cnki.net/caj9.0/downloadMore.html),
identifies CAJViewer 7.3.151 Lite. Its official
[installer](https://download.cnki.net/cajPackage/CAJWinPackage/CAJViewer_7.3.151.Simple.self.exe)
is 66,352,960 bytes, SHA-256
`92fd901042785cd6c8991bec73f7c2edb22b3a7989a7625dc635b07d0f2f0f84`.
All 64 byte ranges have matching total size, Content-Range and ETag; a second
sequential comparison verifies every assembled byte. Of 125 range attempts,
61 failed and remain recorded. Partial downloads and HTML responses were never
executed. This is official-source transport evidence, not a digital-signature
attestation.

The runtime is Debian 12 x86_64 with Wine 8.0 (`8.0~repack-4`), a 32-bit prefix,
Xvfb/Openbox and the recorded distribution packages. The image is
`sha256:6c9f5ec0610a7ff8bc45fe8e0a87dffd0ff17e42466c90b80237a1712847b95c`.
No vendor binary is built into that image. The installer ran separately with
networking disabled. Its complete-install option displayed an MDAC 2.7 prompt
and then an early-installation error; **a successful complete installation is
not claimed**. The unchanged executable and installed `.caa` open association
remained. That association invokes `CAJVieweru.exe` with the file path, the
same route used in the experiment. Reading this OS registration is not vendor
implementation inspection.

The original `valid_out_of_order_objects.pdf` control opens with two pages,
navigates from `1/2` to `2/2`, and displays both independently authored rectangle
shapes. A fresh clone also reports `1/2` at each frozen checkpoint. Original
outline titles were not confirmed in this Windows viewer. CJK interface pixels
have missing glyphs; Unicode text from original controls remains readable.
These controls validate the bounded opening/UI experiment, not every installed
feature, font fidelity or native-Windows compatibility. A historical
[Wine bug report](https://www.winehq.org/pipermail/wine-bugs/2013-April/351965.html)
describes a related 7.2 MDAC installation problem; it does not establish the
cause or a verified remedy for this 7.3.151 run.

The first image build failed on an invalid local-image reference; the second
failed on incompatible old-snapshot/multiarch dependencies. A fresh Debian
build and the observer-compiler extension succeeded. Download, build and
installation failures remain setup evidence, never document failures.

## Frozen observation protocol

Each of the 18 descriptor sessions and two original-control sessions starts
from a separate opaque copy of the same stopped, hash-inventoried prefix.
All original SHA-256 values and 350–404-byte sizes are checked before and after.
Original `.caa` extensions are retained under a fixed local filename; 16 files
declare NH and two KDH. No field value is decoded or exported.

Containers use `--network none`, a read-only root/input, UID/GID 1000,
`--cap-drop ALL`, `no-new-privileges`, 2 GiB memory, two CPUs, 256 PIDs,
bounded temporary filesystems and a 125-second lifetime. An outer 140-second
timeout also removes the container. After display readiness and a bounded
Wine warmup, the unmodified viewer opens the input. Observations occur at
10, 30 and 60 seconds after launch. No retry replaces a source outcome.
Viewer stdout/stderr are discarded. Containers and writable prefix copies
are removed after each attempt; no viewer-generated target caches are kept.

An original MIT observer uses documented
[EnumWindows](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows),
EnumChildWindows and
[WM_GETTEXT](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-gettext)
messages, with at most 256 visible records, 1,024 UTF-16 units per bounded
message and a 100 ms message timeout. Its process has a separate 12-second
limit. The descriptor build reads only static/button/dialog text and exports
geometry, fixed class categories and fixed keyword labels. It omits all
captions, arbitrary control text and editable values. No CAA screenshots are
taken; the full-text build is mounted only for independently authored controls.
The original synthetic network-error control contains a URL and unique marker:
expected keywords are observed while neither value appears in the output.

The 20 frozen sessions finish without an outer timeout, probe failure or OOM;
all 54 descriptor snapshots contain the recorded network/server/error keyword
combination. The receipt keeps per-input results and exact external artifact
identities. These are UI observations, not 18 new conversion failures or passes.

## Provenance and remaining work

Research notes, drivers and controls are original MIT work. Only normal opaque
installation/execution, public Win32 UI messages, installed file-association
metadata and public download configuration were observed. No vendor code,
font program/outline, foreign converter or private HN/JBIG implementation was
inspected, copied or migrated. Installer, document, descriptor, font, PDF and
pixel bodies remain external; no third-party redistribution is implied.

This closes the scoped historical offline-observation question. Obtaining
authorized actual documents, verifying current remote availability or needed
credentials, and native-Windows equivalence remain unverified. No resolver or
converter change is proposed. Rust #406, viewer readiness and the other source
correctness obligations remain open; no release is requested.
