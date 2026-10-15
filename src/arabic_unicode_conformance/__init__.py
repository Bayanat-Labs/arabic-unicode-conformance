# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: Apache-2.0
"""Arabic Unicode Conformance Suite: test cases with expected outputs under named normalisation policies, and a
runner that checks implementations against them."""
from ._version import __version__
from .suite import POLICIES, case_bytes, case_text, load_cases, load_policies

__all__ = ["__version__", "POLICIES", "load_cases", "load_policies", "case_text", "case_bytes"]
