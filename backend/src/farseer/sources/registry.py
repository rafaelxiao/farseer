"""
Fetcher registry - manages all available data sources.
"""

from farseer.sources.base import BaseFetcher


class FetcherRegistry:
    """Registry of available data source fetchers."""

    _fetchers: dict[str, BaseFetcher] = {}

    @classmethod
    def register(cls, fetcher: BaseFetcher) -> None:
        """Register a fetcher."""
        cls._fetchers[fetcher.name] = fetcher

    @classmethod
    def get(cls, name: str) -> BaseFetcher | None:
        """Get fetcher by name."""
        return cls._fetchers.get(name)

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered fetcher names."""
        return list(cls._fetchers.keys())
