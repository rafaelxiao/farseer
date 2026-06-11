"""
Universe Registry - manages symbol sets and tracks ever-seen symbols.

Symbol sets (CSI300, CSI500, etc.) can change over time as stocks are
added/removed from indices. But once we start tracking a symbol, we
keep fetching it forever.
"""

import json
from pathlib import Path

from farseer.universe.sets import CSI300, CSI500

# Where we persist the "ever seen" symbols
PERSIST_FILE = Path(__file__).parent.parent.parent.parent / "data" / "universe_ever_seen.json"


class UniverseRegistry:
    """Manages symbol sets and tracks ever-seen symbols."""

    # Available symbol sets
    SETS = {
        "csi300": CSI300,
        "csi500": CSI500,
    }

    @classmethod
    def get_set(cls, name: str) -> list[str]:
        """Get a specific symbol set by name."""
        if name not in cls.SETS:
            raise ValueError(f"Unknown set: {name}. Available: {list(cls.SETS.keys())}")
        return cls.SETS[name]

    @classmethod
    def get_all_current(cls) -> list[str]:
        """Get all current symbols from all sets (deduplicated)."""
        seen = set()
        result = []
        for symbols in cls.SETS.values():
            for sym in symbols:
                if sym not in seen:
                    seen.add(sym)
                    result.append(sym)
        return result

    @classmethod
    def load_ever_seen(cls) -> set[str]:
        """Load the set of symbols we've ever fetched."""
        if PERSIST_FILE.exists():
            with open(PERSIST_FILE) as f:
                return set(json.load(f))
        return set()

    @classmethod
    def save_ever_seen(cls, symbols: set[str]):
        """Persist the set of symbols we've ever fetched."""
        PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PERSIST_FILE, "w") as f:
            json.dump(sorted(symbols), f, indent=2)

    @classmethod
    def get_fetch_universe(cls) -> list[str]:
        """
        Get the full list of symbols to fetch.
        Combines all current sets + any previously seen symbols.
        """
        current = set(cls.get_all_current())
        ever_seen = cls.load_ever_seen()

        # Merge
        combined = current | ever_seen

        # Save updated list
        cls.save_ever_seen(combined)

        return sorted(combined)

    @classmethod
    def add_symbol(cls, symbol: str):
        """Manually add a symbol to track."""
        ever_seen = cls.load_ever_seen()
        ever_seen.add(symbol)
        cls.save_ever_seen(ever_seen)

    @classmethod
    def add_symbols(cls, symbols: list[str]):
        """Manually add multiple symbols to track."""
        ever_seen = cls.load_ever_seen()
        ever_seen.update(symbols)
        cls.save_ever_seen(ever_seen)
