# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Load the packaged cases and policy specs."""
from __future__ import annotations

import json
import os
import unicodedata
from importlib import resources

POLICIES = ("identity", "nfc", "nfkc", "raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")


def _read(name):
    return resources.files("arabic_unicode_conformance").joinpath("data").joinpath(name).read_text(encoding="utf-8")


def _parse(text):
    # Split on line feeds only: str.splitlines() would also split at U+2028, U+0085 and other separators.
    return [json.loads(line) for line in text.split("\n") if line.strip(" \r\t")]


def load_cases(path=None):
    """Return the list of case records, in suite order. `path` may name another cases.jsonl file or a directory
    of per-category .jsonl files (such as cases/ in the repository)."""
    if path is None:
        return _parse(_read("cases.jsonl"))
    if os.path.isdir(path):
        cases = []
        for name in sorted(os.listdir(path)):
            if name.endswith(".jsonl"):
                with open(os.path.join(path, name), encoding="utf-8") as f:
                    cases.extend(_parse(f.read()))
        order = {c["case_id"]: i for i, c in enumerate(_parse(_read("cases.jsonl")))}
        cases.sort(key=lambda c: (order.get(c["case_id"], len(order)), c["case_id"]))
        return cases
    with open(path, encoding="utf-8") as f:
        return _parse(f.read())


def load_policies():
    return json.loads(_read("policies.json"))["policies"]


def case_text(case):
    """The exact input string (lone surrogates included), or None for a raw-bytes case."""
    if case["input_kind"] == "utf8_bytes":
        return None
    return "".join(chr(int(cp[2:], 16)) for cp in case["input_codepoints"])


def case_bytes(case):
    return bytes.fromhex(case["input_utf8_hex"]) if case["input_kind"] == "utf8_bytes" else None


def _escape(ch):
    o = ord(ch)
    if o > 0xFFFF:
        o -= 0x10000
        return "\\u%04x\\u%04x" % (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF))
    return "\\u%04x" % o


def _invisible(ch):
    cat = unicodedata.category(ch)
    return cat in ("Cc", "Cf", "Zl", "Zp", "Cs", "Co", "Cn") or (cat == "Zs" and ch != " ")


def dumps_line(obj):
    """One JSON line with readable Arabic letters and marks. Invisible characters (controls, format characters,
    line and paragraph separators, spaces other than U+0020, private use, unassigned code points) and lone
    surrogates are written as \\uXXXX escapes, so that every invisible code point is visible in the file and
    line-based tools do not split a record."""
    s = json.dumps(obj, ensure_ascii=False)
    return "".join(_escape(ch) if ch != "\n" and _invisible(ch) else ch for ch in s)
