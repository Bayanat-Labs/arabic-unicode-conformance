# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""CAMeL Tools adapter process. Runs inside an environment where camel-tools (MIT) is installed and calls only its
public normalisation functions. Protocol: JSON lines {"id", "pipeline", "text"} on stdin, {"id", "pipeline", "output",
"error"} on stdout. `--version` prints the tool version."""
import json
import sys
import unicodedata

if sys.argv[1:] == ["--version"]:
    from importlib.metadata import version
    print(json.dumps({"tool": "camel-tools", "version": version("camel-tools"), "python": sys.version.split()[0],
                      "unicodedata": unicodedata.unidata_version}))
    sys.exit(0)

from camel_tools.utils.dediac import dediac_ar  # noqa: E402
from camel_tools.utils.normalize import (  # noqa: E402
    normalize_alef_ar, normalize_alef_maksura_ar, normalize_teh_marbuta_ar, normalize_unicode)


def _norm(s):
    return normalize_alef_maksura_ar(normalize_alef_ar(dediac_ar(normalize_unicode(s))))


PIPELINES = {
    "camel-unicode-nfc": lambda s: normalize_unicode(s, compatibility=False),
    "camel-unicode": normalize_unicode,
    "camel-norm": _norm,
    "camel-norm-teh": lambda s: normalize_teh_marbuta_ar(_norm(s)),
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
