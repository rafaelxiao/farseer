"""Universe definitions, symbol helpers, and format converters.

Loads asset JSONs from farseer/assets/, provides symbol classification utilities.
"""

import json
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent / "assets"

def _load(filename: str) -> list[str]:
    path = _ASSETS / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


# ── Universe sets ──

CSI300 = _load("csi300.json")
CSI500 = _load("csi500.json")
ETF_TOP100 = _load("etf_top100.json")
INDICES = _load("indices.json")


# ── Symbol classification ──

def is_etf(symbol: str) -> bool:
    """Check if symbol is an ETF based on code pattern."""
    code = symbol.split(".")[0]
    return (
        (code.startswith("51") or code.startswith("58") or code.startswith("15"))
        and len(code) == 6
    )

def is_stock(symbol: str) -> bool:
    """Check if symbol is a stock (not ETF)."""
    return not is_etf(symbol)


# ── Exchange constants ──

class Exchange:
    SH = "SH"
    SZ = "SZ"
    HK = "HK"
    US = "US"


class SymbolFormat:
    """Farseer canonical symbol format: {CODE}.{EXCHANGE}"""
    SEPARATOR = "."

    @staticmethod
    def make(code: str, exchange: str) -> str:
        return f"{code}{SymbolFormat.SEPARATOR}{exchange}"

    @staticmethod
    def parse(symbol: str) -> "tuple[str, str]":
        if SymbolFormat.SEPARATOR in symbol:
            code, exchange = symbol.rsplit(SymbolFormat.SEPARATOR, 1)
            return code, exchange
        return symbol, Exchange.US

    @staticmethod
    def is_valid(symbol: str) -> bool:
        try:
            SymbolFormat.parse(symbol)
            return True
        except (ValueError, KeyError):
            return False

    # Format identifiers for data sources
    FARSEER = "farseer"
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YAHOO = "yahoo"
    BINANCE = "binance"


# ── Symbol converters ──

_FORMAT_MAP = {
    "SH": {SymbolFormat.BAOSTOCK: "sh", SymbolFormat.YAHOO: "SS"},
    "SZ": {SymbolFormat.BAOSTOCK: "sz", SymbolFormat.YAHOO: "SZ"},
}

def convert(symbol: str, target: str) -> str:
    """Convert a Farseer symbol to another format."""
    if target == SymbolFormat.FARSEER or target == SymbolFormat.TUSHARE:
        return symbol
    code, exchange = symbol.split(".")
    if target == SymbolFormat.AKSHARE:
        return code
    if target == SymbolFormat.BAOSTOCK:
        return f"{_FORMAT_MAP[exchange][target]}.{code}"
    if target == SymbolFormat.YAHOO:
        return f"{code}.{_FORMAT_MAP[exchange][target]}"
    return symbol
