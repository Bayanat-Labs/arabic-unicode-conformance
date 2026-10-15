# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Adapters: one per implementation under test.

Each adapter exposes pipelines. A pipeline is one way of calling the implementation, mapped to one suite policy:
  relation "conformance"  the implementation claims to implement that policy (its output is judged against it)
  relation "agreement"    the implementation does not claim any suite policy; the closest policy is named so that its
                          output can be compared, and the result is reported as agreement, not conformance
Third-party tools run in their own environment as separate processes (`--python` points to that environment's
interpreter); nothing from them is imported into this package.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from importlib import resources


@dataclass(frozen=True)
class Pipeline:
    id: str
    policy: str
    relation: str
    call: str


@dataclass
class Adapter:
    name: str
    label: str
    pipelines: list
    accepts_bytes: bool
    needs: str = ""
    notes: str = ""
    options: dict = field(default_factory=dict)

    def version(self):
        raise NotImplementedError

    def run(self, requests):
        """requests: list of {"id", "pipeline", "text"} or {"id", "pipeline", "bytes_hex"}.
        Returns {(id, pipeline): (output, error)}."""
        raise NotImplementedError


def _harness(name):
    return str(resources.files("arabic_unicode_conformance").joinpath("harness").joinpath(name))


def _subprocess_jsonl(cmd, requests, timeout=600):
    payload = "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in requests)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, input=payload.encode("utf-8"), capture_output=True, timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError("%s failed (%d): %s" % (cmd[0], proc.returncode, proc.stderr.decode("utf-8", "replace")[-2000:]))
    out = {}
    for line in proc.stdout.decode("utf-8").split("\n"):
        if line.strip():
            r = json.loads(line)
            out[(r["id"], r["pipeline"])] = (r["output"], r["error"])
    return out


def _version_json(cmd):
    proc = subprocess.run(cmd, capture_output=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError("%s --version failed: %s" % (cmd[0], proc.stderr.decode("utf-8", "replace")[-2000:]))
    return json.loads(proc.stdout.decode("utf-8").strip().splitlines()[-1])


# ------------------------------------------------------------------------------------------- in-process adapters
class UnicodedataAdapter(Adapter):
    def __init__(self, **options):
        super().__init__("python-unicodedata", "Python unicodedata.normalize",
                         [Pipeline("py-nfc", "nfc", "conformance", "unicodedata.normalize('NFC', s)"),
                          Pipeline("py-nfkc", "nfkc", "conformance", "unicodedata.normalize('NFKC', s)")],
                         accepts_bytes=True, notes="Bytes are decoded as strict UTF-8 first.", options=options)

    def version(self):
        return {"tool": "Python unicodedata", "version": sys.version.split()[0],
                "unicode": unicodedata.unidata_version}

    def run(self, requests):
        out = {}
        for r in requests:
            try:
                text = bytes.fromhex(r["bytes_hex"]).decode("utf-8") if "bytes_hex" in r else r["text"]
                form = "NFC" if r["pipeline"] == "py-nfc" else "NFKC"
                out[(r["id"], r["pipeline"])] = (unicodedata.normalize(form, text), None)
            except Exception as exc:
                out[(r["id"], r["pipeline"])] = (None, "%s: %s" % (type(exc).__name__, exc))
        return out


class ArabicNormalizePyAdapter(Adapter):
    POLICIES = ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")

    def __init__(self, **options):
        super().__init__("arabic-normalize-py", "arabic-normalize (Python)",
                         [Pipeline("an-py-" + p, p, "conformance", "arabic_normalize.normalize(s, %r)" % p)
                          for p in self.POLICIES],
                         accepts_bytes=True, needs="the arabic_normalize package importable in this environment",
                         notes="Bytes go through arabic_normalize.normalize_bytes.", options=options)

    def version(self):
        import arabic_normalize as an
        return {"tool": "arabic-normalize (Python)", "version": an.__version__, "unicode": an.UNICODE_VERSION,
                "python": sys.version.split()[0]}

    def run(self, requests):
        import arabic_normalize as an
        out = {}
        for r in requests:
            policy = r["pipeline"][len("an-py-"):]
            try:
                if "bytes_hex" in r:
                    res = an.normalize_bytes(bytes.fromhex(r["bytes_hex"]), policy)
                else:
                    res = an.normalize(r["text"], policy)
                out[(r["id"], r["pipeline"])] = (res, None)
            except Exception as exc:
                out[(r["id"], r["pipeline"])] = (None, "%s: %s" % (type(exc).__name__, getattr(exc, "reason", exc)))
        return out


# ------------------------------------------------------------------------------------------- subprocess adapters
class NodeAdapter(Adapter):
    def run(self, requests):
        cmd = [self.options.get("node") or "node", _harness("node_harness.mjs")] + self._mode()
        return _subprocess_jsonl(cmd, requests)

    def version(self):
        return _version_json([self.options.get("node") or "node", _harness("node_harness.mjs")] + self._mode() + ["--version"])


class IcuNodeAdapter(NodeAdapter):
    def __init__(self, **options):
        super().__init__("icu-node", "Node.js String.prototype.normalize (ICU)",
                         [Pipeline("icu-nfc", "nfc", "conformance", "s.normalize('NFC')"),
                          Pipeline("icu-nfkc", "nfkc", "conformance", "s.normalize('NFKC')")],
                         accepts_bytes=True, needs="node on PATH (or --node)",
                         notes="Bytes are decoded with TextDecoder('utf-8', {fatal: true}) first.", options=options)

    def _mode(self):
        return ["icu"]


class ArabicNormalizeJsAdapter(NodeAdapter):
    POLICIES = ("raw-safe-v1", "bayanat-norm-v1", "asr-eval-v1")

    def __init__(self, **options):
        pipes = [Pipeline("an-js-" + p, p, "conformance", "normalize(s, %r)" % p) for p in self.POLICIES]
        pipes += [Pipeline("an-js-nfc", "nfc", "conformance", "normalizeForm(s, 'NFC')"),
                  Pipeline("an-js-nfkc", "nfkc", "conformance", "normalizeForm(s, 'NFKC')")]
        super().__init__("arabic-normalize-js", "arabic-normalize (JavaScript)", pipes, accepts_bytes=True,
                         needs="node, and --js-path pointing to the js/ folder of an arabic-normalize checkout",
                         notes="Bytes go through normalizeBytes (policies) or a strict TextDecoder (normalizeForm).",
                         options=options)

    def _mode(self):
        js = self.options.get("js_path")
        if not js:
            raise RuntimeError("arabic-normalize-js needs --js-path (the js/ folder of an arabic-normalize checkout)")
        return ["arabic-normalize", js]


class PythonToolAdapter(Adapter):
    script = ""

    def _python(self):
        py = self.options.get("python")
        if not py:
            raise RuntimeError("%s needs --python (the interpreter of an environment where the tool is installed)" % self.name)
        return py

    def run(self, requests):
        return _subprocess_jsonl([self._python(), "-I", _harness(self.script)], requests)

    def version(self):
        return _version_json([self._python(), "-I", _harness(self.script), "--version"])


class CamelAdapter(PythonToolAdapter):
    script = "camel_harness.py"

    def __init__(self, **options):
        super().__init__("camel-tools", "CAMeL Tools",
                         [Pipeline("camel-unicode-nfc", "nfc", "agreement", "normalize_unicode(s, compatibility=False)"),
                          Pipeline("camel-unicode", "nfkc", "agreement", "normalize_unicode(s)"),
                          Pipeline("camel-norm", "bayanat-norm-v1", "agreement",
                                   "normalize_alef_maksura_ar(normalize_alef_ar(dediac_ar(normalize_unicode(s))))"),
                          Pipeline("camel-norm-teh", "asr-eval-v1", "agreement",
                                   "normalize_teh_marbuta_ar(<camel-norm>)")],
                         accepts_bytes=False, needs="--python of an environment with camel-tools", options=options)


class PyArabicAdapter(PythonToolAdapter):
    script = "pyarabic_harness.py"

    def __init__(self, **options):
        super().__init__("pyarabic", "PyArabic",
                         [Pipeline("pyarabic-norm", "bayanat-norm-v1", "agreement",
                                   "normalize_alef(strip_tatweel(strip_diacritics(normalize_ligature(s))))"),
                          Pipeline("pyarabic-norm-teh", "asr-eval-v1", "agreement", "normalize_teh(<pyarabic-norm>)")],
                         accepts_bytes=False, needs="--python of an environment with PyArabic (run as a separate process)",
                         options=options)


class WhisperAdapter(PythonToolAdapter):
    script = "whisper_harness.py"

    def __init__(self, **options):
        super().__init__("whisper-basic", "Whisper BasicTextNormalizer",
                         [Pipeline("whisper-basic", "asr-eval-v1", "agreement", "BasicTextNormalizer()(s)"),
                          Pipeline("whisper-basic-rd", "asr-eval-v1", "agreement",
                                   "BasicTextNormalizer(remove_diacritics=True)(s)")],
                         accepts_bytes=False, needs="--python of an environment with whisper-normalizer",
                         options=options)


ADAPTERS = {cls().name: cls for cls in (UnicodedataAdapter, IcuNodeAdapter, ArabicNormalizePyAdapter,
                                        ArabicNormalizeJsAdapter, CamelAdapter, PyArabicAdapter, WhisperAdapter)}


def get(name, **options):
    if name not in ADAPTERS:
        raise KeyError("unknown adapter %r; known: %s" % (name, ", ".join(ADAPTERS)))
    return ADAPTERS[name](**options)
