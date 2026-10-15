# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Independent reference implementation of the six suite policies, used only to author expectations.

identity, nfc and nfkc come straight from Python's unicodedata (the build records its Unicode version).
raw-safe-v1, bayanat-norm-v1 and asr-eval-v1 are written from the stage definitions in
docs/BAYANAT-NORM-V1.md (which follow arabic-normalize-spec-1). This file does not import or copy the
arabic-normalize library; the build compares its output with the library afterwards, and any difference
is either a case error (fixed in the case) or a library finding (reported, expectation unchanged).

Joining types, White_Space, Extended_Pictographic and Emoji_Modifier come from the UCD 18.0.0 files in
ucd/18.0.0/. General_Category, combining classes, decompositions and NFC/NFKC come from unicodedata; the
build checks that every case uses only code points assigned in that unicodedata version, for which these
properties and the normalisation forms are stable between Unicode versions.
"""
from __future__ import annotations

import gzip
import os
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UCD = os.path.join(ROOT, "ucd", "18.0.0")


def _ranges(fname, wanted):
    out = {}
    with gzip.open(os.path.join(UCD, fname), "rt", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(";")]
            rng, value = parts[0], parts[1]
            if wanted is not None and value not in wanted:
                continue
            lo, _, hi = rng.partition("..")
            lo = int(lo, 16)
            hi = int(hi, 16) if hi else lo
            out.setdefault(value, set()).update(range(lo, hi + 1))
    return out


def _joining():
    jt = {}
    with gzip.open(os.path.join(UCD, "ArabicShaping.txt.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(";")]
            jt[int(parts[0], 16)] = parts[2]
    return jt


_JT = _joining()
_PROPS = _ranges("PropList.txt.gz", {"White_Space", "Noncharacter_Code_Point", "Bidi_Control"})
_EMOJI = _ranges("emoji-data.txt.gz", {"Extended_Pictographic", "Emoji_Modifier"})
WHITE_SPACE = _PROPS["White_Space"]
NONCHAR = _PROPS["Noncharacter_Code_Point"]
BIDI = _PROPS["Bidi_Control"]
EXT_PICT = _EMOJI["Extended_Pictographic"]
EMOJI_MOD = _EMOJI["Emoji_Modifier"]

ZWSP, ZWNJ, ZWJ, TATWEEL = 0x200B, 0x200C, 0x200D, 0x0640
FORMAT_STRIP = {0x00AD, 0x2060, *range(0x2061, 0x2065), *range(0x206A, 0x2070), *range(0xFFF9, 0xFFFC), 0xFEFF}
HONORIFIC = {*range(0x0610, 0x0615), *range(0xFD40, 0xFD50), 0xFDCF, *range(0xFDF0, 0xFE00), *range(0x10ED1, 0x10ED9)}
QURANIC = {*range(0x0615, 0x061B), 0x0653, *range(0x0656, 0x0659), *range(0x06D6, 0x06EE), *range(0x0898, 0x08A0),
           *range(0x08CA, 0x08E3), *range(0x08E3, 0x08EA), *range(0x08F0, 0x08F4), 0x08FF, *range(0x10EFD, 0x10F00)}
HARAKAT = set(range(0x064B, 0x0653))
PUNCT_GC = {"Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po"}


def gc(cp):
    if 0xD800 <= cp <= 0xDFFF:
        return "Cs"
    return unicodedata.category(chr(cp))


def is_mark(cp):
    return gc(cp) in ("Mn", "Mc", "Me")


def joining_type(cp):
    if cp in _JT:
        return _JT[cp]
    return "T" if gc(cp) in ("Mn", "Me", "Cf") else "U"


def is_pf(cp):
    if not (0xFB50 <= cp <= 0xFDFF or 0xFE70 <= cp <= 0xFEFF) or cp in HONORIFIC:
        return False
    return unicodedata.decomposition(chr(cp)).startswith("<")


def nfc(cps):
    return [ord(c) for c in unicodedata.normalize("NFC", "".join(map(chr, cps)))]


def nfkc_cp(cp):
    return [ord(c) for c in unicodedata.normalize("NFKC", chr(cp))]


# --------------------------------------------------------------------------------------------- stages
def reject_invalid(cps):
    def bad(cp):
        if 0xD800 <= cp <= 0xDFFF or cp in NONCHAR:
            return True
        return gc(cp) == "Cc" and not (0x09 <= cp <= 0x0D or cp == 0x85)
    return [c for c in cps if not bad(c)]


def strip_controls(cps):
    return [c for c in cps if c not in FORMAT_STRIP]


def presentation_forms_map(cps):
    out = []
    for c in cps:
        out.extend(nfkc_cp(c) if is_pf(c) else [c])
    return out


def _skippable(cp):
    return joining_type(cp) == "T" or cp in (ZWSP, ZWNJ, ZWJ, TATWEEL) or cp in QURANIC


def _context_jt(cp, side):
    """Joining type of a code point seen as context; None when it is skipped. A presentation form takes the
    joining type of the letters it maps to (its first non-skipped code point as next, its last as prev)."""
    if is_pf(cp):
        seq = [c for c in nfkc_cp(cp) if not _skippable(c)]
        if not seq:
            return None
        return joining_type(seq[0] if side == "next" else seq[-1])
    if _skippable(cp):
        return None
    return joining_type(cp)


def _virama_before(cps, i):
    j = i - 1
    while j >= 0 and is_mark(cps[j]):
        if unicodedata.combining(chr(cps[j])) == 9:
            return True
        j -= 1
    return False


def _zwnj_meaningful(cps, i):
    if _virama_before(cps, i):
        return True
    prev = nxt = None
    for j in range(i - 1, -1, -1):
        t = _context_jt(cps[j], "prev")
        if t is not None:
            prev = t
            break
    for j in range(i + 1, len(cps)):
        t = _context_jt(cps[j], "next")
        if t is not None:
            nxt = t
            break
    return prev in ("D", "L", "C") and nxt in ("D", "R", "C")


def _zwj_meaningful(cps, i):
    if _virama_before(cps, i):
        return True
    j = i - 1
    while j >= 0 and (cps[j] in (0xFE0E, 0xFE0F) or cps[j] in EMOJI_MOD or 0xE0020 <= cps[j] <= 0xE007F):
        j -= 1
    before = j >= 0 and cps[j] in EXT_PICT
    after = i + 1 < len(cps) and cps[i + 1] in EXT_PICT
    return before and after


def bidi_zw_strip_except_meaningful(cps):
    out = []
    for i, c in enumerate(cps):
        if c in BIDI or c == ZWSP:
            continue
        if c == ZWNJ and not _zwnj_meaningful(cps, i):
            continue
        if c == ZWJ and not _zwj_meaningful(cps, i):
            continue
        out.append(c)
    return out


def alef_variants_map(cps):
    out = []
    after_alef = False
    for c in cps:
        if c in (0x0622, 0x0623, 0x0625, 0x0671):
            c = 0x0627
        if c == 0x0627:
            out.append(c)
            after_alef = True
            continue
        if after_alef and is_mark(c):
            if c not in (0x0653, 0x0654, 0x0655):
                out.append(c)
            continue
        after_alef = False
        out.append(c)
    return out


def collapse_whitespace(cps):
    out, run = [], []
    for c in cps + [None]:
        if c is not None and c in WHITE_SPACE:
            run.append(c)
            continue
        if run:
            out.extend([0x20] if run != [0x20] else run)
            run = []
        if c is not None:
            out.append(c)
    while out and out[0] in WHITE_SPACE:
        out.pop(0)
    while out and out[-1] in WHITE_SPACE:
        out.pop()
    return out


def arabic_normalize_policy(text, policy):
    """raw-safe-v1, bayanat-norm-v1 or asr-eval-v1, written from the stage table."""
    norm = policy in ("bayanat-norm-v1", "asr-eval-v1")
    cps = [ord(c) for c in text]
    cps = reject_invalid(cps)                                   # 1
    cps = strip_controls(cps)                                   # 2
    if norm:
        cps = presentation_forms_map(cps)                       # 3 (4: honorifics kept)
    cps = bidi_zw_strip_except_meaningful(cps)                  # 5
    cps = nfc(cps)                                              # 6
    if norm:
        cps = [c for c in cps if c != TATWEEL]                  # 7
        cps = [c for c in cps if c not in HARAKAT]              # 8
        cps = [c for c in cps if c not in QURANIC]              # 9
        cps = [c for c in cps if c != 0x0670]                   # 10
        cps = alef_variants_map(cps)                            # 11
        cps = [0x064A if c == 0x0649 else c for c in cps]       # 12
        if policy == "asr-eval-v1":
            cps = [0x0647 if c == 0x0629 else c for c in cps]   # 13
        cps = [0x30 + c - 0x0660 if 0x0660 <= c <= 0x0669 else
               0x30 + c - 0x06F0 if 0x06F0 <= c <= 0x06F9 else c for c in cps]  # 16
        if policy == "asr-eval-v1":
            cps = [0x20 if gc(c) in PUNCT_GC else c for c in cps]  # 17
            cps = collapse_whitespace(cps)                      # 18
    cps = nfc(cps)                                              # 20
    return "".join(map(chr, cps))


POLICIES = ("identity", "nfc", "nfkc", "raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")


def apply(policy, text):
    if policy == "identity":
        return text
    if policy == "nfc":
        return unicodedata.normalize("NFC", text)
    if policy == "nfkc":
        return unicodedata.normalize("NFKC", text)
    return arabic_normalize_policy(text, policy)
