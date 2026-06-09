from datetime import datetime, timezone


async def test_create_and_get_ohlc(client):
    # Create
    payload = {
        "symbol": "AAPL",
        "timeframe": "1d",
        "timestamp": "2024-01-15T00:00:00Z",
        "open": 185.0,
        "high": 188.0,
        "low": 184.0,
        "close": 187.0,
        "volume": 50000000,
    }
    resp = await client.post("/api/v1/ohlc/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["close"] == 187.0

    # Get
    resp = await client.get("/api/v1/ohlc/", params={"symbol": "AAPL", "timeframe": "1d"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["symbol"] == "AAPL"


async def test_batch_create_ohlc(client):
    payload = {
        "items": [
            {
                "symbol": "AAPL",
                "timeframe": "1d",
                "timestamp": f"2024-01-{day:02d}T00:00:00Z",
                "open": 185.0,
                "high": 188.0,
                "low": 184.0,
                "close": 187.0,
                "volume": 50000000,
            }
            for day in range(1, 6)
        ]
    }
    resp = await client.post("/api/v1/ohlc/batch", json=payload)
    assert resp.status_code == 200
    assert len(resp.json()) == 5
