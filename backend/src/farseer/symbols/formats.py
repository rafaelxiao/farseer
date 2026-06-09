"""
Farseer Symbol Format: {CODE}.{EXCHANGE}

Exchanges:
  .SH  - Shanghai Stock Exchange
  .SZ  - Shenzhen Stock Exchange
  .HK  - Hong Kong
  .US  - United States (optional suffix)

Examples:
  600519.SH   - Moutai (Shanghai)
  000858.SZ   - Wuliangye (Shenzhen)
  0700.HK     - Tencent (Hong Kong)
  AAPL        - Apple (US, no suffix needed)
  AAPL.US     - Apple (US, explicit)
"""

from enum import Enum


class Exchange(str, Enum):
    SH = "SH"  # Shanghai
    SZ = "SZ"  # Shenzhen
    HK = "HK"  # Hong Kong
    US = "US"  # United States


class SymbolFormat:
    """Farseer canonical symbol format."""

    SEPARATOR = "."

    @staticmethod
    def make(code: str, exchange: Exchange | str) -> str:
        """Create canonical symbol: 600519 + SH -> 600519.SH"""
        if isinstance(exchange, str):
            exchange = Exchange(exchange)
        return f"{code}{SymbolFormat.SEPARATOR}{exchange.value}"

    @staticmethod
    def parse(symbol: str) -> tuple[str, Exchange]:
        """Parse symbol: 600519.SH -> (600519, Exchange.SH)"""
        if SymbolFormat.SEPARATOR in symbol:
            code, exchange_str = symbol.rsplit(SymbolFormat.SEPARATOR, 1)
            return code, Exchange(exchange_str)
        # No suffix - assume US
        return symbol, Exchange.US

    @staticmethod
    def is_valid(symbol: str) -> bool:
        """Check if symbol matches format."""
        try:
            SymbolFormat.parse(symbol)
            return True
        except (ValueError, KeyError):
            return False
