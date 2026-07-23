from __future__ import annotations

import sys
from pathlib import Path


GATEWAY_SOURCE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "gateway"
    / "src"
)

gateway_source_path = str(GATEWAY_SOURCE_DIRECTORY)

if gateway_source_path not in sys.path:
    sys.path.insert(0, gateway_source_path)
