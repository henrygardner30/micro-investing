"""
Pytest configuration for the local deployment test suite.

Puts the local deployment root (for `src.*`) and the shared `core/` package
on the import path so tests can import the modules under test directly.
"""

import sys
from pathlib import Path

LOCAL_ROOT = Path(__file__).parent.parent          # deployments/local
CORE_ROOT = LOCAL_ROOT.parent.parent / 'core'      # repo-root/core

for path in (LOCAL_ROOT, CORE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
