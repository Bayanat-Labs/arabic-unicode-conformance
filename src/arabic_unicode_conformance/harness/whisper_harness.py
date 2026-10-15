# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Whisper basic text normaliser adapter process. Runs inside an environment where the whisper-normalizer package
(MIT; it packages the BasicTextNormalizer of OpenAI Whisper) is installed. Protocol: JSON lines {"id", "pipeline",
"text"} on stdin, {"id", "pipeline", "output", "error"} on stdout. `--version` prints the tool version."""
import json
import sys
import unicodedata

if sys.argv[1:] == ["--version"]:
    from importlib.metadata import version
    print(json.dumps({"tool": "whisper-normalizer", "version": version("whisper-normalizer"),
                      "python": sys.version.split()[0], "unicodedata": unicodedata.unidata_version}))
    sys.exit(0)

from whisper_normalizer.basic import BasicTextNormalizer  # noqa: E402

PIPELINES = {
    "whisper-basic": BasicTextNormalizer(),
    "whisper-basic-rd": BasicTextNormalizer(remove_diacritics=True),
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
