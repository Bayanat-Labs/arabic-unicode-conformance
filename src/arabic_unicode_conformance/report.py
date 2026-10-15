# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Turn recorded runs into the conformance matrix: CSV files and one static HTML page."""
from __future__ import annotations

import csv
import html
import json
import os

from .runner import judge
from .suite import POLICIES, dumps_line, load_cases


def _rate(n, d):
    return round(n / d, 4) if d else None


def _token_pass(case, o):
    """Whitespace-insensitive comparison: the output and the expectation split into the same tokens (what a word
    error rate tool sees after splitting on whitespace)."""
    if o["status"] == "pass":
        return True
    if case["expected_error"] or o["output"] is None:
        return False
    return o["output"].split() == case["expected"][o["policy"]].split()


def summarise(runs, cases=None):
    """runs: list of (run, observations). Returns the summary rows, the per-category rows, the agreement rows and the category names."""
    cases = cases if cases is not None else load_cases()
    by_id = {c["case_id"]: c for c in cases}
    cats = sorted({c["category"] for c in cases})
    matrix, by_cat, agree = [], [], []
    for run, obs in runs:
        version = run["versions"].get("version", "")
        for p in run["pipelines"]:
            rows = [o for o in obs if o["pipeline"] == p["id"]]
            app = [o for o in rows if o["status"] != "n/a"]
            must = [o for o in app if o["level"] == "must"]
            with_out = [o for o in app if o.get("output") is not None]
            pres = [o for o in with_out if o.get("must_preserve_kept") is not None]
            base = {"implementation": run["label"], "adapter": run["adapter"], "version": version,
                    "pipeline": p["id"], "call": p["call"], "policy": p["policy"], "relation": p["relation"]}
            matrix.append(dict(base, **{
                "cases": len(app), "passed": sum(o["status"] == "pass" for o in app),
                "pass_rate": _rate(sum(o["status"] == "pass" for o in app), len(app)),
                "must_cases": len(must), "must_passed": sum(o["status"] == "pass" for o in must),
                "must_pass_rate": _rate(sum(o["status"] == "pass" for o in must), len(must)),
                "token_pass_rate": _rate(sum(_token_pass(by_id[o["case_id"]], o) for o in app), len(app)),
                "not_applicable": len(rows) - len(app), "errors": sum(o["error"] is not None for o in app),
                "idempotent_rate": _rate(sum(bool(o.get("idempotent")) for o in with_out), len(with_out)),
                "output_nfc_rate": _rate(sum(bool(o.get("output_nfc")) for o in with_out),
                                         sum(o.get("output_nfc") is not None for o in with_out)),
                "must_preserve_rate": _rate(sum(bool(o["must_preserve_kept"]) for o in pres), len(pres)),
            }))
            row = dict(base)
            for cat in cats:
                cr = [o for o in app if o["category"] == cat]
                row[cat] = _rate(sum(o["status"] == "pass" for o in cr), len(cr))
            by_cat.append(row)
            row = dict(base)
            for pol in POLICIES:
                ok = sum(judge(by_id[o["case_id"]], pol, o["output"], o["error"]) == "pass" for o in app)
                row[pol] = _rate(ok, len(app))
            agree.append(row)
    return matrix, by_cat, agree, cats


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _pct(v):
    return "" if v is None else "%.1f%%" % (100 * v)


def _cell(v):
    if v is None:
        return '<td class="na">n/a</td>'
    band = "hi" if v >= 0.999 else "mid" if v >= 0.8 else "lo"
    return '<td class="%s">%s</td>' % (band, _pct(v))


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5b55;--line:#dedad1;--hi:#d9eedb;--mid:#f6ecc9;--lo:#f6d6d0;--na:#efede8}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ecebe6;--muted:#a9a69d;--line:#34343a;--hi:#1f4429;--mid:#4a3f17;--lo:#552a24;--na:#26262b}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ecebe6;--muted:#a9a69d;--line:#34343a;--hi:#1f4429;--mid:#4a3f17;--lo:#552a24;--na:#26262b}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:24px 16px}
main{max-width:1200px;margin:0 auto} h1{font-size:1.5rem;margin:0 0 .25rem} h2{font-size:1.1rem;margin:2rem 0 .5rem}
p,li{color:var(--muted);max-width:75ch} .scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%} th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{font-weight:600;font-size:.85rem} td.hi{background:var(--hi)} td.mid{background:var(--mid)} td.lo{background:var(--lo)} td.na{background:var(--na);color:var(--muted)}
code{font-size:.85em} .tag{font-size:.75rem;padding:1px 6px;border-radius:9px;border:1px solid var(--line)}
"""


def write_reports(runs, out_dir, cases=None, title="Arabic Unicode Conformance Suite: conformance matrix", run_date=None):
    os.makedirs(out_dir, exist_ok=True)
    cases = cases if cases is not None else load_cases()
    matrix, by_cat, agree, cats = summarise(runs, cases)
    _write_csv(os.path.join(out_dir, "conformance_matrix.csv"), matrix)
    _write_csv(os.path.join(out_dir, "conformance_by_category.csv"), by_cat)
    _write_csv(os.path.join(out_dir, "agreement.csv"), agree)
    with open(os.path.join(out_dir, "runs.json"), "w", encoding="utf-8") as f:
        json.dump([r for r, _ in runs], f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(os.path.join(out_dir, "observations.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for run, obs in runs:
            for o in obs:
                rec = dict({"adapter": run["adapter"], "version": run["versions"].get("version", "")}, **o)
                f.write(dumps_line(rec) + "\n")

    e = html.escape
    n_cases = len(cases)
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             "<title>Conformance matrix</title><style>%s</style></head><body><main>" % CSS,
             "<h1>%s</h1>" % e(title),
             "<p>%d cases, %d categories, %d policies. Each row is one way of calling one implementation. "
             "<b>Conformance</b> rows are judged against a policy the implementation claims to implement; "
             "<b>agreement</b> rows compare a tool that claims no suite policy with the closest policy, and do not "
             "say that the tool is wrong. <b>Same tokens</b> ignores differences in whitespace only (the view of a word error "
             "rate tool that splits on spaces). Raw-byte cases are not applicable to tools that only accept strings.%s</p>"
             % (n_cases, len(cats), len(POLICIES), (" Run on %s." % e(run_date)) if run_date else "")]
    parts.append("<h2>Pass rate against the mapped policy</h2><div class='scroll'><table><tr><th>Implementation</th><th>Version</th>"
                 "<th>Pipeline</th><th>Policy</th><th>Relation</th><th>All cases</th><th>Must cases</th><th>Same tokens</th><th>Idempotent</th>"
                 "<th>Output in NFC</th><th>Must-preserve kept</th></tr>")
    for r in matrix:
        parts.append("<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td><code>%s</code></td><td><span class='tag'>%s</span></td>%s%s%s%s%s%s</tr>"
                     % (e(r["implementation"]), e(str(r["version"])), e(r["pipeline"]), e(r["policy"]), e(r["relation"]),
                        _cell(r["pass_rate"]), _cell(r["must_pass_rate"]), _cell(r["token_pass_rate"]), _cell(r["idempotent_rate"]),
                        _cell(r["output_nfc_rate"]), _cell(r["must_preserve_rate"])))
    parts.append("</table></div>")
    parts.append("<h2>Pass rate by category (mapped policy)</h2><div class='scroll'><table><tr><th>Pipeline</th><th>Policy</th>%s</tr>"
                 % "".join("<th>%s</th>" % e(c) for c in cats))
    for r in by_cat:
        parts.append("<tr><td><code>%s</code></td><td><code>%s</code></td>%s</tr>"
                     % (e(r["pipeline"]), e(r["policy"]), "".join(_cell(r[c]) for c in cats)))
    parts.append("</table></div>")
    parts.append("<h2>Agreement with every policy</h2><p>Share of applicable cases where the pipeline's output equals "
                 "the expected output of each policy. Useful to see which policy a tool behaves most like.</p>"
                 "<div class='scroll'><table><tr><th>Pipeline</th>%s</tr>" % "".join("<th>%s</th>" % e(p) for p in POLICIES))
    for r in agree:
        parts.append("<tr><td><code>%s</code></td>%s</tr>" % (e(r["pipeline"]), "".join(_cell(r[p]) for p in POLICIES)))
    parts.append("</table></div>")
    parts.append("<h2>Runs</h2><ul>")
    for run, _ in runs:
        v = run["versions"]
        parts.append("<li>%s: %s</li>" % (e(run["label"]), e(", ".join("%s %s" % (k, v[k]) for k in v))))
    parts.append("</ul><p>Generated by arabic-unicode-conformance from the recorded runs in this folder. "
                 "Cases: CC BY 4.0. Code: Apache-2.0. Bayanat Labs, hello@bayanatlabs.com.</p></main></body></html>")
    with open(os.path.join(out_dir, "conformance_matrix.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts) + "\n")
    return matrix
