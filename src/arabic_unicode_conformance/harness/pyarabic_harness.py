# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""PyArabic adapter process. PyArabic is GPL-licensed, so it is never imported by this package: this script runs as
a separate process inside an environment where PyArabic is installed, and calls only documented functions of
pyarabic.araby. Protocol: JSON lines {"id", "pipeline", "text"} on stdin, {"id", "pipeline", "output", "error"} on
stdout. `--version` prints the tool version."""
import json
import sys
import unicodedata
import warnings

warnings.simplefilter("ignore")

if sys.argv[1:] == ["--version"]:
    from importlib.metadata import version
    print(json.dumps({"tool": "PyArabic", "version": version("PyArabic"), "python": sys.version.split()[0],
                      "unicodedata": unicodedata.unidata_version}))
    sys.exit(0)

import pyarabic.araby as A  # noqa: E402


def _norm(s):
    return A.normalize_alef(A.strip_tatweel(A.strip_diacritics(A.normalize_ligature(s))))


PIPELINES = {
    "pyarabic-norm": _norm,
    "pyarabic-norm-teh": lambda s: A.normalize_teh(_norm(s)),
}

for line in sys.stdin:
    rec = json.loads(line)
    out = {"id": rec["id"], "pipeline": rec["pipeline"], "output": None, "error": None}
    try:
        out["output"] = PIPELINES[rec["pipeline"]](rec["text"])
    except Exception as exc:  # recorded as a failure, never fatal
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    sys.stdout.write(json.dumps(out, ensure_ascii=True) + "\n")
sys.stdout.flush()
