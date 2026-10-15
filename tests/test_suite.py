# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
import collections
import json
import os
import shutil
import subprocess
import sys
import unicodedata

import pytest

import arabic_unicode_conformance as auc
from arabic_unicode_conformance import adapters as A
from arabic_unicode_conformance.cli import main
from arabic_unicode_conformance.report import write_reports
from arabic_unicode_conformance.runner import run_adapter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = auc.load_cases()
BY_ID = {c["case_id"]: c for c in CASES}
FIELDS = {"case_id", "category", "level", "language_tag", "input_kind", "input", "input_codepoints", "input_utf8_hex",
          "input_has_lone_surrogate", "expected", "expected_error", "must_preserve", "rationale_en", "references",
          "nfc_nfkc_unicode_version", "added_in", "author", "synthetic", "review_status"}


def assigned_locally(case):
    """True when every code point of the input is assigned in this interpreter's unicodedata (older Python versions
    lack recent Arabic additions, so NFC/NFKC results for those code points are not comparable)."""
    for cp in case["input_codepoints"]:
        o = int(cp[2:], 16)
        if 0xD800 <= o <= 0xDFFF or (o & 0xFFFE) == 0xFFFE or 0xFDD0 <= o <= 0xFDEF:
            continue
        if unicodedata.category(chr(o)) == "Cn":
            return False
    return True


def test_counts_and_ids():
    assert len(CASES) == 300
    assert len(BY_ID) == len(CASES)
    assert len({c["category"] for c in CASES}) == 18
    for c in CASES:
        assert set(c) == FIELDS, c["case_id"]
        assert c["case_id"].startswith("ar-uc-" + c["category"].replace("_", "-") + "-")
        assert c["level"] in ("must", "should")
        assert c["synthetic"] is True
        assert set(c["expected"]) == set(auc.POLICIES)


def test_codepoints_and_bytes_match_input():
    for c in CASES:
        if c["input_kind"] == "utf8_bytes":
            assert c["input"] is None and c["expected_error"] == "invalid_utf8"
            with pytest.raises(UnicodeDecodeError):
                bytes.fromhex(c["input_utf8_hex"]).decode("utf-8")
            continue
        text = auc.case_text(c)
        assert text == c["input"]
        assert c["input_codepoints"] == ["U+%04X" % ord(ch) for ch in text]
        if c["input_has_lone_surrogate"]:
            assert c["input_utf8_hex"] is None
        else:
            assert bytes.fromhex(c["input_utf8_hex"]).decode("utf-8") == text


def test_identity_expectation_is_the_input():
    for c in CASES:
        if c["input_kind"] == "text":
            assert c["expected"]["identity"] == c["input"]


def test_must_preserve_survives_in_every_folding_policy():
    for c in CASES:
        for cp in c["must_preserve"]:
            ch = chr(int(cp[2:], 16))
            for p in ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1"):
                assert ch in c["expected"][p], (c["case_id"], p)


def test_browsable_case_files_match_the_packaged_copy():
    folder = os.path.join(ROOT, "cases")
    if not os.path.isdir(folder):
        pytest.skip("repository checkout not available")
    assert auc.load_cases(folder) == CASES
    counts = collections.Counter(c["category"] for c in CASES)
    assert sorted(n[:-6] for n in os.listdir(folder) if n.endswith(".jsonl")) == sorted(counts)


def test_policy_specs():
    specs = {p["policy_id"]: p for p in auc.load_policies()}
    assert tuple(specs) == auc.POLICIES
    hashes = {"raw-safe-v1": "57c3d9f03fb9b6854f2527cd1e8a47cadc266f47f02dda94652306dacea03bb5",
              "bayanat-norm-v1": "ebdb82000d0762a65120ffa9311bc6f01b481b19d4348ea5bedb3ab23d759321",
              "asr-eval-v1": "5d866146536a23b90c0882044dae5f55f2484f0635e206828246eabeb69668de"}
    for pid, h in hashes.items():
        assert specs[pid]["sha256"] == h


def test_nfc_nfkc_expectations_match_this_python():
    checked = 0
    for c in CASES:
        if c["input_kind"] != "text" or not assigned_locally(c):
            continue
        assert unicodedata.normalize("NFC", c["input"]) == c["expected"]["nfc"], c["case_id"]
        assert unicodedata.normalize("NFKC", c["input"]) == c["expected"]["nfkc"], c["case_id"]
        checked += 1
    assert checked > 250


def test_unicodedata_adapter_passes():
    run, obs = run_adapter(A.get("python-unicodedata"), [c for c in CASES if c["input_kind"] != "text" or assigned_locally(c)])
    assert obs and all(o["status"] == "pass" for o in obs)
    assert run["versions"]["unicode"] == unicodedata.unidata_version


def test_arabic_normalize_python_passes_every_case():
    pytest.importorskip("arabic_normalize")
    run, obs = run_adapter(A.get("arabic-normalize-py"), CASES)
    assert len(obs) == 3 * len(CASES)
    assert [o["case_id"] for o in obs if o["status"] != "pass"] == []


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_icu_node_adapter_runs():
    run, obs = run_adapter(A.get("icu-node"), CASES[:20])
    assert len(obs) == 40 and all(o["status"] in ("pass", "fail") for o in obs)


def test_judge_and_report(tmp_path):
    run, obs = run_adapter(A.get("python-unicodedata"), CASES[:30])
    obs[0] = dict(obs[0], status="fail", output="x")
    matrix = write_reports([(run, obs)], str(tmp_path), CASES[:30], run_date="2026-10-15")
    assert {r["pipeline"] for r in matrix} == {"py-nfc", "py-nfkc"}
    assert any(r["passed"] == r["cases"] - 1 for r in matrix)
    for name in ("conformance_matrix.csv", "conformance_by_category.csv", "agreement.csv", "conformance_matrix.html", "observations.jsonl", "runs.json"):
        assert (tmp_path / name).exists()
    for line in (tmp_path / "observations.jsonl").read_text(encoding="utf-8").split("\n"):
        if line:
            json.loads(line)


def test_cli(tmp_path, capsys):
    assert main(["list"]) == 0
    assert "300 cases" in capsys.readouterr().out
    out = tmp_path / "run.json"
    assert main(["run", "--impl", "python-unicodedata", "--out", str(out)]) == 0
    assert main(["report", str(out), "--out", str(tmp_path / "rep")]) == 0
    assert (tmp_path / "rep" / "conformance_matrix.html").exists()


def test_module_entry_point():
    r = subprocess.run([sys.executable, "-m", "arabic_unicode_conformance", "--version"], capture_output=True, text=True)
    assert r.returncode == 0 and auc.__version__ in r.stdout


def test_published_matrix_matches_recorded_observations():
    """reports/conformance_matrix.csv is regenerated from reports/observations.jsonl and agrees with the packaged cases."""
    obs_path = os.path.join(ROOT, "reports", "observations.jsonl")
    if not os.path.exists(obs_path):
        pytest.skip("repository checkout not available")
    from arabic_unicode_conformance.runner import judge
    with open(obs_path, encoding="utf-8") as f:
        for line in f.read().split("\n"):
            if not line:
                continue
            o = json.loads(line)
            if o["status"] == "n/a":
                continue
            assert judge(BY_ID[o["case_id"]], o["policy"], o["output"], o["error"]) == o["status"], o
