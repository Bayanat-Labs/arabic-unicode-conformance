#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Fill the generated sections of README.md (between <!-- BEGIN name --> and <!-- END name --> markers) with
numbers computed from the released files: src/arabic_unicode_conformance/data/*, scripts/cases_source.py and
reports/*. Run after scripts/build_suite.py and scripts/run_matrix.py:  python -I scripts/make_docs.py"""
import collections
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from arabic_unicode_conformance.suite import POLICIES, load_cases, load_policies  # noqa: E402


def stats():
    import cases_source
    cases = load_cases()
    with open(os.path.join(ROOT, "reports", "conformance_matrix.csv"), encoding="utf-8") as f:
        matrix = list(csv.DictReader(f))
    with open(os.path.join(ROOT, "reports", "runs.json"), encoding="utf-8") as f:
        runs = json.load(f)
    cats = collections.Counter(c["category"] for c in cases)
    levels = collections.Counter(c["level"] for c in cases)
    return {
        "cases": cases, "matrix": matrix, "runs": runs, "categories": cats, "levels": levels,
        "n_cases": len(cases), "n_categories": len(cats), "n_policies": len(POLICIES),
        "n_expectations": len(cases) * len(POLICIES),
        "n_text": sum(c["input_kind"] == "text" for c in cases),
        "n_bytes": sum(c["input_kind"] == "utf8_bytes" for c in cases),
        "n_surrogate": sum(c["input_has_lone_surrogate"] for c in cases),
        "n_hand": sum(len(c["x"]) for c in cases_source.CASES),
        "n_preserve": sum(bool(c["must_preserve"]) for c in cases),
        "n_langs": len({c["language_tag"] for c in cases}),
        "n_impl": len(runs), "n_pipelines": len(matrix),
        "n_conformance": sum(r["relation"] == "conformance" for r in matrix),
        "n_agreement": sum(r["relation"] == "agreement" for r in matrix),
        "n_unchanged_norm": sum(c["input_kind"] == "text" and c["expected"]["bayanat-norm-v1"] == c["input"] for c in cases),
    }


def pct(v):
    return "n/a" if v in ("", None) else "%.1f%%" % (100 * float(v))


def sections(s):
    out = {}
    out["numbers"] = "\n".join([
        "| | |", "|---|---|",
        "| Test cases | %d (%d text inputs, %d raw-byte inputs that are not valid UTF-8) |" % (s["n_cases"], s["n_text"], s["n_bytes"]),
        "| Categories | %d |" % s["n_categories"],
        "| Policies | %d (%s) |" % (s["n_policies"], ", ".join("`%s`" % p for p in POLICIES)),
        "| Expected outputs | %d (every case under every policy) |" % s["n_expectations"],
        "| Expected outputs also stated explicitly in the case source and checked against the reference implementation | %d |" % s["n_hand"],
        "| Levels | %d `must`, %d `should` |" % (s["levels"]["must"], s["levels"]["should"]),
        "| Cases with letters that must survive | %d |" % s["n_preserve"],
        "| Language tags | %d |" % s["n_langs"],
        "| Implementations in the matrix | %d (%d pipelines: %d conformance, %d agreement) |" % (s["n_impl"], s["n_pipelines"], s["n_conformance"], s["n_agreement"]),
    ])
    rows = ["| Category | Cases | must | should |", "|---|---|---|---|"]
    for cat in sorted(s["categories"]):
        cs = [c for c in s["cases"] if c["category"] == cat]
        rows.append("| `%s` | %d | %d | %d |" % (cat, len(cs), sum(c["level"] == "must" for c in cs), sum(c["level"] == "should" for c in cs)))
    out["categories"] = "\n".join(rows)
    rows = ["| Implementation | Version | Pipeline | Policy | Relation | Pass | Must pass | Same tokens |", "|---|---|---|---|---|---|---|---|"]
    for r in s["matrix"]:
        rows.append("| %s | %s | `%s` | `%s` | %s | %s/%s (%s) | %s/%s | %s |" % (
            r["implementation"], r["version"], r["pipeline"], r["policy"], r["relation"], r["passed"], r["cases"],
            pct(r["pass_rate"]), r["must_passed"], r["must_cases"], pct(r["token_pass_rate"])))
    out["matrix"] = "\n".join(rows)
    runs = s["runs"]
    out["runs"] = "\n".join("- %s: %s" % (r["label"], ", ".join("%s %s" % kv for kv in r["versions"].items())) for r in runs)
    pol = {p["policy_id"]: p for p in load_policies()}
    rows = ["| Policy | What it does | Defined by |", "|---|---|---|"]
    for pid in POLICIES:
        p = pol[pid]
        src = ("arabic-normalize, SHA-256 `%s...`" % p["sha256"][:16]) if "sha256" in p else p["source"]
        rows.append("| `%s` | %s | %s |" % (pid, p["definition"], src))
    out["policies"] = "\n".join(rows)
    return out


def fill(path, secs):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for name, body in secs.items():
        pat = re.compile(r"(<!-- BEGIN %s -->\n).*?(<!-- END %s -->)" % (name, name), re.S)
        text, n = pat.subn(lambda m: m.group(1) + body + "\n" + m.group(2), text)
        if n == 0 and ("BEGIN %s " % name) in text:
            raise SystemExit("marker %s malformed in %s" % (name, path))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    s = stats()
    fill(os.path.join(ROOT, "README.md"), sections(s))
    print(json.dumps({k: v for k, v in s.items() if k.startswith("n_")}, indent=1))
