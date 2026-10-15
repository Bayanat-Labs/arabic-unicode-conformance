#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Build the Hugging Face dataset folder from the released files (cases, policies, reports). Every number in the
dataset card is computed here. Needs pyarrow.

  python -I scripts/make_dataset.py OUT_DIR [--source-commit SHA]
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import shutil
import sys

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from arabic_unicode_conformance import __version__  # noqa: E402
from arabic_unicode_conformance.suite import POLICIES, dumps_line, load_cases, load_policies  # noqa: E402

REPO = "Bayanat-Labs/arabic-unicode-conformance"
GITHUB = "https://github.com/" + REPO
DATE = "2026-10-15"


def has_sur(s):
    return s is not None and any(0xD800 <= ord(c) <= 0xDFFF for c in s)


def utf8_or_none(s):
    """Parquet strings must be valid UTF-8: strings holding a lone surrogate are stored as null (use the code points)."""
    return None if has_sur(s) else s


def cps(s):
    return None if s is None else ["U+%04X" % ord(c) for c in s]


def write_parquet(rows, schema, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), path, compression="zstd")


def write_jsonl(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(dumps_line(r) + "\n")


S, L, B = pa.string(), pa.list_(pa.string()), pa.bool_()


def build(out, source_commit):
    cases = load_cases()
    pols = {p["policy_id"]: p for p in load_policies()}
    with open(os.path.join(ROOT, "reports", "observations.jsonl"), encoding="utf-8") as f:
        observations = [json.loads(x) for x in f.read().split("\n") if x]
    with open(os.path.join(ROOT, "reports", "runs.json"), encoding="utf-8") as f:
        runs = json.load(f)
    with open(os.path.join(ROOT, "reports", "conformance_matrix.csv"), encoding="utf-8") as f:
        matrix = list(csv.DictReader(f))
    label = {r["adapter"]: r["label"] for r in runs}

    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    # ---- config "cases": one row per case, the expected output of every policy in its own column
    case_rows = []
    for c in cases:
        r = {"case_id": c["case_id"], "category": c["category"], "level": c["level"], "language_tag": c["language_tag"],
             "input_kind": c["input_kind"], "input": utf8_or_none(c["input"]), "input_codepoints": c["input_codepoints"],
             "input_utf8_hex": c["input_utf8_hex"], "input_has_lone_surrogate": c["input_has_lone_surrogate"]}
        for p in POLICIES:
            r["expected_" + p.replace("-", "_")] = utf8_or_none(c["expected"][p])
        r.update({"expected_error": c["expected_error"], "must_preserve": c["must_preserve"],
                  "rationale_en": c["rationale_en"], "references": c["references"],
                  "nfc_nfkc_unicode_version": c["nfc_nfkc_unicode_version"], "added_in": c["added_in"],
                  "author": c["author"], "synthetic": c["synthetic"], "review_status": c["review_status"]})
        case_rows.append(r)
    case_schema = pa.schema([("case_id", S), ("category", S), ("level", S), ("language_tag", S), ("input_kind", S),
                             ("input", S), ("input_codepoints", L), ("input_utf8_hex", S), ("input_has_lone_surrogate", B)]
                            + [("expected_" + p.replace("-", "_"), S) for p in POLICIES]
                            + [("expected_error", S), ("must_preserve", L), ("rationale_en", S), ("references", L),
                               ("nfc_nfkc_unicode_version", S), ("added_in", S), ("author", S), ("synthetic", B),
                               ("review_status", S)])

    # ---- config "expectations": one row per (case, policy), with exact code points
    exp_rows = []
    for c in cases:
        for p in POLICIES:
            e = c["expected"][p]
            exp_rows.append({"case_id": c["case_id"], "category": c["category"], "level": c["level"], "policy": p,
                             "policy_sha256": pols[p].get("sha256"), "input_kind": c["input_kind"],
                             "input": utf8_or_none(c["input"]), "input_codepoints": c["input_codepoints"],
                             "input_utf8_hex": c["input_utf8_hex"], "expected_output": utf8_or_none(e),
                             "expected_codepoints": cps(e), "expected_error": c["expected_error"],
                             "changed": None if e is None else e != c["input"], "must_preserve": c["must_preserve"]})
    exp_schema = pa.schema([("case_id", S), ("category", S), ("level", S), ("policy", S), ("policy_sha256", S),
                            ("input_kind", S), ("input", S), ("input_codepoints", L), ("input_utf8_hex", S),
                            ("expected_output", S), ("expected_codepoints", L), ("expected_error", S), ("changed", B),
                            ("must_preserve", L)])

    # ---- config "observations": every output recorded for the conformance matrix
    obs_rows = []
    for o in observations:
        obs_rows.append({"implementation": label[o["adapter"]], "adapter": o["adapter"], "version": o["version"],
                         "pipeline": o["pipeline"], "policy": o["policy"], "relation": o["relation"],
                         "case_id": o["case_id"], "category": o["category"], "level": o["level"],
                         "output": utf8_or_none(o["output"]), "output_codepoints": cps(o["output"]), "error": o["error"],
                         "status": o["status"], "idempotent": o.get("idempotent"), "output_nfc": o.get("output_nfc"),
                         "must_preserve_kept": o.get("must_preserve_kept")})
    obs_schema = pa.schema([("implementation", S), ("adapter", S), ("version", S), ("pipeline", S), ("policy", S),
                            ("relation", S), ("case_id", S), ("category", S), ("level", S), ("output", S),
                            ("output_codepoints", L), ("error", S), ("status", S), ("idempotent", B),
                            ("output_nfc", B), ("must_preserve_kept", B)])

    for name, rows, schema in (("cases", case_rows, case_schema), ("expectations", exp_rows, exp_schema),
                               ("observations", obs_rows, obs_schema)):
        write_parquet(rows, schema, os.path.join(out, "data", name, "test-00000-of-00001.parquet"))
    write_jsonl(cases, os.path.join(out, "jsonl", "cases.jsonl"))
    write_jsonl(observations, os.path.join(out, "jsonl", "observations.jsonl"))
    os.makedirs(os.path.join(out, "conformance"))
    for n in ("conformance_matrix.csv", "conformance_by_category.csv", "agreement.csv", "conformance_matrix.html", "runs.json"):
        shutil.copy(os.path.join(ROOT, "reports", n), os.path.join(out, "conformance", n))
    os.makedirs(os.path.join(out, "policies"))
    shutil.copy(os.path.join(ROOT, "src", "arabic_unicode_conformance", "data", "policies.json"), os.path.join(out, "policies", "policies.json"))
    for n in ("BAYANAT-NORM-V1.md", "BAYANAT-NORM-V1.ar.md"):
        shutil.copy(os.path.join(ROOT, "docs", n), os.path.join(out, "policies", n))
    shutil.copy(os.path.join(ROOT, "CITATION.cff"), os.path.join(out, "CITATION.cff"))

    # ---- numbers for the card
    cats = collections.Counter(c["category"] for c in cases)
    levels = collections.Counter(c["level"] for c in cases)
    langs = collections.Counter(c["language_tag"] for c in cases)
    changed = {p: sum(r["changed"] is True for r in exp_rows if r["policy"] == p) for p in POLICIES}
    n = {"cases": len(cases), "categories": len(cats), "policies": len(POLICIES), "expectations": len(exp_rows),
         "observations": len(obs_rows), "implementations": len(runs), "pipelines": len(matrix),
         "text": sum(c["input_kind"] == "text" for c in cases), "bytes": sum(c["input_kind"] == "utf8_bytes" for c in cases),
         "surrogate": sum(c["input_has_lone_surrogate"] for c in cases),
         "null_expected": sum(r["expected_output"] is None and r["expected_error"] is None for r in exp_rows),
         "must": levels["must"], "should": levels["should"], "langs": len(langs),
         "preserve": sum(bool(c["must_preserve"]) for c in cases)}
    card = card_text(n, cats, cases, langs, changed, matrix, runs, pols)
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(card)
    with open(os.path.join(out, "LICENSE"), "w", encoding="utf-8", newline="\n") as f:
        f.write("The data in this repository is licensed under the Creative Commons Attribution 4.0 International "
                "License (CC BY 4.0), copyright 2026 Bayanat Labs.\nFull text: https://creativecommons.org/licenses/by/4.0/legalcode\n"
                "Attribute as: \"Arabic Unicode Conformance Suite, Bayanat Labs (https://bayanatlabs.com), CC BY 4.0\".\n"
                "The outputs of third-party tools in the observations config are recorded observations of those tools, "
                "run unmodified; the tools keep their own licences.\n")
    manifest = {"name": "arabic-unicode-conformance", "version": __version__, "created": DATE,
                "source_repository": GITHUB, "source_commit": source_commit,
                "nfc_nfkc_expectations": "Python 3.14.7 unicodedata, Unicode 16.0.0",
                "named_policies": {p: pols[p]["sha256"] for p in ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")},
                "arabic_normalize_commit": pols["bayanat-norm-v1"]["library_commit"], "counts": n}
    with open(os.path.join(out, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write("\n")
    sums = []
    for dp, _, fs in os.walk(out):
        for fn in sorted(fs):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, out)
            if rel == "SHA256SUMS":
                continue
            with open(full, "rb") as g:
                sums.append("%s  %s" % (hashlib.sha256(g.read()).hexdigest(), rel))
    with open(os.path.join(out, "SHA256SUMS"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(sums, key=lambda x: x.split("  ", 1)[1])) + "\n")
    return n


def pct(v):
    return "%.1f%%" % (100 * float(v)) if v not in ("", None) else "n/a"


def card_text(n, cats, cases, langs, changed, matrix, runs, pols):
    cfg_yaml = "\n".join("  - config_name: %s\n%s    data_files:\n      - split: test\n        path: data/%s/test-00000-of-00001.parquet"
                         % (c, "    default: true\n" if c == "cases" else "", c) for c in ("cases", "expectations", "observations"))
    lines = ["---", 'pretty_name: "Arabic Unicode Conformance Suite"', "license: cc-by-4.0",
             "language:\n  - ar\n  - fa\n  - ur", "size_categories:\n  - n<1K",
             "tags:\n  - arabic\n  - arabic-nlp\n  - unicode\n  - text-normalization\n  - conformance-tests\n  - test-suite\n  - asr-evaluation\n  - synthetic\n  - bayanat-labs",
             "configs:", cfg_yaml, "---", ""]
    lines += [
        "# Arabic Unicode Conformance Suite",
        "",
        "> %d test cases with the exact expected output of Arabic text normalisation under %d named policies, and the observed outputs of %d implementations. Version %s (%s). Code and runner: [GitHub](%s)." % (n["cases"], n["policies"], n["implementations"], __version__, DATE, GITHUB),
        "> Published by **Bayanat Labs** (bayanatlabs.com). Arabic summary at the end of this card.",
        "",
        "## What it is",
        "",
        "Arabic text normalisation (removing harakat and tatweel, folding alef forms, mapping presentation forms such as ﻻ, handling ZWNJ, bidi controls and Arabic-Indic digits) is done differently by every tool, and reports rarely say exactly what was done, so word error rates and deduplication counts computed with different tools are not comparable. This dataset pins the behaviour down: each case gives an input string (with its code points and UTF-8 bytes) and the exact output under six named policies: `identity`, `nfc`, `nfkc`, and the three policies of the open-source library [arabic-normalize](https://github.com/Bayanat-Labs/arabic-normalize): `raw-safe-v1` (cleaning only), `bayanat-norm-v1` (a normalised text column) and `asr-eval-v1` (speech recognition scoring). The policies are defined stage by stage in `policies/BAYANAT-NORM-V1.md`.",
        "",
        "arabic-normalize also ships 80 conformance fixtures ([Bayanat-Labs/arabic-normalization-conformance](https://huggingface.co/datasets/Bayanat-Labs/arabic-normalization-conformance)); this suite is broader, with more categories, more policies and more implementations.",
        "",
        "**Intended uses:** testing an Arabic normaliser against a named policy; stating which normalisation a word error rate or a search index used; comparing tools on Arabic Unicode edge cases.",
        "**Out-of-scope uses:** training or evaluating language models (the set is small and synthetic); statistics about how often a phenomenon occurs in real text; judging whether a policy is linguistically right for a task (the policies are choices).",
        "",
        "## What is released",
        "",
        "| Config | Split | One row per | Rows |",
        "|---|---|---|---|",
        "| `cases` (default) | `test` | case, with the expected output of every policy in its own column | %d |" % n["cases"],
        "| `expectations` | `test` | case and policy, with exact expected code points | %d |" % n["expectations"],
        "| `observations` | `test` | implementation pipeline and case: the output it gave and whether it matched | %d |" % n["observations"],
        "",
        "Also in the repository: `jsonl/` (the same cases and observations as JSON Lines, with invisible characters written as `\\uXXXX` escapes), `conformance/` (the conformance matrix as CSV and HTML, and the versions of every tool run), `policies/` (policy specs and the normative text in English and Arabic), `MANIFEST.json` and `SHA256SUMS`.",
        "",
        "## How to load",
        "",
        "```python",
        "from datasets import load_dataset",
        'cases = load_dataset("%s", "cases", split="test")' % REPO,
        "",
        "def exact_input(row):  # rebuilds the exact input, lone surrogates included",
        '    return "".join(chr(int(cp[2:], 16)) for cp in row["input_codepoints"])',
        "",
        "failures = [r[\"case_id\"] for r in cases",
        "            if r[\"input_kind\"] == \"text\" and my_normaliser(exact_input(r)) != r[\"expected_bayanat_norm_v1\"]]",
        "```",
        "",
        "The runner on GitHub does the same for several tools and builds the matrix: `pip install \"git+%s@v%s\"`, then `arabic-unicode-conformance run --impl <adapter>`. The package will also be installable with `pip install arabic-unicode-conformance` once it is published." % (GITHUB, __version__),
        "",
        "## Breakdown",
        "",
        "| | |", "|---|---|",
        "| Cases | %d (%d text inputs, %d raw-byte inputs that are not valid UTF-8) |" % (n["cases"], n["text"], n["bytes"]),
        "| Inputs with a lone surrogate | %d |" % n["surrogate"],
        "| Levels | %d `must`, %d `should` |" % (n["must"], n["should"]),
        "| Cases with letters that must survive (`must_preserve`) | %d |" % n["preserve"],
        "| Language tags | %d (%s) |" % (n["langs"], ", ".join("%s %d" % kv for kv in sorted(langs.items(), key=lambda kv: (-kv[1], kv[0])))),
        "",
        "| Category | Cases | must | should |", "|---|---|---|---|",
    ]
    for cat in sorted(cats):
        cs = [c for c in cases if c["category"] == cat]
        lines.append("| `%s` | %d | %d | %d |" % (cat, len(cs), sum(c["level"] == "must" for c in cs), sum(c["level"] == "should" for c in cs)))
    lines += ["", "| Policy | Text cases whose expected output differs from the input | Defined by |", "|---|---|---|"]
    for p in POLICIES:
        src = ("arabic-normalize policy, SHA-256 `%s`" % pols[p]["sha256"]) if pols[p].get("sha256") else pols[p]["source"]
        lines.append("| `%s` | %d of %d | %s |" % (p, changed[p], n["text"], src))
    lines += ["", "## Conformance matrix", "",
              "**Conformance** rows are implementations that claim the policy. **Agreement** rows are tools that claim no suite policy, compared with the closest one; low agreement means the tool normalises differently, not that it is wrong. \"Same tokens\" ignores whitespace differences only. The three raw-byte cases are not applicable to tools that accept only strings. The exact calls are listed in `ADAPTERS.md` on GitHub.", "",
              "| Implementation | Version | Pipeline | Policy | Relation | Pass | Same tokens |", "|---|---|---|---|---|---|---|"]
    for r in matrix:
        lines.append("| %s | %s | `%s` | `%s` | %s | %s/%s (%s) | %s |" % (r["implementation"], r["version"], r["pipeline"], r["policy"],
                                                                   r["relation"], r["passed"], r["cases"], pct(r["pass_rate"]), pct(r["token_pass_rate"])))
    lines += ["", "Run on %s with: %s." % (DATE, "; ".join("%s (%s)" % (r["label"], ", ".join("%s %s" % kv for kv in r["versions"].items())) for r in runs)),
              "Tools were run unmodified, through their public functions, each in its own environment; PyArabic (GPL) ran as a separate process. Maintainers and users are welcome to send corrections to hello@bayanatlabs.com.", "",
              "## Structure (config `cases`)", "",
              "| Field | Type | Description |", "|---|---|---|",
              "| `case_id` | string | Stable id, never reused (`ar-uc-<category>-<nnn>`) |",
              "| `category`, `level` | string | Phenomenon tested; `must` or `should` |",
              "| `language_tag` | string | Language of the input (`und` when not language-specific); the policies do not depend on it |",
              "| `input_kind` | string | `text`, or `utf8_bytes` for raw bytes that are not valid UTF-8 |",
              "| `input` | string, nullable | The input. Null for raw-byte inputs and for inputs holding a lone surrogate (Parquet strings must be valid UTF-8): rebuild those from `input_codepoints` |",
              "| `input_codepoints` | list of string | Exact input code points (`U+0649`) |",
              "| `input_utf8_hex` | string, nullable | UTF-8 bytes in hex; the raw bytes for `utf8_bytes` inputs; null when the input holds a lone surrogate |",
              "| `expected_identity` ... `expected_asr_eval_v1` | string, nullable | Expected output per policy; null when the input must be rejected or when the output holds a lone surrogate (the `expectations` config has the exact code points) |",
              "| `expected_error` | string, nullable | `invalid_utf8` when every policy must reject the input |",
              "| `must_preserve` | list of string | Code points that `raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` must keep |",
              "| `rationale_en`, `references` | string, list | Why the expected outputs are what they are, and the specifications behind them |",
              "| `nfc_nfkc_unicode_version` | string | Unicode version of the `nfc` and `nfkc` expectations (16.0.0; every input uses code points assigned since Unicode 13.0.0) |",
              "| `added_in`, `author`, `synthetic`, `review_status` | string, bool | Suite version, authorship (Bayanat Labs), `synthetic: true`, review status |",
              "",
              "## Creation", "",
              "- Every input was written by Bayanat Labs for this suite; no text is taken from a corpus or from another project's tests (`synthetic: true`).",
              "- `identity`, `nfc` and `nfkc` expectations: Python 3.14 `unicodedata` (Unicode 16.0.0).",
              "- `raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` expectations: an independent reference implementation written from the stage definitions; many were also stated explicitly in the case source and checked against it. arabic-normalize (Python and JavaScript, commit `%s`) passes every case." % pols["bayanat-norm-v1"]["library_commit"],
              "- Every expected output is a fixed point of its policy (checked by the build).",
              "- Review status: not yet reviewed by native Arabic speakers (`review_status: \"pending native review\"`).",
              "",
              "## Considerations and limitations", "",
              "- The policies are choices: folding أ to ا or ى to ي merges some distinct words, and `asr-eval-v1` splits numbers at Arabic separators. The suite tests that a normaliser does what a policy says.",
              "- The cases show behaviour; they say nothing about frequency in real text.",
              "- Agreement rows depend on how each tool's functions were combined into a pipeline; other combinations exist.",
              "- Bidi display order and glyph shaping are not tested.",
              "- Personal data: none. Common names such as محمد and مصطفى appear only as spelling examples.",
              "",
              "## Licensing", "",
              "CC BY 4.0. Attribute as \"Arabic Unicode Conformance Suite, Bayanat Labs, CC BY 4.0\". The runner code on GitHub is Apache-2.0. The `observations` config records outputs of third-party tools; the tools keep their own licences.",
              "",
              "## Citation", "",
              "```bibtex",
              "@misc{bayanatlabs_arabic_unicode_conformance_2026,",
              "  title  = {Arabic Unicode Conformance Suite},",
              "  author = {{Bayanat Labs}},",
              "  year   = {2026},",
              "  note   = {Version %s}," % __version__,
              "  url    = {https://huggingface.co/datasets/%s}" % REPO,
              "}",
              "```",
              "",
              "## Contact, corrections and takedown", "",
              "hello@bayanatlabs.com. Bayanat Labs also builds Arabic speech and text datasets for evaluation and training.",
              "",
              "## Changelog", "",
              "| Version | Date | Change |", "|---|---|---|",
              "| %s | %s | First release: %d cases, %d policies, %d implementations |" % (__version__, DATE, n["cases"], n["policies"], n["implementations"]),
              "",
              "## بالعربية", "",
              "*The Arabic text has not yet been reviewed by a native Arabic writer; the English governs.*", "",
              "<div dir=\"rtl\" lang=\"ar\">", "",
              "حزمة اختبار مفتوحة لتوحيد النص العربي: %d حالة، لكل منها نص مدخل ونقاط ترميزه وبايتاته، والناتج الدقيق المتوقع تحت %d سياسات مسمّاة (`identity` و`nfc` و`nfkc` و`raw-safe-v1` و`bayanat-norm-v1` و`asr-eval-v1`)، مع مخرجات %d تطبيقات مسجّلة في مصفوفة مطابقة. تغطي الحالات التطويل والهمزات وصور الألف والألف المقصورة والتاء المربوطة وترتيب الحركات والعلامات القرآنية والأرقام وأشكال العرض ولام ألف والفاصل غير الواصل ومحارف الاتجاه وعلامات الترقيم والمسافات وحروف اللهجات (ڤ ڨ ݣ ڭ پ چ گ) والمحارف المتشابهة والمدخلات المعيبة. كتبت بيانات لابز كل الحالات لهذه الحزمة، والترخيص CC BY 4.0. النص المعياري للسياسات بالعربية في `policies/BAYANAT-NORM-V1.ar.md`." % (n["cases"], n["policies"], n["implementations"]),
              "", "</div>", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--source-commit")
    a = ap.parse_args()
    print(json.dumps(build(a.out, a.source_commit), indent=1))
