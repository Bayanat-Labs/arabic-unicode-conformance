# Arabic Unicode Conformance Suite

**Test cases with exact expected outputs for Arabic text normalisation under named policies, and a runner that checks any normaliser against them. By Bayanat Labs.**

Arabic text normalisation (removing harakat and tatweel, folding alef forms, mapping presentation forms such as ﻻ, handling ZWNJ, bidi controls and Arabic-Indic digits) is done differently by every tool, and reports rarely say exactly what was done. Word error rates, deduplication counts and search indexes built with different normalisers are then not comparable. This suite pins the behaviour down: every case gives an input string, its code points and bytes, and the exact output under six named policies. Run your normaliser against it and state which policy it follows.

- Version 0.1.0 (15 October 2026). Cases, policy specs and documentation: CC BY 4.0. Code: Apache-2.0.
- Normative text of the policies: [docs/BAYANAT-NORM-V1.md](docs/BAYANAT-NORM-V1.md) (Arabic: [docs/BAYANAT-NORM-V1.ar.md](docs/BAYANAT-NORM-V1.ar.md)).
- Dataset copy on Hugging Face: [Bayanat-Labs/arabic-unicode-conformance](https://huggingface.co/datasets/Bayanat-Labs/arabic-unicode-conformance).
- The three named policies are those of [arabic-normalize](https://github.com/Bayanat-Labs/arabic-normalize).

arabic-normalize also ships 80 conformance fixtures ([Bayanat-Labs/arabic-normalization-conformance](https://huggingface.co/datasets/Bayanat-Labs/arabic-normalization-conformance)); this suite is broader, with more categories, more policies and more implementations.

## In numbers

<!-- BEGIN numbers -->
| | |
|---|---|
| Test cases | 300 (297 text inputs, 3 raw-byte inputs that are not valid UTF-8) |
| Categories | 18 |
| Policies | 6 (`identity`, `nfc`, `nfkc`, `raw-safe-v1`, `bayanat-norm-v1`, `asr-eval-v1`) |
| Expected outputs | 1800 (every case under every policy) |
| Expected outputs also stated explicitly in the case source and checked against the reference implementation | 473 |
| Levels | 264 `must`, 36 `should` |
| Cases with letters that must survive | 23 |
| Language tags | 14 |
| Implementations in the matrix | 7 (20 pipelines: 12 conformance, 8 agreement) |
<!-- END numbers -->

## Policies

<!-- BEGIN policies -->
| Policy | What it does | Defined by |
|---|---|---|
| `identity` | The output is the input, code point for code point. Input bytes that are not valid UTF-8 are rejected. | definition |
| `nfc` | UAX #15 canonical decomposition, canonical ordering and canonical composition. Lone surrogates and noncharacters pass through unchanged. Input bytes that are not valid UTF-8 are rejected. | Python unicodedata.normalize('NFC'), Unicode 16.0.0 |
| `nfkc` | UAX #15 compatibility decomposition, canonical ordering and canonical composition. Lone surrogates and noncharacters pass through unchanged. Input bytes that are not valid UTF-8 are rejected. | Python unicodedata.normalize('NFKC'), Unicode 16.0.0 |
| `raw-safe-v1` | NFC plus removal of invalid code points and invisible controls (a meaningful ZWNJ or emoji ZWJ is kept). No letter, mark, digit or punctuation is changed. Recipe for text_diac columns and for display or legal uses. | arabic-normalize, SHA-256 `57c3d9f03fb9b685...` |
| `bayanat-norm-v1` | A normalisation policy for text_norm columns. NFC plus mapping of Arabic presentation forms; invisible controls removed except a meaningful ZWNJ or emoji ZWJ; tatweel, harakat, Quranic marks and superscript alef removed; alef variants to bare alef; alef maqsura to yeh; taa marbuta kept and flagged; Arabic-Indic and Extended Arabic-Indic digits to ASCII; honorific ligatures kept and flagged. | arabic-normalize, SHA-256 `ebdb82000d0762a6...` |
| `asr-eval-v1` | bayanat-norm-v1 plus taa marbuta folded to heh, punctuation replaced by spaces and whitespace collapsed. Intended for WER and CER scoring. Lossy: use only for scoring, never as a stored text field. | arabic-normalize, SHA-256 `5d866146536a23b9...` |
<!-- END policies -->

`raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` are defined stage by stage in [docs/BAYANAT-NORM-V1.md](docs/BAYANAT-NORM-V1.md); the YAML specs are in [policies/](policies/).

## Install

The package is not on PyPI yet. Install it from GitHub, pinned to the release tag:

```bash
pip install "git+https://github.com/Bayanat-Labs/arabic-unicode-conformance@v0.1.0"
```

`pip install arabic-unicode-conformance` will work once it is published. The package has no runtime dependencies and needs Python 3.9 or later.

## Use

```bash
arabic-unicode-conformance list                                   # cases, policies, adapters
arabic-unicode-conformance run --impl python-unicodedata          # Python's own NFC and NFKC
arabic-unicode-conformance run --impl arabic-normalize-py --check # exit 1 if a 'must' case fails
arabic-unicode-conformance run --impl pyarabic --python /path/to/env/bin/python --out pyarabic.json
arabic-unicode-conformance report pyarabic.json --out reports/
```

Test your own normaliser directly from Python:

```python
from arabic_unicode_conformance import load_cases, case_text

def my_normalise(text: str) -> str:
    ...

failures = []
for case in load_cases():
    if case["input_kind"] != "text":          # raw-byte cases test UTF-8 decoding
        continue
    text = case_text(case)                    # exact input, rebuilt from the code points
    if my_normalise(text) != case["expected"]["bayanat-norm-v1"]:
        failures.append(case["case_id"])
print(len(failures), "failures")
```

Or read the cases without installing anything: [cases/](cases/) has one JSON Lines file per category. Invisible characters are written as `\uXXXX` escapes in those files, so every code point is visible.

A case looks like this (shortened):

```json
{"case_id": "ar-uc-hamza-011", "category": "hamza", "level": "must", "language_tag": "ar", "input_kind": "text",
 "input": "ىٔ", "input_codepoints": ["U+0649", "U+0654"], "input_utf8_hex": "d989d994",
 "expected": {"identity": "ىٔ", "nfc": "ىٔ", "nfkc": "ىٔ", "raw-safe-v1": "ىٔ", "bayanat-norm-v1": "ئ", "asr-eval-v1": "ئ"},
 "expected_error": null, "must_preserve": [],
 "rationale_en": "Alef maqsura + combining hamza has no precomposed form, so NFC keeps it; bayanat-norm-v1 maps alef maqsura to yeh and the final NFC pass then composes U+0626."}
```

## Categories

<!-- BEGIN categories -->
| Category | Cases | must | should |
|---|---|---|---|
| `alef` | 18 | 15 | 3 |
| `bidi` | 18 | 15 | 3 |
| `confusables` | 12 | 12 | 0 |
| `diacritic_order` | 22 | 17 | 5 |
| `dialect_letters` | 15 | 15 | 0 |
| `digits` | 24 | 22 | 2 |
| `hamza` | 23 | 21 | 2 |
| `joiners` | 18 | 11 | 7 |
| `lam_alef` | 14 | 13 | 1 |
| `malformed` | 14 | 13 | 1 |
| `mixed_script` | 10 | 10 | 0 |
| `presentation_forms` | 26 | 18 | 8 |
| `punctuation` | 14 | 14 | 0 |
| `quranic` | 18 | 16 | 2 |
| `spaces` | 12 | 12 | 0 |
| `taa_marbuta` | 10 | 10 | 0 |
| `tatweel` | 14 | 13 | 1 |
| `yeh` | 18 | 17 | 1 |
<!-- END categories -->

## Conformance matrix

Each row is one way of calling one implementation (a pipeline), compared with one policy. **Conformance** rows are implementations that claim to implement that policy. **Agreement** rows are tools that claim no suite policy; the closest policy is named so their output can be compared, and a low agreement only means the tool normalises differently, not that it is wrong. "Same tokens" ignores differences in whitespace only. Raw-byte cases are not applicable to tools that accept only strings. Full tables, per category and against every policy: [reports/conformance_matrix.html](reports/conformance_matrix.html), [reports/conformance_matrix.csv](reports/conformance_matrix.csv), [reports/conformance_by_category.csv](reports/conformance_by_category.csv), [reports/agreement.csv](reports/agreement.csv). Every output is recorded in [reports/observations.jsonl](reports/observations.jsonl).

<!-- BEGIN matrix -->
| Implementation | Version | Pipeline | Policy | Relation | Pass | Must pass | Same tokens |
|---|---|---|---|---|---|---|---|
| Python unicodedata.normalize | 3.14.7 | `py-nfc` | `nfc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| Python unicodedata.normalize | 3.14.7 | `py-nfkc` | `nfkc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| Node.js String.prototype.normalize (ICU) | 78.2 | `icu-nfc` | `nfc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| Node.js String.prototype.normalize (ICU) | 78.2 | `icu-nfkc` | `nfkc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (Python) | 0.1.0 | `an-py-raw-safe-v1` | `raw-safe-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (Python) | 0.1.0 | `an-py-bayanat-norm-v1` | `bayanat-norm-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (Python) | 0.1.0 | `an-py-asr-eval-v1` | `asr-eval-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (JavaScript) | 0.1.0 | `an-js-raw-safe-v1` | `raw-safe-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (JavaScript) | 0.1.0 | `an-js-bayanat-norm-v1` | `bayanat-norm-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (JavaScript) | 0.1.0 | `an-js-asr-eval-v1` | `asr-eval-v1` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (JavaScript) | 0.1.0 | `an-js-nfc` | `nfc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| arabic-normalize (JavaScript) | 0.1.0 | `an-js-nfkc` | `nfkc` | conformance | 300/300 (100.0%) | 264/264 | 100.0% |
| CAMeL Tools | 1.6.0 | `camel-unicode-nfc` | `nfc` | agreement | 297/297 (100.0%) | 261/261 | 100.0% |
| CAMeL Tools | 1.6.0 | `camel-unicode` | `nfkc` | agreement | 295/297 (99.3%) | 260/261 | 99.3% |
| CAMeL Tools | 1.6.0 | `camel-norm` | `bayanat-norm-v1` | agreement | 178/297 (59.9%) | 162/261 | 62.3% |
| CAMeL Tools | 1.6.0 | `camel-norm-teh` | `asr-eval-v1` | agreement | 156/297 (52.5%) | 143/261 | 55.6% |
| PyArabic | 0.6.15 | `pyarabic-norm` | `bayanat-norm-v1` | agreement | 177/297 (59.6%) | 155/261 | 59.6% |
| PyArabic | 0.6.15 | `pyarabic-norm-teh` | `asr-eval-v1` | agreement | 146/297 (49.2%) | 124/261 | 53.2% |
| Whisper BasicTextNormalizer | 0.1.15 | `whisper-basic` | `asr-eval-v1` | agreement | 79/297 (26.6%) | 75/261 | 40.7% |
| Whisper BasicTextNormalizer | 0.1.15 | `whisper-basic-rd` | `asr-eval-v1` | agreement | 132/297 (44.4%) | 120/261 | 49.8% |
<!-- END matrix -->

Run on 15 October 2026 with:

<!-- BEGIN runs -->
- Python unicodedata.normalize: tool Python unicodedata, version 3.14.7, unicode 16.0.0
- Node.js String.prototype.normalize (ICU): node 22.23.2, icu 78.2, icu_unicode 17.0, tool Node.js String.prototype.normalize (ICU), version 78.2
- arabic-normalize (Python): tool arabic-normalize (Python), version 0.1.0, unicode 18.0.0, python 3.14.7
- arabic-normalize (JavaScript): node 22.23.2, icu 78.2, icu_unicode 17.0, tool arabic-normalize (JavaScript), version 0.1.0, unicode 18.0.0
- CAMeL Tools: tool camel-tools, version 1.6.0, python 3.12.14, unicodedata 15.0.0
- PyArabic: tool PyArabic, version 0.6.15, python 3.12.14, unicodedata 15.0.0
- Whisper BasicTextNormalizer: tool whisper-normalizer, version 0.1.15, python 3.12.14, unicodedata 15.0.0
<!-- END runs -->

Tools were run unmodified, through their public functions; the exact calls are in [docs/ADAPTERS.md](docs/ADAPTERS.md). PyArabic is GPL-licensed and runs only as a separate process; no third-party code is included in this repository. Corrections are welcome at hello@bayanatlabs.com or as a GitHub issue.

## Reproduce the matrix

```bash
pip install "git+https://github.com/Bayanat-Labs/arabic-unicode-conformance@v0.1.0"
pip install "git+https://github.com/Bayanat-Labs/arabic-normalize@3ad22326a66596e8dc413321017251eed6e60439"
git clone https://github.com/Bayanat-Labs/arabic-unicode-conformance && cd arabic-unicode-conformance
bash scripts/setup_tools.sh ../tools        # one environment per tool, pinned versions (needs uv, git, node)
python scripts/run_matrix.py --tools ../tools --out reports --date 2026-10-15
```

## How the cases were made

- Every input was written by Bayanat Labs for this suite (`synthetic: true` on every case); no text is taken from a corpus or from another project's tests. The source is [scripts/cases_source.py](scripts/cases_source.py).
- The `identity`, `nfc` and `nfkc` expectations come from Python's `unicodedata` at Unicode 16.0.0 (Python 3.14). Every input uses only code points that were already assigned in Unicode 13.0.0, and Unicode's normalisation stability policy keeps their NFC and NFKC forms fixed, so the expectations hold for any implementation at Unicode 13.0.0 or later (the tests check them on Python 3.9, whose `unicodedata` is at Unicode 13.0.0).
- The `raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` expectations come from an independent reference implementation written from the stage definitions ([scripts/reference_policies.py](scripts/reference_policies.py)); many are also stated explicitly in the case source, and the build fails if the two differ. The expectations were then compared with arabic-normalize (Python and JavaScript), which passes every case.
- [scripts/build_suite.py](scripts/build_suite.py) (install the build extra first: `pip install -e ".[build]"`) writes the case files and checks that every expected output is a fixed point of its policy. The tests also check, on seeded random Arabic-script strings, that the reference implementation is idempotent, gives NFC output and agrees with arabic-normalize.
- Review status: the cases have not yet been reviewed by native Arabic speakers (`review_status: "pending native review"`).

## Limitations

- The policies are choices, not linguistic truths: folding أ to ا or ى to ي merges some distinct words, and asr-eval-v1 splits numbers at Arabic separators. The suite tests that a normaliser does what a policy says, not that the policy suits every task.
- 300 cases show behaviour; they say nothing about how often each phenomenon occurs in real text.
- Agreement rows depend on how each tool's functions were combined into a pipeline ([docs/ADAPTERS.md](docs/ADAPTERS.md)); another combination of the same tool can agree more or less.
- Bidi display order and glyph shaping are not tested; the suite tests code points in and code points out.

## Layout

| Path | Content |
|---|---|
| `cases/<category>.jsonl` | The cases, one file per category |
| `policies/<policy>.yaml` | Policy specs |
| `docs/` | Normative policy text (English, Arabic) and adapter notes |
| `reports/` | Conformance matrix (CSV, HTML), recorded runs and every observed output |
| `src/arabic_unicode_conformance/` | Runner, adapters, report generator, packaged copy of the cases |
| `scripts/` | Case source, reference implementation, build and matrix scripts |
| `ucd/18.0.0/` | The Unicode Character Database files the reference implementation reads |

## Licence

Code (the `arabic_unicode_conformance` package and `scripts/` except `cases_source.py`): Apache-2.0 ([LICENSE](LICENSE)). Cases, policy specs, documentation and reports: CC BY 4.0 ([LICENSE-data](LICENSE-data)); attribute as "Arabic Unicode Conformance Suite, Bayanat Labs, CC BY 4.0". Unicode Character Database files: Unicode License V3 ([NOTICE-unicode.txt](NOTICE-unicode.txt)).

## Cite

```bibtex
@misc{bayanatlabs_arabic_unicode_conformance_2026,
  title  = {Arabic Unicode Conformance Suite},
  author = {{Bayanat Labs}},
  year   = {2026},
  note   = {Version 0.1.0},
  url    = {https://github.com/Bayanat-Labs/arabic-unicode-conformance}
}
```

See also [CITATION.cff](CITATION.cff). When you report a normalised result, name the policy id and its SHA-256.

## بالعربية

حزمة اختبار مفتوحة لتوحيد النص العربي: لكل حالة نص مدخل ونقاط ترميزه وبايتاته، والناتج الدقيق المتوقع تحت ست سياسات مسمّاة (`identity` و`nfc` و`nfkc` و`raw-safe-v1` و`bayanat-norm-v1` و`asr-eval-v1`). تغطي الحالات التطويل والهمزات وصور الألف والألف المقصورة والتاء المربوطة وترتيب الحركات والعلامات القرآنية والأرقام وأشكال العرض ولام ألف والفاصل غير الواصل ومحارف الاتجاه وعلامات الترقيم والمسافات وحروف اللهجات (ڤ ڨ ݣ ڭ پ چ گ) والمحارف المتشابهة والمدخلات المعيبة. ويشغّل البرنامج المرافق أي أداة توحيد على الحالات ويُخرج مصفوفة مطابقة. النص المعياري للسياسات بالعربية في [docs/BAYANAT-NORM-V1.ar.md](docs/BAYANAT-NORM-V1.ar.md).

*The Arabic text has not yet been reviewed by a native Arabic writer; the English governs.*

Contact and corrections: hello@bayanatlabs.com
