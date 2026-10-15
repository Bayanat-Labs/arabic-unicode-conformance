# Adapters

An adapter runs one implementation over the suite. Each adapter has one or more pipelines; a pipeline is one way of calling the implementation, mapped to one suite policy with one of two relations:

- **conformance**: the implementation claims to implement that policy, so its output is judged against it;
- **agreement**: the implementation claims no suite policy. The closest policy is named so that the outputs can be compared. A low agreement says the tool normalises differently from that policy, not that the tool is wrong.

Third-party tools run unmodified, through their public functions, in their own environment and as a separate process (`--python` names that environment's interpreter). Nothing from them is imported into or copied into this package. PyArabic is GPL-licensed and is only ever run this way.

| Adapter | Pipeline | Exact call | Policy | Relation | Raw-byte input |
|---|---|---|---|---|---|
| `python-unicodedata` | `py-nfc` | `unicodedata.normalize('NFC', s)` | `nfc` | conformance | strict UTF-8 decode first |
| | `py-nfkc` | `unicodedata.normalize('NFKC', s)` | `nfkc` | conformance | strict UTF-8 decode first |
| `icu-node` | `icu-nfc` | `s.normalize('NFC')` in Node.js | `nfc` | conformance | `TextDecoder('utf-8', {fatal: true})` first |
| | `icu-nfkc` | `s.normalize('NFKC')` in Node.js | `nfkc` | conformance | same |
| `arabic-normalize-py` | `an-py-<policy>` | `arabic_normalize.normalize(s, policy)` | the same policy | conformance | `arabic_normalize.normalize_bytes` |
| `arabic-normalize-js` | `an-js-<policy>` | `normalize(s, policy)` | the same policy | conformance | `normalizeBytes` |
| | `an-js-nfc`, `an-js-nfkc` | `normalizeForm(s, 'NFC' / 'NFKC')` | `nfc`, `nfkc` | conformance | strict `TextDecoder` first |
| `camel-tools` | `camel-unicode-nfc` | `normalize_unicode(s, compatibility=False)` | `nfc` | agreement | not applicable |
| | `camel-unicode` | `normalize_unicode(s)` | `nfkc` | agreement | not applicable |
| | `camel-norm` | `normalize_alef_maksura_ar(normalize_alef_ar(dediac_ar(normalize_unicode(s))))` | `bayanat-norm-v1` | agreement | not applicable |
| | `camel-norm-teh` | `normalize_teh_marbuta_ar(` the above `)` | `asr-eval-v1` | agreement | not applicable |
| `pyarabic` | `pyarabic-norm` | `normalize_alef(strip_tatweel(strip_diacritics(normalize_ligature(s))))` | `bayanat-norm-v1` | agreement | not applicable |
| | `pyarabic-norm-teh` | `normalize_teh(` the above `)` | `asr-eval-v1` | agreement | not applicable |
| `whisper-basic` | `whisper-basic` | `BasicTextNormalizer()(s)` | `asr-eval-v1` | agreement | not applicable |
| | `whisper-basic-rd` | `BasicTextNormalizer(remove_diacritics=True)(s)` | `asr-eval-v1` | agreement | not applicable |

The pipelines for the third-party tools are reasonable compositions of their documented functions for the stated purpose; other compositions of the same tools exist and would agree more or less. CAMeL Tools functions come from `camel_tools.utils.normalize` and `camel_tools.utils.dediac`; PyArabic functions from `pyarabic.araby`; the Whisper basic normaliser from the `whisper-normalizer` package, which packages the `BasicTextNormalizer` of OpenAI Whisper.

## Checks besides the pass rate

For every output the runner also records:

- `idempotent`: running the same pipeline on its own output gives the same output;
- `output_nfc`: the output is in NFC (not applicable when the output holds a lone surrogate);
- `must_preserve_kept`: every code point in the case's `must_preserve` list is still in the output;
- token agreement ("same tokens" in the matrix): the output and the expectation split on whitespace into the same tokens.

## Adding an adapter

Subclass `Adapter` in `src/arabic_unicode_conformance/adapters.py`, list its pipelines with the policy each one claims or is compared with, implement `run(requests)` (requests are `{"id", "pipeline", "text"}` or `{"id", "pipeline", "bytes_hex"}`; return `{(id, pipeline): (output, error)}`) and `version()`, and register the class in `ADAPTERS`. For a tool in another language or with an incompatible licence, follow the pattern of `harness/*.py` and `harness/node_harness.mjs`: a small script that reads JSON lines on stdin and writes JSON lines on stdout, run as a separate process.
