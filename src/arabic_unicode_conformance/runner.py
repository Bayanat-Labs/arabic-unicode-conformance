# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Run one adapter over the suite and record one observation per (pipeline, case)."""
from __future__ import annotations

import platform
import time
import unicodedata

from . import __version__
from .suite import case_bytes, case_text, load_cases


def judge(case, policy, output, error):
    """pass / fail for one output against the case's expectation under `policy`."""
    if case["expected_error"]:
        return "pass" if error is not None else "fail"
    if error is not None:
        return "fail"
    return "pass" if output == case["expected"][policy] else "fail"


def run_adapter(adapter, cases=None):
    cases = cases if cases is not None else load_cases()
    by_id = {c["case_id"]: c for c in cases}
    requests, skipped = [], []
    for c in cases:
        for p in adapter.pipelines:
            if c["input_kind"] == "utf8_bytes":
                if adapter.accepts_bytes:
                    requests.append({"id": c["case_id"], "pipeline": p.id, "bytes_hex": case_bytes(c).hex()})
                else:
                    skipped.append((c["case_id"], p))
            else:
                requests.append({"id": c["case_id"], "pipeline": p.id, "text": case_text(c)})
    started = time.time()
    first = adapter.run(requests)
    # Second pass on every text output, for the idempotence check.
    again = [{"id": cid, "pipeline": pid, "text": out} for (cid, pid), (out, err) in first.items() if out is not None]
    second = adapter.run(again) if again else {}
    elapsed = time.time() - started
    pipes = {p.id: p for p in adapter.pipelines}
    obs = []
    for (cid, pid), (out, err) in sorted(first.items()):
        c, p = by_id[cid], pipes[pid]
        rec = {"pipeline": pid, "case_id": cid, "category": c["category"], "level": c["level"], "policy": p.policy,
               "relation": p.relation, "output": out, "error": err, "status": judge(c, p.policy, out, err)}
        if out is not None:
            out2, err2 = second.get((cid, pid), (None, "missing"))
            rec["idempotent"] = err2 is None and out2 == out
            # Not applicable when the output holds a lone surrogate (the NFC and NFKC policies pass them through).
            rec["output_nfc"] = None if any(0xD800 <= ord(ch) <= 0xDFFF for ch in out) else unicodedata.is_normalized("NFC", out)
            keep = [chr(int(cp[2:], 16)) for cp in c["must_preserve"]]
            rec["must_preserve_kept"] = all(ch in out for ch in keep) if keep else None
        obs.append(rec)
    for cid, p in skipped:
        c = by_id[cid]
        obs.append({"pipeline": p.id, "case_id": cid, "category": c["category"], "level": c["level"], "policy": p.policy,
                    "relation": p.relation, "output": None, "error": None, "status": "n/a"})
    run = {"adapter": adapter.name, "label": adapter.label, "versions": adapter.version(),
           "pipelines": [{"id": p.id, "policy": p.policy, "relation": p.relation, "call": p.call} for p in adapter.pipelines],
           "runner": "arabic-unicode-conformance %s" % __version__, "runner_python": platform.python_version(),
           "runner_unicodedata": unicodedata.unidata_version, "platform": platform.platform(terse=True),
           "cases": len(cases), "seconds": round(elapsed, 2)}
    return run, obs
