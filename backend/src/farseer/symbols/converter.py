"""
Symbol conversion between Farseer format and data source formats.
"""

from farseer.symbols.formats import Exchange, SymbolFormat


class SymbolConverter:
    """Convert between Farseer canonical symbols and source-specific formats."""

    # --- yfinance ---
    # yfinance uses: 600519.SS (Shanghai), 000858.SZ (Shenzhen), AAPL (US)

    @staticmethod
    def to_yfinance(symbol: str) -> str:
        """Farseer -> yfinance: 600519.SH -> 600519.SS"""
        code, exchange = SymbolFormat.parse(symbol)
        if exchange == Exchange.SH:
            return f"{code}.SS"
        elif exchange == Exchange.SZ:
            return f"{code}.SZ"
        elif exchange == Exchange.HK:
            return f"{code}.HK"
        else:  # US
            return code

    @staticmethod
    def from_yfinance(yf_symbol: str) -> str:
        """yfinance -> Farseer: 600519.SS -> 600519.SH"""
        if yf_symbol.endswith(".SS"):
            return SymbolFormat.make(yf_symbol[:-3], Exchange.SH)
        elif yf_symbol.endswith(".SZ"):
            return SymbolFormat.make(yf_symbol[:-3], Exchange.SZ)
        elif yf_symbol.endswith(".HK"):
            return SymbolFormat.make(yf_symbol[:-3], Exchange.HK)
        else:
            return SymbolFormat.make(yf_symbol, Exchange.US)

    # --- baostock ---
    # baostock uses: sh.600519 (Shanghai), sz.000858 (Shenzhen)

    @staticmethod
    def to_baostock(symbol: str) -> str:
        """Farseer -> baostock: 600519.SH -> sh.600519"""
        code, exchange = SymbolFormat.parse(symbol)
        if exchange == Exchange.SH:
            return f"sh.{code}"
        elif exchange == Exchange.SZ:
            return f"sz.{code}"
        else:
            raise ValueError(f"baostock does not support exchange: {exchange}")

    @staticmethod
    def from_baostock(bs_symbol: str) -> str:
        """baostock -> Farseer: sh.600519 -> 600519.SH"""
        prefix, code = bs_symbol.split(".", 1)
        if prefix == "sh":
            return SymbolFormat.make(code, Exchange.SH)
        elif prefix == "sz":
            return SymbolFormat.make(code, Exchange.SZ)
        else:
            raise ValueError(f"Unknown baostock prefix: {prefix}")

    # --- tushare ---
    # tushare uses: 600519.SH (same as Farseer!)

    @staticmethod
    def to_tushare(symbol: str) -> str:
        """Farseer -> tushare: 600519.SH -> 600519.SH (no conversion needed)"""
        return symbol

    @staticmethod
    def from_tushare(ts_symbol: str) -> str:
        """tushare -> Farseer: 600519.SH -> 600519.SH (no conversion needed)"""
        return ts_symbol
