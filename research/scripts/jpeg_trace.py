# SPDX-License-Identifier: MIT
"""Read bounded public JPEG observations and correlate exact byte/row identities.

These are value correlations, not a renderer call graph or readiness oracle.
RGB_ROWS_AT_DESTROY proves returned rows, not JPEG finish/EOI validation.
"""
from pathlib import Path
import re

COMPLETE = {"FINISH_RGB", "RGB_ROWS_AT_DESTROY"}
SHA256 = re.compile(r"[0-9a-f]{64}")


def read_trace(path):
    path = Path(path)
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("JPEG trace exceeds 16 MiB")
    events, limits, sequences = [], [], {}
    consumed = 0
    with path.open(encoding="ascii") as source:
        for ordinal, line in enumerate(iter(lambda: source.readline(513), ""), 1):
            consumed += len(line)
            if ordinal > 40000 or len(line) > 512 or consumed > 16 * 1024 * 1024:
                raise ValueError("JPEG trace record bound exceeded")
            if line == "LIMIT_EVENTS\n":
                limits.append({"line": ordinal, "kind": "LIMIT_EVENTS"})
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 18:
                raise ValueError("JPEG trace requires an explicit process namespace")
            event = {
                "line": ordinal, "sequence": int(fields[0]),
                "monotonic_ns_after_digest": int(fields[1]),
                "thread_id": int(fields[2]), "kind": fields[3],
                "context": int(fields[4]), "compressor": int(fields[5]),
                "width": int(fields[6]), "height": int(fields[7]),
                "rows": int(fields[8]), "components": int(fields[9]),
                "color": int(fields[10]), "quality": int(fields[11]),
                "dct": int(fields[12]), "sampling_hex": fields[13],
                "unit_quantizers": int(fields[14]),
                "rgb_sha256": fields[15], "encoded_sha256": fields[16],
                "process_id": int(fields[17]),
            }
            if (event["process_id"] <= 0 or event["thread_id"] <= 0
                    or event["monotonic_ns_after_digest"] <= 0
                    or not 0 <= event["sequence"] < 10000
                    or event["compressor"] not in (0, 1)
                    or event["unit_quantizers"] not in (0, 1)):
                raise ValueError("invalid JPEG observation identity")
            for name in ("rgb_sha256", "encoded_sha256"):
                if event[name] and not SHA256.fullmatch(event[name]):
                    raise ValueError("invalid JPEG observation digest")
            if event["kind"] in COMPLETE:
                w, h = event["width"], event["height"]
                if (not 200 <= w <= 4096 or not 100 <= h <= 4096
                        or w * h > 4 * 1024 * 1024 or event["rows"] != h
                        or event["components"] != 3 or event["color"] != 2
                        or not event["rgb_sha256"]
                        or (event["compressor"] and event["kind"] != "FINISH_RGB")):
                    raise ValueError("incomplete or unsupported RGB grid")
            if event["kind"].startswith("LIMIT"):
                limits.append({"line": ordinal, "kind": event["kind"]})
            sequences.setdefault(event["process_id"], []).append(event["sequence"])
            events.append(event)
    if not events:
        raise ValueError("empty JPEG trace")
    for values in sequences.values():
        if sorted(values) != list(range(len(values))):
            raise ValueError("process-local sequence gap, missing prefix or duplicate")
    return {"events": events, "limits": limits}


def matching_chains(trace, rgb_sha256, size, before_monotonic_ns):
    """Return all scoped matches; missing/limited evidence is never a match.

    Identical encoded bytes must occur in the same process, with the same
    dimensions, strictly ordered before the supplied monotonic bound.
    Multiple matching encodes are retained, without guessing which was used.
    More than 10,000 candidate pairs makes the correlation unavailable.
    """
    if trace["limits"]:
        return []
    encoders = {}
    for event in trace["events"]:
        if (event["kind"] == "FINISH_RGB" and event["compressor"]
                and event["encoded_sha256"]
                and [event["width"], event["height"]] == list(size)):
            key = event["process_id"], event["encoded_sha256"]
            encoders.setdefault(key, []).append(event)
    matches = []
    examined = 0
    for decoder in trace["events"]:
        if (decoder["kind"] not in COMPLETE or decoder["compressor"]
                or decoder["rgb_sha256"] != rgb_sha256
                or [decoder["width"], decoder["height"]] != list(size)
                or decoder["monotonic_ns_after_digest"] > before_monotonic_ns):
            continue
        key = decoder["process_id"], decoder["encoded_sha256"]
        for encoder in encoders.get(key, ()):
            examined += 1
            if examined > 10000:
                raise ValueError("JPEG correlation exceeds 10000 candidate pairs")
            if encoder["monotonic_ns_after_digest"] < decoder["monotonic_ns_after_digest"]:
                matches.append({"encoder": encoder, "decoder": decoder})
    return matches
