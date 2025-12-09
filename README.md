# eo-api

REST API for EnergyOracle - UK energy market data for PPA settlement.

## Features

- **System Prices** - Elexon SSP/SBP imbalance prices
- **Day-Ahead Prices** - APXMIDP market index
- **Carbon Intensity** - National Grid gCO2/kWh
- **Fuel Mix** - Generation breakdown by source
- **Settlement Calculator** - PPA settlement with monthly averages
- **Analytics** - Daily/weekly averages, peak/off-peak, statistics, carbon-weighted prices

## Installation

```bash
cd eo-api
pip install -e ".[dev]"
```

## Environment Setup

Create `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

## Running the API

```bash
# Development mode
uvicorn eo_api.main:app --reload

# Or via CLI
eo-api
```

API will be available at `http://localhost:8000`

- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Prices

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uk/prices/system/latest` | GET | Latest system prices |
| `/uk/prices/system/{date}` | GET | System prices by date |
| `/uk/prices/system/range/` | GET | System prices for date range |
| `/uk/prices/system/monthly-avg/{year}/{month}` | GET | Monthly average for PPA |
| `/uk/prices/dayahead/latest` | GET | Latest day-ahead prices |
| `/uk/prices/dayahead/{date}` | GET | Day-ahead prices by date |
| `/uk/prices/dayahead/monthly-avg/{year}/{month}` | GET | Monthly average |

### Carbon

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uk/carbon/intensity/current` | GET | Current carbon intensity |
| `/uk/carbon/intensity/{date}` | GET | Carbon intensity by date |
| `/uk/carbon/intensity/range/` | GET | Carbon intensity range |
| `/uk/carbon/fuelmix/current` | GET | Current fuel mix |
| `/uk/carbon/fuelmix/{date}` | GET | Fuel mix by date |

### Settlement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uk/settlement/calculate` | POST | Calculate PPA settlement |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/uk/analytics/prices/daily` | GET | Daily average prices |
| `/uk/analytics/prices/weekly` | GET | Weekly average prices |
| `/uk/analytics/prices/peak-offpeak` | GET | Peak vs Off-Peak breakdown |
| `/uk/analytics/prices/statistics` | GET | Comprehensive price statistics |
| `/uk/analytics/carbon/weighted-price` | GET | Prices weighted by carbon intensity |
| `/uk/analytics/carbon/daily-summary` | GET | Daily carbon intensity summaries |

## Usage Examples

### Get Monthly Average for PPA Settlement

```bash
curl http://localhost:8000/uk/prices/system/monthly-avg/2025/11
```

Response:
```json
{
  "year": 2025,
  "month": 11,
  "average_price": 72.50,
  "min_price": -15.00,
  "max_price": 285.00,
  "settlement_periods": 1440,
  "unit": "GBP/MWh",
  "price_type": "system"
}
```

### Calculate PPA Settlement

```bash
curl -X POST http://localhost:8000/uk/settlement/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2025,
    "month": 11,
    "discount_per_mwh": 5.00,
    "volume_mwh": 14200,
    "price_type": "system"
  }'
```

Response:
```json
{
  "year": 2025,
  "month": 11,
  "price_type": "system",
  "average_price": 72.50,
  "discount": 5.00,
  "settlement_price": 67.50,
  "volume_mwh": 14200,
  "settlement_amount": 958500.00,
  "settlement_periods": 1440,
  "unit": "GBP/MWh",
  "currency": "GBP"
}
```

### Get Current Carbon Intensity

```bash
curl http://localhost:8000/uk/carbon/intensity/current
```

Response:
```json
{
  "data": [
    {
      "datetime": "2025-12-09T14:30:00+00:00",
      "intensity": 125,
      "intensity_index": "moderate",
      "data_source": "national_grid"
    }
  ],
  "count": 1,
  "unit": "gCO2/kWh"
}
```

### Get Price Statistics

```bash
curl "http://localhost:8000/uk/analytics/prices/statistics?from_date=2025-11-01&to_date=2025-11-30"
```

Response:
```json
{
  "period": "month",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "price_type": "system",
  "average": 76.29,
  "median": 71.52,
  "min": -30.0,
  "max": 247.31,
  "std_dev": 32.62,
  "volatility_pct": 42.8,
  "percentile_25": 60.51,
  "percentile_75": 100.0,
  "percentile_95": 119.72,
  "settlement_periods": 1000,
  "negative_periods": 24,
  "spike_periods": 10,
  "unit": "GBP/MWh"
}
```

### Get Peak vs Off-Peak Breakdown

```bash
curl "http://localhost:8000/uk/analytics/prices/peak-offpeak?from_date=2025-11-01&to_date=2025-11-07"
```

Response:
```json
{
  "period": "week",
  "start_date": "2025-11-01",
  "end_date": "2025-11-07",
  "peak_average": 80.17,
  "peak_min": -15.0,
  "peak_max": 139.9,
  "peak_periods": 120,
  "offpeak_average": 64.94,
  "offpeak_min": -30.0,
  "offpeak_max": 160.0,
  "offpeak_periods": 216,
  "peak_premium": 15.23,
  "peak_premium_pct": 23.5,
  "unit": "GBP/MWh"
}
```

## Project Structure

```
eo-api/
├── pyproject.toml
├── README.md
├── .env.example
├── src/eo_api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── database.py          # Supabase client
│   ├── routers/
│   │   ├── prices.py        # Price endpoints
│   │   ├── carbon.py        # Carbon endpoints
│   │   ├── settlement.py    # Settlement endpoints
│   │   └── analytics.py     # Analytics endpoints
│   ├── services/
│   │   ├── price_service.py
│   │   ├── carbon_service.py
│   │   ├── settlement_service.py
│   │   └── analytics_service.py
│   └── models/
│       └── responses.py     # Pydantic models
└── tests/
```

## PPA Settlement Context

UK PPAs commonly reference these indices:

| Index | Source | Use Case |
|-------|--------|----------|
| System Price | Elexon SSP/SBP | Primary settlement index |
| Day-Ahead | APXMIDP | Forward pricing, discounts |

### Typical PPA Formula

```
Settlement Price = Monthly Average System Price - £X/MWh discount
Settlement Amount = Settlement Price × Volume
```

Example:
```
November 2025: £72.50 avg - £5.00 discount = £67.50/MWh
14,200 MWh × £67.50 = £958,500
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **Supabase** - PostgreSQL database
- **uvicorn** - ASGI server

## License

MIT
