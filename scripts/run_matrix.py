#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Run every adapter and rebuild reports/ (the conformance matrix) in one command.

  bash scripts/setup_tools.sh TOOLS                          # once
  python scripts/run_matrix.py --tools TOOLS --out reports --date 2026-10-15

The arabic-normalize Python package must be importable in the environment that runs this script. Adapters whose
tool is missing are skipped with a message, and the matrix is built from the others.
"""
import argparse
import json
import os
import sys

from arabic_unicode_conformance import adapters as A
from arabic_unicode_conformance.report import write_reports
from arabic_unicode_conformance.runner import run_adapter
from arabic_unicode_conformance.suite import load_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True, help="folder created by scripts/setup_tools.sh")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--date")
    ap.add_argument("--runs", help="also keep one run file per adapter in this folder")
    a = ap.parse_args()
    t = a.tools
    py = lambda name: os.path.join(t, name, "bin", "python")  # noqa: E731
    plan = [("python-unicodedata", {}), ("icu-node", {}), ("arabic-normalize-py", {}),
            ("arabic-normalize-js", {"js_path": os.path.join(t, "arabic-normalize", "js")}),
            ("camel-tools", {"python": py("camel")}), ("pyarabic", {"python": py("pyarabic")}),
            ("whisper-basic", {"python": py("whisper")})]
    cases = load_cases()
    runs = []
    for name, opts in plan:
        try:
            run, obs = run_adapter(A.get(name, **opts), cases)
        except Exception as exc:  # a missing tool must not stop the others
            print("skipped %s: %s" % (name, exc), file=sys.stderr)
            continue
        runs.append((run, obs))
        print("%-22s %d observations" % (name, len(obs)))
        if a.runs:
            os.makedirs(a.runs, exist_ok=True)
            with open(os.path.join(a.runs, name + ".json"), "w", encoding="utf-8") as f:
                json.dump({"run": run, "observations": obs}, f, ensure_ascii=True)
    write_reports(runs, a.out, cases, run_date=a.date)
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
