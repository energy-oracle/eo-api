# eo-api

Public REST/GraphQL API Gateway for EnergyOracle.

## Endpoints

- `GET /v1/{country}/pun/latest` - Latest PUN price
- `GET /v1/{country}/pun/historical` - Historical data
- `WS /v1/stream` - Real-time WebSocket

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL + TimescaleDB
- Redis (caching, rate limiting)

## Setup

```bash
pip install -e ".[dev]"
uvicorn api.main:app --reload
```

## License

MIT
