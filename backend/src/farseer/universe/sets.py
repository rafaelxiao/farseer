"""
Symbol sets for different indices.
Loaded from JSON files in data/ directory.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _load_symbols(filename: str) -> list[str]:
    """Load symbols from JSON file."""
    path = DATA_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


# CSI 300 (沪深300)
CSI300 = _load_symbols("csi300.json")

# CSI 500 (中证500)
CSI500 = _load_symbols("csi500.json")

# Top 100 Liquid ETFs
ETF_TOP100 = _load_symbols("etf_top100.json")
