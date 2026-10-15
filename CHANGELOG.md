# Changelog

Case ids are never reused. A changed expectation gets a new case id and the old id is listed as removed.

## 0.1.0 (15 October 2026)

Added
- 300 cases in 18 categories, each with its expected output under six policies: `identity`, `nfc`, `nfkc`, `raw-safe-v1`, `bayanat-norm-v1` and `asr-eval-v1` (policy files of arabic-normalize 0.1.0).
- Normative policy text `docs/BAYANAT-NORM-V1.md` (English) and `docs/BAYANAT-NORM-V1.ar.md` (Arabic).
- Runner and CLI with adapters for Python `unicodedata`, Node.js `String.prototype.normalize` (ICU), arabic-normalize (Python and JavaScript), CAMeL Tools, PyArabic and the Whisper basic text normaliser.
- Conformance matrix in `reports/` (CSV, HTML and every recorded output).
