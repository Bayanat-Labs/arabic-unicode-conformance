# Bayanat-Norm v1: Arabic text normalisation policies (normative text)

| Field | Value |
|---|---|
| Document version | 1.0, 15 October 2026 |
| Policies | `raw-safe-v1`, `bayanat-norm-v1`, `asr-eval-v1` (plus the Unicode baselines `identity`, `nfc`, `nfkc`) |
| Stage definitions | arabic-normalize-spec-1, as implemented by arabic-normalize 0.1.0 (commit `3ad22326a66596e8dc413321017251eed6e60439`) |
| Unicode data | UCD 18.0.0 for the three named policies; see section 6 for `nfc` and `nfkc` |
| Test suite | Arabic Unicode Conformance Suite 0.1.0 (https://github.com/Bayanat-Labs/arabic-unicode-conformance) |
| Licence | CC BY 4.0, Bayanat Labs |

The key words MUST, MUST NOT and SHOULD are used as in RFC 2119. Arabic version: [BAYANAT-NORM-V1.ar.md](BAYANAT-NORM-V1.ar.md).

## 1. Purpose

Arabic text can be normalised in many ways (removing harakat, folding alef forms, mapping presentation forms, removing tatweel and invisible characters), and two tools that both say "normalised Arabic" can give different strings. A word error rate, a deduplication count or a search index built on one is then not comparable with one built on the other. This document names three normalisation policies, defines every step of each and the order of the steps, so that any implementation in any language can reproduce them exactly. The Arabic Unicode Conformance Suite turns the definitions into test cases.

The three policies are the policies of the arabic-normalize library. Each is identified by its id and by the SHA-256 of its canonical policy file:

| Policy | Use | SHA-256 of the policy file |
|---|---|---|
| `raw-safe-v1` | Cleaning only: removes invalid and invisible characters and applies NFC; letters, marks, digits, punctuation and spacing are kept | `57c3d9f03fb9b6854f2527cd1e8a47cadc266f47f02dda94652306dacea03bb5` |
| `bayanat-norm-v1` | A normalised text column for deduplication, statistics and comparison | `ebdb82000d0762a65120ffa9311bc6f01b481b19d4348ea5bedb3ab23d759321` |
| `asr-eval-v1` | Scoring speech recognition output (word and character error rates) | `5d866146536a23b90c0882044dae5f55f2484f0635e206828246eabeb69668de` |

A released policy never changes. A change in behaviour is published under a new policy id (for example `bayanat-norm-v2`), and the old id keeps its definition and its hash.

## 2. Terms

- **Text** is a sequence of Unicode code points. Input given as bytes MUST be valid UTF-8; otherwise it is rejected as a whole (no output).
- **Mark**: a code point of General_Category Mn, Mc or Me.
- **Mark run after X**: the maximal sequence of marks that directly follows code point X.
- **Joining type**: from ArabicShaping.txt. A code point not listed there has joining type T when its General_Category is Mn, Me or Cf, and U otherwise.
- **Harakat**: U+064B..U+0652 (fathatan, dammatan, kasratan, fatha, damma, kasra, shadda, sukun).
- **Quranic mark set Q**: U+0615..U+061A, U+0653, U+0656..U+0658, U+06D6..U+06ED, U+0898..U+089F, U+08CA..U+08E9, U+08F0..U+08F3, U+08FF, U+10EFD..U+10EFF.
- **Honorific set H**: U+0610..U+0614, U+FD40..U+FD4F, U+FDCF, U+FDF0..U+FDFF, U+10ED1..U+10ED8.
- **Presentation form set PF**: code points in U+FB50..U+FDFF or U+FE70..U+FEFF that have a compatibility decomposition in UnicodeData.txt, minus H.
- **Bidi controls**: U+061C, U+200E, U+200F, U+202A..U+202E, U+2066..U+2069. **Zero-width characters**: U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ.
- **Whitespace**: White_Space=Yes in PropList.txt. **Punctuation**: General_Category Pc, Pd, Ps, Pe, Pi, Pf or Po.

## 3. The stages and their order

An implementation MUST apply the stages in this order. A stage marked "keep" does nothing for that policy.

| # | Stage | raw-safe-v1 | bayanat-norm-v1 | asr-eval-v1 |
|---|---|---|---|---|
| 1 | Remove invalid code points | drop | drop | drop |
| 2 | Remove invisible format characters | strip | strip | strip |
| 3 | Arabic presentation forms | keep | map | map |
| 4 | Honorific ligatures | keep | keep (flag) | keep (flag) |
| 5 | Bidi controls and zero-width characters | strip except meaningful | strip except meaningful | strip except meaningful |
| 6 | Canonical normalisation | NFC | NFC | NFC |
| 7 | Tatweel | keep | strip | strip |
| 8 | Harakat | keep | strip | strip |
| 9 | Quranic marks | keep | strip | strip |
| 10 | Superscript alef | keep | strip | strip |
| 11 | Alef variants | keep | map | map |
| 12 | Alef maqsura | keep | to yeh | to yeh |
| 13 | Taa marbuta | keep | keep (flag) | to heh |
| 14 | Hamza carriers | keep | keep | keep |
| 15 | Persian and Urdu letters | keep | keep | keep |
| 16 | Digits | keep | to ASCII | to ASCII |
| 17 | Punctuation | keep | keep | replace with a space |
| 18 | Whitespace | keep | keep | collapse and trim |
| 19 | Latin letter case | keep | keep | keep |
| 20 | Final canonical normalisation | NFC | NFC | NFC |

"Flag" means the character is kept and an implementation that reports flags reports it; flags do not change the output string, and this suite tests only the output string.

### 3.1 Stage 1: remove invalid code points
Remove lone surrogates (U+D800..U+DFFF), noncharacters (Noncharacter_Code_Point=Yes) and control characters (General_Category Cc) except the whitespace controls U+0009..U+000D and U+0085.

### 3.2 Stage 2: remove invisible format characters
Remove U+00AD SOFT HYPHEN, U+2060 WORD JOINER, U+2061..U+2064, U+206A..U+206F, U+FFF9..U+FFFB and U+FEFF (at any position). Variation selectors, tag characters and U+034F are kept.

### 3.3 Stage 3: Arabic presentation forms (map)
Replace every code point of PF with its NFKC form. For example U+FEFB becomes U+0644 U+0627 and U+FE70 becomes U+0020 U+064B, exactly as NFKC gives. Nothing outside PF is changed by this stage: Latin ligatures, fullwidth forms, superscript digits, U+0675..U+0678 and the Arabic Mathematical Alphabetic Symbols keep their form.

### 3.4 Stage 4: honorific ligatures (keep)
Code points of H (for example U+FDF2 and U+FDFA) are kept as single characters. They are not expanded.

### 3.5 Stage 5: bidi controls and zero-width characters (strip except meaningful)
Remove every bidi control and every ZWSP. Remove every ZWNJ and every ZWJ that is not meaningful. The decision for each ZWNJ or ZWJ is made on the text as it enters this stage.

- For a ZWNJ, *prev* is the nearest code point before it and *next* the nearest code point after it, skipping the context-skip set: code points of joining type T, U+200B, U+200C, U+200D, U+0640 and the set Q. A code point of PF counts with the joining type of the letters it maps to (its first non-skipped code point when it is *next*, its last when it is *prev*); a PF code point that maps only to skipped code points is itself skipped.
- A ZWNJ is meaningful when *prev* has joining type D, L or C and *next* has joining type D, R or C, or when the mark run directly before it contains a code point with canonical combining class 9 (virama).
- A ZWJ is meaningful when the nearest code point before it, skipping U+FE0E, U+FE0F, Emoji_Modifier code points and U+E0020..U+E007F, is Extended_Pictographic and the code point directly after it is Extended_Pictographic (an emoji ZWJ sequence), or when the mark run directly before it contains a virama.

### 3.6 Stage 6: canonical normalisation
Apply Unicode Normalization Form C (UAX #15) to the whole text.

### 3.7 Stages 7 to 10
- Stage 7 removes U+0640 TATWEEL.
- Stage 8 removes the harakat U+064B..U+0652.
- Stage 9 removes every code point of Q. Language-specific vowel signs and tone marks (U+0659..U+065F, U+0897, U+08EA..U+08EF, U+08F4..U+08FE) are not in Q and are kept.
- Stage 10 removes U+0670 SUPERSCRIPT ALEF.

### 3.8 Stage 11: alef variants (map)
Replace U+0622, U+0623, U+0625 and U+0671 with U+0627, and remove every U+0653, U+0654 or U+0655 in the mark run after any U+0627. Other alef letters (U+0672, U+0673, U+0675, U+0773, U+0774) are kept.

### 3.9 Stages 12 to 15
- Stage 12 (to yeh) replaces U+0649 with U+064A. U+06CC FARSI YEH is not changed.
- Stage 13 (to heh, asr-eval-v1 only) replaces U+0629 with U+0647.
- Stage 14 keeps U+0624 and U+0626. A combining hamza that is not on an alef is kept.
- Stage 15 keeps Persian and Urdu letters (for example U+06CC, U+06A9, U+06C1, U+06BE) and every other Arabic-script letter, including U+06A4, U+06A8, U+0763, U+06AD, U+067E, U+0686 and U+06AF.

### 3.10 Stage 16: digits (to ASCII)
Replace U+0660..U+0669 and U+06F0..U+06F9 with U+0030..U+0039. U+066B and U+066C are punctuation, not digits.

### 3.11 Stage 17: punctuation (asr-eval-v1: replace with a space)
Replace every punctuation code point with U+0020, so that the words on both sides stay apart.

### 3.12 Stage 18: whitespace (asr-eval-v1: collapse and trim)
Replace every maximal run of whitespace that is not exactly one U+0020 with one U+0020, then remove whitespace at the start and at the end.

### 3.13 Stage 20: final canonical normalisation
Apply NFC again. Removing a tatweel or mapping a letter can leave a sequence that NFC composes: for example alef maqsura + combining hamza becomes yeh + hamza at stage 12, which NFC composes to U+0626.

## 4. Unicode baselines

- `identity`: the output is the input. Bytes that are not valid UTF-8 are rejected.
- `nfc`: UAX #15 Normalization Form C. `nfkc`: UAX #15 Normalization Form KC. Lone surrogates and noncharacters pass through unchanged. Bytes that are not valid UTF-8 are rejected.

## 5. Properties every conforming output has

- **Idempotence**: applying the policy to its own output gives the same output.
- **NFC**: the output of `raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` is in NFC.
- **Letters survive**: no policy removes a code point of General_Category Lo; only stages 3, 11, 12 and 13 replace letters, and dialect letters such as ڤ ڨ ݣ ڭ پ چ گ pass through every policy unchanged. (Tatweel and the small waw and yeh U+06E5 and U+06E6 are not Lo and can be removed.)

## 6. Unicode versions

The three named policies use UCD 18.0.0. The suite's `nfc` and `nfkc` expectations were computed with Python's `unicodedata` at Unicode 16.0.0, and every case uses only code points that were already assigned in Unicode 13.0.0. For such code points Unicode's normalisation stability policy guarantees the same NFC and NFKC results in every later version, so the expectations hold for implementations at Unicode 13.0.0 or later.

## 7. Known edges (these are part of the definition)

- A ZWNJ directly before a tatweel that is followed by a non-joining character is removed even by `raw-safe-v1`, because the neighbour test skips the tatweel.
- ZWSP is removed, not replaced by a space, so two words separated only by a ZWSP run together.
- An isolated haraka presentation form (for example U+FE70) leaves a space behind in `bayanat-norm-v1`, because its NFKC form begins with a space.
- In `asr-eval-v1` the Arabic decimal and thousands separators are punctuation, so `١٬٠٠٠` scores as two tokens.
- Removing the superscript alef from Uthmani spelling leaves the consonantal skeleton (ٱلْكِتَٰبُ becomes الكتب), which is not converted to modern spelling.
- The policies do not depend on a language tag: Farsi yeh and keheh are kept in Arabic text, and a meaningful ZWNJ is kept in Arabic text.

## 8. Claiming conformance

An implementation conforms to a policy when it produces the expected output of that policy for every case of the suite. Report it with the suite version and the result, for example: "conforms to `bayanat-norm-v1` (Arabic Unicode Conformance Suite 0.1.0, 300 of 300 cases)". A tool that implements a different normalisation can still be compared with a policy; report that as agreement, not conformance.
