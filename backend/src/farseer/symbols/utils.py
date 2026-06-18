"""
Symbol utility functions.
"""


def is_etf(symbol: str) -> bool:
    """Check if symbol is an ETF based on code pattern."""
    code = symbol.split(".")[0]
    # SH: 51xxxx, 58xxxx; SZ: 15xxxx
    return (
        (code.startswith("51") or code.startswith("58") or code.startswith("15"))
        and len(code) == 6
    )


def is_stock(symbol: str) -> bool:
    """Check if symbol is a stock (not ETF)."""
    return not is_etf(symbol)
