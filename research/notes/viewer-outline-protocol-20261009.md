# Displayed-contents observation protocol (2026-10-09)

[Samples #63](https://github.com/rwv/caj2pdf-samples/issues/63) checks the
available contents panel of each original in the existing 849-source C8/HN-B
inventory. It addresses the observation gap in
[Rust #303](https://github.com/rwv/caj2pdf-rust/issues/303), under
[Rust #406](https://github.com/rwv/caj2pdf-rust/issues/406). This protocol does
not implement a stored-outline format or validate document rendering.

## Public interface and bounds

The original Linux x86-64/Qt5 observer wraps the public static
`QApplication::exec` and `QCoreApplication::exec`, forwarding both to their
original entry points. A single GUI-thread timer samples at one-second
intervals, at most 60 times. It enumerates at most 8,192 widgets and 64 trees;
each first-column model traversal is capped at 10,000 nodes and depth 128.
It walks collapsed children as well as expanded nodes. `canFetchMore`, a
non-default root, invalid indexes and every enumeration limit remain explicit.
The observer never calls `fetchMore`, reads item text or private roles, or
changes a model. A stop file stops only its own timer and writes an acknowledgement.

Observations contain public model/widget class names, a hash of the widget
name, visibility and geometry, node/root counts, depth, PID, tick and host
monotonic timestamp. The observer also records numeric page indicators in the
top toolbar and counts visible left-panel labels equal to the measured empty
contents caption. It exports no title or font program. JSON records are
bounded to 2,048 bytes; failed logging exits 126, a missing forwarded symbol
exits 125. The Python reader caps traces at 8 MiB/4,000 records.

## Fixed real-source protocol

The runner verifies every manifest SHA-256, variant and declared page count
before starting any session. It uses the existing independent header parser,
limits manifests to 1,000 inputs/1 MiB and individual files to 512 MiB, and
requires a new output directory outside the checkout. Every source receives a
fresh process and read-only copy, with hashes checked before and after.

The externally supplied image is pinned by digest, never downloaded by this
runner. Each container has network disabled, read-only root/input, uid 1000,
all capabilities dropped, no-new-privileges, 2 GiB memory/swap, two CPUs,
256 PIDs, a 64 MiB file-size limit and a 90-second lifetime. Output and small
temporary mounts are separate. Fixed worker choices are 1, 2, 4 or 6. An
unconfirmed container removal cancels queued captures; already-running
captures finish their cleanup. Failures are retained without automatic retry.

The X11 desktop is 1600×1200 at 96 dpi, with the supplied Noto Sans CJK UI
font. After five seconds the runner captures startup, maximizes, waits two
seconds and captures again. It selects the contents tab only if the measured
tree is not already visible; clicking an already selected tab would hide it.
It moves the pointer away, waits five seconds and captures contents A, then
waits ten seconds for B and five seconds for C. Commands and screenshots have
host monotonic timestamps and hashes. Startup and all three contents frames
remain external, including a frame whose validation fails.

Each checkpoint uses the latest complete timer sample before its screenshot,
at most three seconds old. It never falls back to an earlier matching sample.
The receipt requires one visible measured `QTreeWidget`/`QTreeModel`, its
default root, measured contents-panel geometry, no lazy/invalid/limited state,
and the first-page indicator with the source's declared total. An empty model
must have the visible empty-contents caption; a populated model must not.
The three distinct checkpoint samples and every intervening consecutive tick
must agree. The final trace is hashed only after the observer acknowledges
stopping its timer. Input integrity, live container state, no OOM, memory peak
and removal are required separately.

Results are `EMPTY_DISPLAYED`, `NONEMPTY_DISPLAYED` or `NOT_CONFIRMED`.
These are observations of this viewer and finite interval, not conversion
passes. Empty displayed contents do not exclude an unknown stored layout,
later asynchronous changes, or behavior in another viewer version. A future
positive C8/HN-B source still needs the independent layout/mutation work in
#303. This probe does not resolve raster readiness, source fonts or ornaments.

## Reproduction and original controls

```sh
c++ -std=c++17 -shared -fPIC -O2 -Wall -Wextra -Werror -DQT_NO_VERSION_TAGGING \
  research/cajviewer/qtree_observe.cpp -ldl -o /external/tree-observer.so \
  $(pkg-config --cflags --libs Qt5Widgets)
python3 research/cajviewer/outline_capture.py \
  /external/manifest.json /external/documents /external/new-outlines \
  --observer /external/tree-observer.so \
  --ui-font /external/NotoSansCJK-Regular.ttc \
  --image sha256:cb5049d3448b6d5bcfd371cf195d522d637869dce075cb1650d74198875171de \
  --workers 6
python3 -m unittest discover -s research/conformance -p 'test_qtree_observe.py' -v
python3 -m unittest discover -s research/conformance -p 'test_outline_capture.py' -v
```

Each manifest row has `source_sha256`, `variant` (`C8` or `HN-B`) and `pages`;
an optional `source_id` is carried through. Input paths are `<sha256>.caj`.
The tools require Python 3.11+, Pillow, Docker/X11 helpers in the already
supplied viewer image and public Qt5 development libraries to compile.
CI installs only distro Qt development libraries and original test dependencies;
it requires neither the viewer nor external documents.

The original Qt controls exercise a delayed empty-to-six-node nested model,
empty/lazy/deep/wide/invalid models, requested stop and excessive tree count.
They compare lazy fetch calls with an unobserved Qt baseline: Qt's own view can
request rows, so zero total fetch calls is not a valid observer assertion.
The initial zero-fetch assertion failed and was corrected on that basis.
Original Python controls exercise hidden/wrong/ambiguous/stale receipts,
malformed/oversized logs, independently generated HN-B header/hash checks,
duplicates, changed inputs, OOM and cleanup failure. These are tool controls,
not compatibility passes.

## Provenance

All added source is original MIT work. The observer uses public Qt5 headers
from Debian `qtbase5-dev` 5.15.15; relevant header SHA-256 values are:

| Header | SHA-256 |
| --- | --- |
| `QtWidgets/qapplication.h` | `885d342b20ffef565acc453a18cea2a4f1babe2bf44b694250980fe12df9bd52` |
| `QtWidgets/qtreeview.h` | `7478cb63625eabe9cb65ff719c7842153bad946bbc0e20c105c86cabaf04e0da` |
| `QtCore/qabstractitemmodel.h` | `cb9ae10a61b803605085d5062a3e8efc3adaed47080359eeb449da74c80814c5` |

Current official documentation describes the public
[model](https://doc.qt.io/qt-6/qabstractitemmodel.html) and
[tree-view](https://doc.qt.io/qt-6/qtreeview.html) concepts; Qt6 documentation is
not the Qt5 ABI authority. No vendor implementation, foreign converter,
private HN/JBIG module or font program/outline was inspected or migrated.
Documents, generated controls, screenshots, logs, fonts and binaries remain
external. Metadata receipts may publish counts and hashes only.

The initial original-model run in the viewer image failed before executing
its test because the image supplies only the X11 platform plugin. The corrected
Xvfb control observes zero then six nodes. Independent real-source calibration
observes the known HN-A example's 81 nodes/root count 13/depth 3 and an empty
C8 model. Those preliminary attempts remain distinct from the final tool's
three-source pilot and full sweep. The full sweep is bracketed by fresh runs
of the known 132-page HN-A example. A report must retain all failures, source
and tool identities, both bracket controls and all 849 per-input outcomes
before claiming complete observation coverage.
