# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""The reference implementation used to author the expectations (scripts/reference_policies.py) reproduces them, and
its arabic-normalize policies are idempotent and NFC-stable on seeded random Arabic-script strings."""
import os
import sys
import unicodedata

import pytest

import arabic_unicode_conformance as auc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if not os.path.exists(os.path.join(SCRIPTS, "reference_policies.py")):
    pytest.skip("repository checkout not available", allow_module_level=True)
sys.path.insert(0, SCRIPTS)
import reference_policies as ref  # noqa: E402

FOLDING = ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")


def _local(case):
    for cp in case["input_codepoints"]:
        o = int(cp[2:], 16)
        if not (0xD800 <= o <= 0xDFFF or o in ref.NONCHAR) and unicodedata.category(chr(o)) == "Cn":
            return False
    return True


def test_reference_reproduces_every_expectation():
    for c in auc.load_cases():
        if c["input_kind"] != "text" or not _local(c):
            continue
        for p in auc.POLICIES:
            assert ref.apply(p, c["input"]) == c["expected"][p], (c["case_id"], p)


hypothesis = pytest.importorskip("hypothesis")
st = hypothesis.strategies

# An alphabet weighted towards the code points the suite is about: Arabic letters and marks, presentation forms,
# joiners, bidi controls, digits, punctuation and spaces.
ALPHABET = ([chr(c) for c in range(0x0600, 0x0700)] + [chr(c) for c in range(0xFE70, 0xFEFD)]
            + [chr(c) for c in range(0xFB50, 0xFBB2)] + list("​‌‍‎‏؜‪‫‬"
                                                             "⁦⁧⁩﻿    ab1.,!")
            + ["\U0001F468", "\U0001F469", "\U0001F3FD", "️"])
ALPHABET = [ch for ch in ALPHABET if unicodedata.category(ch) != "Cn" and ord(ch) not in ref.NONCHAR]


@hypothesis.settings(max_examples=400, derandomize=True, deadline=None)
@hypothesis.given(st.text(alphabet=st.sampled_from(ALPHABET), max_size=24))
def test_folding_policies_are_idempotent_and_nfc_stable(text):
    for p in FOLDING:
        out = ref.apply(p, text)
        assert ref.apply(p, out) == out, p
        assert unicodedata.is_normalized("NFC", out), p


@hypothesis.settings(max_examples=400, derandomize=True, deadline=None)
@hypothesis.given(st.text(alphabet=st.sampled_from(ALPHABET), max_size=24))
def test_reference_agrees_with_arabic_normalize(text):
    an = pytest.importorskip("arabic_normalize")
    for p in FOLDING:
        assert an.normalize(text, p) == ref.apply(p, text), p
