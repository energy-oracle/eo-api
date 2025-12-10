"""Analytics service - advanced calculations for price and carbon data."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from statistics import mean, median, stdev
from supabase import Client

from ..models import (
    DailyAverage,
    DailyAverageResponse,
    WeeklyAverage,
    WeeklyAverageResponse,
    PeakOffPeakBreakdown,
    PriceStatistics,
    CarbonWeightedPrice,
    DailyCarbonSummary,
    DailyCarbonSummaryResponse,
    RenewableGenerationIndex,
    GreenPremium,
)


class AnalyticsService:
    """Service for advanced analytics calculations."""

    # Peak hours: 07:00-19:00 = settlement periods 15-38 (UK time)
    PEAK_PERIODS = set(range(15, 39))

    def __init__(self, db: Client):
        self.db = db

    # ============== Daily Averages ==============

    def get_daily_averages(
        self, from_date: date, to_date: date, price_type: str = "system"
    ) -> DailyAverageResponse:
        """Calculate daily average prices for a date range."""
        table = "system_prices" if price_type == "system" else "day_ahead_prices"

        response = (
            self.db.table(table)
            .select("settlement_date, price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .order("settlement_date")
            .execute()
        )

        # Group by date
        daily_data: dict[date, list[Decimal]] = {}
        for row in response.data:
            d = date.fromisoformat(row["settlement_date"])
            if d not in daily_data:
                daily_data[d] = []
            daily_data[d].append(Decimal(str(row["price"])))

        # Calculate averages
        averages = []
        for d, prices in sorted(daily_data.items()):
            averages.append(
                DailyAverage(
                    date=d,
                    average_price=round(sum(prices) / len(prices), 2),
                    min_price=min(prices),
                    max_price=max(prices),
                    settlement_periods=len(prices),
                )
            )

        return DailyAverageResponse(
            data=averages, count=len(averages), price_type=price_type
        )

    # ============== Weekly Averages ==============

    def get_weekly_averages(
        self, from_date: date, to_date: date, price_type: str = "system"
    ) -> WeeklyAverageResponse:
        """Calculate weekly average prices."""
        table = "system_prices" if price_type == "system" else "day_ahead_prices"

        response = (
            self.db.table(table)
            .select("settlement_date, price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .order("settlement_date")
            .execute()
        )

        # Group by ISO week
        weekly_data: dict[tuple[int, int], dict] = {}
        for row in response.data:
            d = date.fromisoformat(row["settlement_date"])
            year, week, _ = d.isocalendar()
            key = (year, week)

            if key not in weekly_data:
                # Calculate week start (Monday) and end (Sunday)
                week_start = d - timedelta(days=d.weekday())
                week_end = week_start + timedelta(days=6)
                weekly_data[key] = {
                    "week_start": week_start,
                    "week_end": week_end,
                    "week_number": week,
                    "prices": [],
                }
            weekly_data[key]["prices"].append(Decimal(str(row["price"])))

        # Calculate averages
        averages = []
        for (year, week), data in sorted(weekly_data.items()):
            prices = data["prices"]
            averages.append(
                WeeklyAverage(
                    week_start=data["week_start"],
                    week_end=data["week_end"],
                    week_number=data["week_number"],
                    average_price=round(sum(prices) / len(prices), 2),
                    min_price=min(prices),
                    max_price=max(prices),
                    settlement_periods=len(prices),
                )
            )

        return WeeklyAverageResponse(
            data=averages, count=len(averages), price_type=price_type
        )

    # ============== Peak/Off-Peak Breakdown ==============

    def get_peak_offpeak_breakdown(
        self, from_date: date, to_date: date, price_type: str = "system"
    ) -> PeakOffPeakBreakdown:
        """Calculate peak vs off-peak price breakdown."""
        table = "system_prices" if price_type == "system" else "day_ahead_prices"

        response = (
            self.db.table(table)
            .select("settlement_date, settlement_period, price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .execute()
        )

        peak_prices = []
        offpeak_prices = []

        for row in response.data:
            d = date.fromisoformat(row["settlement_date"])
            period = row["settlement_period"]
            price = Decimal(str(row["price"]))

            # Peak = weekday (Mon-Fri) AND peak hours
            is_weekday = d.weekday() < 5
            is_peak_hour = period in self.PEAK_PERIODS

            if is_weekday and is_peak_hour:
                peak_prices.append(price)
            else:
                offpeak_prices.append(price)

        # Calculate stats
        peak_avg = sum(peak_prices) / len(peak_prices) if peak_prices else Decimal(0)
        offpeak_avg = (
            sum(offpeak_prices) / len(offpeak_prices) if offpeak_prices else Decimal(0)
        )
        premium = peak_avg - offpeak_avg
        premium_pct = (premium / offpeak_avg * 100) if offpeak_avg else Decimal(0)

        # Determine period type
        days = (to_date - from_date).days + 1
        if days <= 1:
            period = "day"
        elif days <= 7:
            period = "week"
        else:
            period = "month"

        return PeakOffPeakBreakdown(
            period=period,
            start_date=from_date,
            end_date=to_date,
            peak_average=round(peak_avg, 2),
            peak_min=min(peak_prices) if peak_prices else Decimal(0),
            peak_max=max(peak_prices) if peak_prices else Decimal(0),
            peak_periods=len(peak_prices),
            offpeak_average=round(offpeak_avg, 2),
            offpeak_min=min(offpeak_prices) if offpeak_prices else Decimal(0),
            offpeak_max=max(offpeak_prices) if offpeak_prices else Decimal(0),
            offpeak_periods=len(offpeak_prices),
            peak_premium=round(premium, 2),
            peak_premium_pct=round(premium_pct, 1),
        )

    # ============== Price Statistics ==============

    def get_price_statistics(
        self, from_date: date, to_date: date, price_type: str = "system"
    ) -> PriceStatistics:
        """Calculate comprehensive price statistics."""
        table = "system_prices" if price_type == "system" else "day_ahead_prices"

        response = (
            self.db.table(table)
            .select("price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .execute()
        )

        if not response.data:
            raise ValueError(f"No data found for {from_date} to {to_date}")

        prices = [float(row["price"]) for row in response.data]
        prices_decimal = [Decimal(str(p)) for p in prices]
        prices_sorted = sorted(prices)

        avg = mean(prices)
        std = stdev(prices) if len(prices) > 1 else 0

        # Percentiles
        def percentile(data: list, p: float) -> float:
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            return data[f] + (k - f) * (data[c] - data[f])

        # Period type
        days = (to_date - from_date).days + 1
        if days <= 1:
            period = "day"
        elif days <= 7:
            period = "week"
        elif days <= 31:
            period = "month"
        else:
            period = "year"

        return PriceStatistics(
            period=period,
            start_date=from_date,
            end_date=to_date,
            price_type=price_type,
            average=round(Decimal(str(avg)), 2),
            median=round(Decimal(str(median(prices))), 2),
            min=min(prices_decimal),
            max=max(prices_decimal),
            std_dev=round(Decimal(str(std)), 2),
            volatility_pct=round(Decimal(str(std / avg * 100)) if avg else Decimal(0), 1),
            percentile_25=round(Decimal(str(percentile(prices_sorted, 25))), 2),
            percentile_75=round(Decimal(str(percentile(prices_sorted, 75))), 2),
            percentile_95=round(Decimal(str(percentile(prices_sorted, 95))), 2),
            settlement_periods=len(prices),
            negative_periods=sum(1 for p in prices if p < 0),
            spike_periods=sum(1 for p in prices if p > avg * 2),
        )

    # ============== Carbon-Weighted Prices ==============

    def get_carbon_weighted_price(
        self, from_date: date, to_date: date
    ) -> CarbonWeightedPrice:
        """Calculate prices weighted by carbon intensity."""
        # Get system prices
        prices_response = (
            self.db.table("system_prices")
            .select("settlement_date, settlement_period, price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .execute()
        )

        # Get carbon intensity
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        carbon_response = (
            self.db.table("carbon_intensity")
            .select("datetime, intensity")
            .gte("datetime", start_dt.isoformat())
            .lt("datetime", end_dt.isoformat())
            .execute()
        )

        # Index carbon by datetime (rounded to half-hour)
        carbon_index = {}
        for row in carbon_response.data:
            dt = datetime.fromisoformat(row["datetime"].replace("Z", "+00:00"))
            # Round to nearest half hour
            minute = 0 if dt.minute < 30 else 30
            key = dt.replace(minute=minute, second=0, microsecond=0)
            carbon_index[key] = row["intensity"]

        # Categorize prices by carbon intensity
        all_prices = []
        green_prices = []  # < 100 gCO2/kWh
        brown_prices = []  # > 200 gCO2/kWh
        carbon_values = []

        for row in prices_response.data:
            d = date.fromisoformat(row["settlement_date"])
            period = row["settlement_period"]
            price = float(row["price"])

            # Convert settlement period to datetime
            hour = (period - 1) // 2
            minute = 30 if (period - 1) % 2 else 0
            dt = datetime.combine(d, datetime.min.time()).replace(
                hour=hour, minute=minute, tzinfo=None
            )

            all_prices.append(price)

            # Look up carbon (try with and without timezone)
            carbon = carbon_index.get(dt)
            if carbon is None:
                # Try UTC version
                dt_utc = dt.replace(tzinfo=None)
                carbon = carbon_index.get(dt_utc)

            if carbon is not None:
                carbon_values.append(carbon)
                if carbon < 100:
                    green_prices.append(price)
                elif carbon > 200:
                    brown_prices.append(price)

        # Calculate averages
        avg_price = mean(all_prices) if all_prices else 0
        green_avg = mean(green_prices) if green_prices else avg_price
        brown_avg = mean(brown_prices) if brown_prices else avg_price
        avg_carbon = int(mean(carbon_values)) if carbon_values else 0

        # Period type
        days = (to_date - from_date).days + 1
        period = "day" if days <= 1 else "week" if days <= 7 else "month"

        return CarbonWeightedPrice(
            period=period,
            start_date=from_date,
            end_date=to_date,
            average_price=round(Decimal(str(avg_price)), 2),
            green_average=round(Decimal(str(green_avg)), 2),
            green_periods=len(green_prices),
            green_pct=round(
                Decimal(str(len(green_prices) / len(all_prices) * 100))
                if all_prices
                else Decimal(0),
                1,
            ),
            brown_average=round(Decimal(str(brown_avg)), 2),
            brown_periods=len(brown_prices),
            brown_pct=round(
                Decimal(str(len(brown_prices) / len(all_prices) * 100))
                if all_prices
                else Decimal(0),
                1,
            ),
            green_premium=round(Decimal(str(green_avg - avg_price)), 2),
            avg_carbon_intensity=avg_carbon,
        )

    # ============== Daily Carbon Summary ==============

    def get_daily_carbon_summary(
        self, from_date: date, to_date: date
    ) -> DailyCarbonSummaryResponse:
        """Calculate daily carbon intensity summaries."""
        # Get carbon intensity
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        carbon_response = (
            self.db.table("carbon_intensity")
            .select("datetime, intensity")
            .gte("datetime", start_dt.isoformat())
            .lt("datetime", end_dt.isoformat())
            .order("datetime")
            .execute()
        )

        # Get fuel mix
        fuel_response = (
            self.db.table("fuel_mix")
            .select("datetime, wind, solar, hydro, gas, nuclear, coal, biomass")
            .gte("datetime", start_dt.isoformat())
            .lt("datetime", end_dt.isoformat())
            .execute()
        )

        # Index fuel mix by date
        fuel_by_date: dict[date, list[dict]] = {}
        for row in fuel_response.data:
            dt = datetime.fromisoformat(row["datetime"].replace("Z", "+00:00"))
            d = dt.date()
            if d not in fuel_by_date:
                fuel_by_date[d] = []
            fuel_by_date[d].append(row)

        # Group carbon by date
        carbon_by_date: dict[date, list[int]] = {}
        for row in carbon_response.data:
            dt = datetime.fromisoformat(row["datetime"].replace("Z", "+00:00"))
            d = dt.date()
            if d not in carbon_by_date:
                carbon_by_date[d] = []
            carbon_by_date[d].append(row["intensity"])

        # Calculate daily summaries
        summaries = []
        for d, intensities in sorted(carbon_by_date.items()):
            # Count hours in each band (each reading = 0.5 hours)
            very_low = sum(1 for i in intensities if i < 50) * 0.5
            low = sum(1 for i in intensities if 50 <= i < 100) * 0.5
            moderate = sum(1 for i in intensities if 100 <= i < 200) * 0.5
            high = sum(1 for i in intensities if 200 <= i < 300) * 0.5
            very_high = sum(1 for i in intensities if i >= 300) * 0.5

            # Calculate dominant fuel and renewable %
            dominant_fuel = "unknown"
            renewable_pct = Decimal(0)

            if d in fuel_by_date:
                fuel_totals = {
                    "wind": 0,
                    "solar": 0,
                    "hydro": 0,
                    "gas": 0,
                    "nuclear": 0,
                    "coal": 0,
                    "biomass": 0,
                }
                for fm in fuel_by_date[d]:
                    for fuel in fuel_totals:
                        if fm.get(fuel):
                            fuel_totals[fuel] += float(fm[fuel])

                count = len(fuel_by_date[d])
                if count > 0:
                    for fuel in fuel_totals:
                        fuel_totals[fuel] /= count

                    dominant_fuel = max(fuel_totals, key=fuel_totals.get)
                    renewable_pct = Decimal(
                        str(
                            round(
                                fuel_totals["wind"]
                                + fuel_totals["solar"]
                                + fuel_totals["hydro"],
                                1,
                            )
                        )
                    )

            summaries.append(
                DailyCarbonSummary(
                    date=d,
                    average_intensity=int(mean(intensities)),
                    min_intensity=min(intensities),
                    max_intensity=max(intensities),
                    very_low_hours=Decimal(str(very_low)),
                    low_hours=Decimal(str(low)),
                    moderate_hours=Decimal(str(moderate)),
                    high_hours=Decimal(str(high)),
                    very_high_hours=Decimal(str(very_high)),
                    dominant_fuel=dominant_fuel,
                    renewable_pct=renewable_pct,
                )
            )

        return DailyCarbonSummaryResponse(data=summaries, count=len(summaries))

    # ============== Renewable Generation Index ==============

    def get_renewable_generation_index(
        self, year: int, month: int
    ) -> RenewableGenerationIndex:
        """Calculate renewable generation index for a month."""
        # Calculate date range for the month
        from_date = date(year, month, 1)
        if month == 12:
            to_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            to_date = date(year, month + 1, 1) - timedelta(days=1)

        # Get fuel mix for the month
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        fuel_response = (
            self.db.table("fuel_mix")
            .select("datetime, wind, solar, hydro, biomass, gas, nuclear, coal")
            .gte("datetime", start_dt.isoformat())
            .lt("datetime", end_dt.isoformat())
            .execute()
        )

        if not fuel_response.data:
            raise ValueError(f"No fuel mix data found for {year}-{month:02d}")

        # Calculate averages
        wind_total = 0.0
        solar_total = 0.0
        hydro_total = 0.0
        biomass_total = 0.0
        count = 0

        for row in fuel_response.data:
            wind_total += float(row.get("wind") or 0)
            solar_total += float(row.get("solar") or 0)
            hydro_total += float(row.get("hydro") or 0)
            biomass_total += float(row.get("biomass") or 0)
            count += 1

        wind_avg = wind_total / count if count > 0 else 0
        solar_avg = solar_total / count if count > 0 else 0
        hydro_avg = hydro_total / count if count > 0 else 0
        biomass_avg = biomass_total / count if count > 0 else 0
        total_renewable = wind_avg + solar_avg + hydro_avg + biomass_avg

        # Classify REGO supply
        if total_renewable < 30:
            rego_supply = "low"
        elif total_renewable < 50:
            rego_supply = "medium"
        else:
            rego_supply = "high"

        # Calculate vs previous month
        vs_previous: Decimal | None = None
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        try:
            prev_from = date(prev_year, prev_month, 1)
            if prev_month == 12:
                prev_to = date(prev_year + 1, 1, 1) - timedelta(days=1)
            else:
                prev_to = date(prev_year, prev_month + 1, 1) - timedelta(days=1)

            prev_start_dt = datetime.combine(prev_from, datetime.min.time())
            prev_end_dt = datetime.combine(prev_to, datetime.min.time()) + timedelta(days=1)

            prev_response = (
                self.db.table("fuel_mix")
                .select("wind, solar, hydro, biomass")
                .gte("datetime", prev_start_dt.isoformat())
                .lt("datetime", prev_end_dt.isoformat())
                .execute()
            )

            if prev_response.data:
                prev_total = 0.0
                prev_count = 0
                for row in prev_response.data:
                    prev_total += (
                        float(row.get("wind") or 0)
                        + float(row.get("solar") or 0)
                        + float(row.get("hydro") or 0)
                        + float(row.get("biomass") or 0)
                    )
                    prev_count += 1
                if prev_count > 0:
                    prev_avg = prev_total / prev_count
                    if prev_avg > 0:
                        vs_previous = Decimal(
                            str(round((total_renewable - prev_avg) / prev_avg * 100, 1))
                        )
        except Exception:
            pass  # No previous month data available

        return RenewableGenerationIndex(
            period=f"{year}-{month:02d}",
            start_date=from_date,
            end_date=to_date,
            total_renewable_pct=Decimal(str(round(total_renewable, 1))),
            wind_pct=Decimal(str(round(wind_avg, 1))),
            solar_pct=Decimal(str(round(solar_avg, 1))),
            hydro_pct=Decimal(str(round(hydro_avg, 1))),
            biomass_pct=Decimal(str(round(biomass_avg, 1))),
            vs_previous_month_pct=vs_previous,
            estimated_rego_supply=rego_supply,
            settlement_periods=count,
        )

    # ============== Green Premium ==============

    def get_green_premium(
        self, year: int, month: int, renewable_threshold: int = 50
    ) -> GreenPremium:
        """Calculate green premium - price difference based on renewable %."""
        # Calculate date range for the month
        from_date = date(year, month, 1)
        if month == 12:
            to_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            to_date = date(year, month + 1, 1) - timedelta(days=1)

        # Get system prices
        prices_response = (
            self.db.table("system_prices")
            .select("settlement_date, settlement_period, price")
            .gte("settlement_date", from_date.isoformat())
            .lte("settlement_date", to_date.isoformat())
            .execute()
        )

        if not prices_response.data:
            raise ValueError(f"No price data found for {year}-{month:02d}")

        # Get fuel mix
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1)

        fuel_response = (
            self.db.table("fuel_mix")
            .select("datetime, wind, solar, hydro, biomass")
            .gte("datetime", start_dt.isoformat())
            .lt("datetime", end_dt.isoformat())
            .execute()
        )

        # Index fuel mix by datetime (rounded to half-hour)
        fuel_index: dict[datetime, float] = {}
        for row in fuel_response.data:
            dt = datetime.fromisoformat(row["datetime"].replace("Z", "+00:00"))
            # Round to nearest half hour
            minute = 0 if dt.minute < 30 else 30
            key = dt.replace(minute=minute, second=0, microsecond=0, tzinfo=None)
            renewable_pct = (
                float(row.get("wind") or 0)
                + float(row.get("solar") or 0)
                + float(row.get("hydro") or 0)
                + float(row.get("biomass") or 0)
            )
            fuel_index[key] = renewable_pct

        # Categorize prices by renewable %
        green_prices: list[float] = []
        brown_prices: list[float] = []

        for row in prices_response.data:
            d = date.fromisoformat(row["settlement_date"])
            period = row["settlement_period"]
            price = float(row["price"])

            # Convert settlement period to datetime
            hour = (period - 1) // 2
            minute = 30 if (period - 1) % 2 else 0
            dt = datetime.combine(d, datetime.min.time()).replace(
                hour=hour, minute=minute
            )

            # Look up renewable %
            renewable_pct = fuel_index.get(dt, None)
            if renewable_pct is not None:
                if renewable_pct > renewable_threshold:
                    green_prices.append(price)
                else:
                    brown_prices.append(price)

        # Calculate averages
        if not green_prices and not brown_prices:
            raise ValueError(f"No matched price/fuel data for {year}-{month:02d}")

        green_avg = mean(green_prices) if green_prices else 0
        brown_avg = mean(brown_prices) if brown_prices else 0
        premium = green_avg - brown_avg
        premium_pct = (premium / brown_avg * 100) if brown_avg else 0

        return GreenPremium(
            period=f"{year}-{month:02d}",
            start_date=from_date,
            end_date=to_date,
            green_price_avg=Decimal(str(round(green_avg, 2))),
            green_periods=len(green_prices),
            brown_price_avg=Decimal(str(round(brown_avg, 2))),
            brown_periods=len(brown_prices),
            green_premium=Decimal(str(round(premium, 2))),
            green_premium_pct=Decimal(str(round(premium_pct, 1))),
            renewable_threshold=renewable_threshold,
        )
