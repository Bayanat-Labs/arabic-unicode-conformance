# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Command line: arabic-unicode-conformance {list,run,report}."""
from __future__ import annotations

import argparse
import collections
import json
import sys

from . import __version__
from . import adapters as A
from .suite import POLICIES, load_cases


def _list(args):
    cases = load_cases(args.cases)
    print("arabic-unicode-conformance %s: %d cases, %d policies" % (__version__, len(cases), len(POLICIES)))
    for cat, n in sorted(collections.Counter(c["category"] for c in cases).items()):
        print("  %-20s %d" % (cat, n))
    print("policies: " + ", ".join(POLICIES))
    print("adapters:")
    for name, cls in A.ADAPTERS.items():
        a = cls()
        print("  %-22s %s%s" % (name, a.label, ("  (needs %s)" % a.needs) if a.needs else ""))
        for p in a.pipelines:
            print("      %-20s %-12s %-16s %s" % (p.id, p.relation, p.policy, p.call))
    return 0


def _run(args):
    adapter = A.get(args.impl, python=args.python, node=args.node, js_path=args.js_path)
    from .runner import run_adapter
    run, obs = run_adapter(adapter, load_cases(args.cases))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"run": run, "observations": obs}, f, ensure_ascii=True)
            f.write("\n")
    failed_must = 0
    for p in adapter.pipelines:
        rows = [o for o in obs if o["pipeline"] == p.id and o["status"] != "n/a"]
        ok = sum(o["status"] == "pass" for o in rows)
        must = [o for o in rows if o["level"] == "must"]
        must_ok = sum(o["status"] == "pass" for o in must)
        if p.relation == "conformance":
            failed_must += len(must) - must_ok
        print("%-20s %-12s %-16s %3d/%3d pass (must %3d/%3d)" % (p.id, p.relation, p.policy, ok, len(rows), must_ok, len(must)))
        if args.show_failures:
            for o in rows:
                if o["status"] == "fail":
                    print("    %s output=%r error=%r" % (o["case_id"], o["output"], o["error"]))
    if args.check and failed_must:
        print("%d must cases failed in conformance pipelines" % failed_must, file=sys.stderr)
        return 1
    return 0


def _report(args):
    from .report import write_reports
    runs = []
    for path in args.runs:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        runs.append((d["run"], d["observations"]))
    write_reports(runs, args.out, load_cases(args.cases), run_date=args.date)
    print("wrote %s/conformance_matrix.csv, conformance_by_category.csv, agreement.csv, conformance_matrix.html, observations.jsonl, runs.json" % args.out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arabic-unicode-conformance",
                                 description="Run Arabic text normalisers against the Arabic Unicode Conformance Suite.")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    ap.add_argument("--cases", help="a cases.jsonl file or a cases/ directory (default: the packaged cases)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list cases, policies and adapters").set_defaults(func=_list)
    r = sub.add_parser("run", help="run one adapter over every case")
    r.add_argument("--impl", required=True, help="adapter name (see `list`)")
    r.add_argument("--python", help="interpreter of the environment where a third-party Python tool is installed")
    r.add_argument("--node", help="node executable (default: node on PATH)")
    r.add_argument("--js-path", help="js/ folder of an arabic-normalize checkout (arabic-normalize-js adapter)")
    r.add_argument("--out", help="write the run and every observation to this JSON file")
    r.add_argument("--show-failures", action="store_true")
    r.add_argument("--check", action="store_true", help="exit 1 if a conformance pipeline fails any 'must' case")
    r.set_defaults(func=_run)
    rep = sub.add_parser("report", help="build the matrix (CSV + HTML) from run files")
    rep.add_argument("runs", nargs="+")
    rep.add_argument("--out", required=True)
    rep.add_argument("--date", help="run date shown on the HTML page")
    rep.set_defaults(func=_report)
    args = ap.parse_args(argv)
    return args.func(args)
