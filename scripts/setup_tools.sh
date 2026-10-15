#!/usr/bin/env bash
# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
# Create one environment per third-party tool, with the versions used for the published matrix, and check out
# the JavaScript port of arabic-normalize at the pinned commit. Needs uv, git and node.
#   bash scripts/setup_tools.sh TOOLS_DIR
set -euo pipefail
DIR="${1:?usage: setup_tools.sh TOOLS_DIR}"
AN_COMMIT=3ad22326a66596e8dc413321017251eed6e60439
mkdir -p "$DIR"
uv venv -q --python 3.12 "$DIR/camel"
# The normalisation functions of CAMeL Tools need only these packages; --no-deps skips the model stack.
uv pip install -q --python "$DIR/camel/bin/python" --no-deps camel-tools==1.6.0 emoji==2.16.0 six==1.17.0
uv venv -q --python 3.12 "$DIR/pyarabic"
uv pip install -q --python "$DIR/pyarabic/bin/python" PyArabic==0.6.15
uv venv -q --python 3.12 "$DIR/whisper"
uv pip install -q --python "$DIR/whisper/bin/python" whisper-normalizer==0.1.15
if [ ! -d "$DIR/arabic-normalize" ]; then
  git clone -q https://github.com/Bayanat-Labs/arabic-normalize.git "$DIR/arabic-normalize"
fi
git -C "$DIR/arabic-normalize" checkout -q "$AN_COMMIT"
echo "tools ready in $DIR"
