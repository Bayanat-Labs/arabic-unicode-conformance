#!/usr/bin/env python3
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Build the case files from scripts/cases_source.py.

For every case: assign a stable id, record code points and UTF-8 bytes, compute the expected output under the six
policies with scripts/reference_policies.py, check the expectations stated explicitly in the source against it,
check that every expected output is a fixed point of its policy, and write
  cases/<category>.jsonl                                    one file per category (browsable copy)
  src/arabic_unicode_conformance/data/cases.jsonl           all cases in one file (packaged copy)
  src/arabic_unicode_conformance/data/policies.json         the six policy specs (packaged copy)
  policies/<policy>.yaml                                    the six policy specs

Run with Python 3.14 (unicodedata 16.0.0, the pinned version for the nfc and nfkc expectations):
  python3.14 -I scripts/build_suite.py
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import cases_source  # noqa: E402
import reference_policies as ref  # noqa: E402

PINNED_UNICODE = "16.0.0"
SUITE_VERSION = "0.1.0"
AN_COMMIT = "3ad22326a66596e8dc413321017251eed6e60439"
AN_REPO = "https://github.com/Bayanat-Labs/arabic-normalize"
SHORT = {"r": "raw-safe-v1", "b": "bayanat-norm-v1", "a": "asr-eval-v1", "c": "nfc", "k": "nfkc"}
REFERENCES = {
    "tatweel": ["Unicode Core Spec ch. 9 (Arabic tatweel U+0640)", "BAYANAT-NORM-V1 stage 7"],
    "hamza": ["UAX #15 canonical composition", "UnicodeData.txt decompositions of U+0622..U+0626", "BAYANAT-NORM-V1 stages 11 and 14"],
    "alef": ["UAX #15 canonical composition", "BAYANAT-NORM-V1 stage 11"],
    "yeh": ["BAYANAT-NORM-V1 stages 12 and 15"],
    "taa_marbuta": ["BAYANAT-NORM-V1 stage 13"],
    "diacritic_order": ["UAX #15 canonical ordering", "UnicodeData.txt canonical combining classes", "BAYANAT-NORM-V1 stages 6 and 8"],
    "quranic": ["Unicode Core Spec ch. 9 (Quranic annotation signs)", "BAYANAT-NORM-V1 stages 9 and 10"],
    "digits": ["UnicodeData.txt numeric values", "BAYANAT-NORM-V1 stages 16 and 17"],
    "presentation_forms": ["UAX #15 compatibility decomposition", "BAYANAT-NORM-V1 stages 3 and 4"],
    "lam_alef": ["UAX #15 compatibility decomposition", "BAYANAT-NORM-V1 stages 3 and 11"],
    "joiners": ["ArabicShaping.txt joining types", "emoji-data.txt", "BAYANAT-NORM-V1 stages 2 and 5"],
    "bidi": ["UAX #9 explicit formatting characters", "PropList.txt Bidi_Control", "BAYANAT-NORM-V1 stage 5"],
    "punctuation": ["UnicodeData.txt General_Category P*", "BAYANAT-NORM-V1 stage 17"],
    "spaces": ["PropList.txt White_Space", "BAYANAT-NORM-V1 stage 18"],
    "mixed_script": ["UAX #15", "BAYANAT-NORM-V1 stages 3 and 19"],
    "dialect_letters": ["BAYANAT-NORM-V1 stage 15 (keep)"],
    "confusables": ["UTS #39 confusables", "BAYANAT-NORM-V1 stages 12, 15 and 16"],
    "malformed": ["UTF-8 (RFC 3629)", "PropList.txt Noncharacter_Code_Point", "BAYANAT-NORM-V1 stage 1"],
}


def cp_list(s):
    return ["U+%04X" % ord(c) for c in s]


def has_surrogate(s):
    return any(0xD800 <= ord(c) <= 0xDFFF for c in s)


def dumps(obj):
    from arabic_unicode_conformance.suite import dumps_line
    return dumps_line(obj)


POLICY_SPECS = [
    {"policy_id": "identity", "family": "unicode", "title": "Identity",
     "definition": "The output is the input, code point for code point. Input bytes that are not valid UTF-8 are rejected.",
     "source": "definition"},
    {"policy_id": "nfc", "family": "unicode", "title": "Unicode Normalization Form C",
     "definition": "UAX #15 canonical decomposition, canonical ordering and canonical composition. Lone surrogates and noncharacters pass through unchanged. Input bytes that are not valid UTF-8 are rejected.",
     "source": "Python unicodedata.normalize('NFC'), Unicode %s" % PINNED_UNICODE},
    {"policy_id": "nfkc", "family": "unicode", "title": "Unicode Normalization Form KC",
     "definition": "UAX #15 compatibility decomposition, canonical ordering and canonical composition. Lone surrogates and noncharacters pass through unchanged. Input bytes that are not valid UTF-8 are rejected.",
     "source": "Python unicodedata.normalize('NFKC'), Unicode %s" % PINNED_UNICODE},
]


def arabic_normalize_specs():
    """The three arabic-normalize policies, read from the installed library's policy files (CC BY 4.0, Bayanat Labs)."""
    import arabic_normalize as an
    out = []
    for pid in ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1"):
        p = an.load_policy(pid)
        d = p.data
        out.append({"policy_id": pid, "family": "arabic-normalize", "title": d["meta"]["title_en"],
                    "definition": d["meta"]["description_en"], "sha256": p.policy_hash,
                    "library": "arabic-normalize %s" % an.__version__, "library_commit": AN_COMMIT,
                    "library_repository": AN_REPO, "spec": d["spec"], "unicode_version": d["unicode_version"],
                    "unicode_form": d["unicode_form"], "stages": d["stages"],
                    "source": "%s/blob/%s/src/arabic_normalize/policies/%s.json" % (AN_REPO, AN_COMMIT, pid)})
    return out


def main():
    if unicodedata.unidata_version != PINNED_UNICODE:
        sys.exit("unicodedata %s found; the nfc and nfkc expectations are pinned to %s (use Python 3.14)"
                 % (unicodedata.unidata_version, PINNED_UNICODE))
    errors, records, per_cat = [], [], {}
    for case in cases_source.CASES:
        cat = case["category"]
        per_cat[cat] = per_cat.get(cat, 0) + 1
        cid = "ar-uc-%s-%03d" % (cat.replace("_", "-"), per_cat[cat])
        rec = {"case_id": cid, "category": cat, "level": case["level"], "language_tag": case["language_tag"],
               "input_kind": case["kind"]}
        if case["kind"] == "utf8_bytes":
            raw = case["input_bytes"]
            try:
                raw.decode("utf-8")
                errors.append("%s: bytes decode as UTF-8" % cid)
            except UnicodeDecodeError:
                pass
            rec.update({"input": None, "input_codepoints": [], "input_utf8_hex": raw.hex(), "input_has_lone_surrogate": False,
                        "expected": {p: None for p in ref.POLICIES}, "expected_error": "invalid_utf8", "must_preserve": []})
        else:
            text = case["input"]
            for ch in text:
                o = ord(ch)
                if unicodedata.category(ch) == "Cn" and not (0xD800 <= o <= 0xDFFF) and o not in ref.NONCHAR:
                    errors.append("%s: U+%04X is not assigned in Unicode %s" % (cid, o, PINNED_UNICODE))
            sur = has_surrogate(text)
            expected = {p: ref.apply(p, text) for p in ref.POLICIES}
            for k, want in case["x"].items():
                got = expected[SHORT[k]]
                if got != want:
                    errors.append("%s: explicit %s expectation %s != reference %s"
                                  % (cid, SHORT[k], cp_list(want), cp_list(got)))
            for p, out in expected.items():
                if ref.apply(p, out) != out:
                    errors.append("%s: expected %s output is not a fixed point" % (cid, p))
            keep = sorted({c for c in case["keep"]})
            for c in keep:
                for p in ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1"):
                    if c not in expected[p]:
                        errors.append("%s: must_preserve U+%04X missing from %s" % (cid, ord(c), p))
            rec.update({"input": text, "input_codepoints": cp_list(text),
                        "input_utf8_hex": None if sur else text.encode("utf-8").hex(),
                        "input_has_lone_surrogate": sur, "expected": expected, "expected_error": None,
                        "must_preserve": ["U+%04X" % ord(c) for c in keep]})
        rec.update({"rationale_en": case["rationale_en"], "references": REFERENCES[cat],
                    "nfc_nfkc_unicode_version": PINNED_UNICODE, "added_in": SUITE_VERSION, "author": "Bayanat Labs",
                    "synthetic": True, "review_status": "pending native review"})
        records.append(rec)
    if errors:
        print("\n".join(errors))
        sys.exit("%d errors" % len(errors))

    specs = POLICY_SPECS + arabic_normalize_specs()
    cats = sorted(per_cat)
    os.makedirs(os.path.join(ROOT, "cases"), exist_ok=True)
    for cat in cats:
        with open(os.path.join(ROOT, "cases", "%s.jsonl" % cat), "w", encoding="utf-8", newline="\n") as f:
            for r in records:
                if r["category"] == cat:
                    f.write(dumps(r) + "\n")
    data = os.path.join(ROOT, "src", "arabic_unicode_conformance", "data")
    os.makedirs(data, exist_ok=True)
    with open(os.path.join(data, "cases.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(dumps(r) + "\n")
    with open(os.path.join(data, "policies.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"suite_version": SUITE_VERSION, "policies": specs}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    import yaml
    os.makedirs(os.path.join(ROOT, "policies"), exist_ok=True)
    for s in specs:
        with open(os.path.join(ROOT, "policies", "%s.yaml" % s["policy_id"]), "w", encoding="utf-8", newline="\n") as f:
            f.write("# %s policy spec, Arabic Unicode Conformance Suite %s (CC BY 4.0, Bayanat Labs)\n" % (s["policy_id"], SUITE_VERSION))
            yaml.safe_dump(s, f, allow_unicode=True, sort_keys=False, width=110)
    print(json.dumps({"cases": len(records), "categories": {c: per_cat[c] for c in cats},
                      "hand_written_expectations": sum(len(c["x"]) for c in cases_source.CASES)}, indent=1))


if __name__ == "__main__":
    main()
