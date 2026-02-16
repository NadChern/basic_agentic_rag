import sqlite3
from pydantic import BaseModel, field_validator
from typing import Optional, Literal

DB_PATH = "./db/sales.db"


# Input Models
class MetricsInput(BaseModel):
    metric_type: Literal['forecast_comparison', 'yoy_comparison', 'growth', 'category_breakdown']
    year: int
    period: Literal['monthly', 'quarterly'] = 'monthly'
    period_number: Optional[int] = None
    forecast_values: Optional[dict[int, float]] = None
    compare_year: Optional[int] = None

    @field_validator('forecast_values', mode='before')
    @classmethod
    def convert_forecast_keys(cls, v):
        if v is None:
            return v
        return {int(k): float(val) for k, val in v.items()}


# Output Models
class PeriodResult(BaseModel):
    period_label: str
    period_number: int


class ForecastResult(PeriodResult):
    actual: float
    forecast: float
    variance: float
    variance_pct: float
    status: Literal['above_forecast', 'below_forecast', 'on_target']


class ForecastSummary(BaseModel):
    total_actual: float
    total_forecast: float
    total_variance: float
    total_variance_pct: float


class ForecastComparisonOutput(BaseModel):
    status: Literal['success', 'error']
    year: int
    period: str
    results: list[ForecastResult]
    summary: ForecastSummary


class YoYResult(PeriodResult):
    current_year_value: float
    compare_year_value: float
    change: float
    change_pct: float


class YoYSummary(BaseModel):
    total_current: float
    total_compare: float
    total_change: float
    total_change_pct: float


class YoYComparisonOutput(BaseModel):
    status: Literal['success', 'error']
    current_year: int
    compare_year: int
    period: str
    results: list[YoYResult]
    summary: YoYSummary


class GrowthResult(PeriodResult):
    current: float
    previous: Optional[float]
    growth_pct: Optional[float]


class GrowthOutput(BaseModel):
    status: Literal['success', 'error']
    year: int
    period: str
    results: list[GrowthResult]
    summary: dict


class CategoryResult(BaseModel):
    category: str
    amount: float
    percentage_of_total: float


class CategoryOutput(BaseModel):
    status: Literal['success', 'error']
    year: int
    period: str
    results: list[CategoryResult]
    summary: dict


class ErrorOutput(BaseModel):
    status: Literal['error'] = 'error'
    message: str


def calculate_metrics(
    metric_type: str,
    year: int,
    period: str = 'monthly',
    period_number: int = None,
    forecast_values: dict = None,
    compare_year: int = None
) -> dict:
    """Calculate sales metrics and perform analysis on sales data.

    This tool handles aggregation and mathematical calculations that are difficult
    for LLMs to perform accurately. Use this instead of trying to calculate metrics
    from raw query_sales results.

    Args:
        metric_type: Type of analysis to perform. One of:
            - 'forecast_comparison': Compare actual sales vs forecast values
            - 'yoy_comparison': Year-over-year comparison between two years
            - 'growth': Period-over-period growth rates
            - 'category_breakdown': Sales breakdown by category for a period

        year: Primary year to analyze (e.g., 2025)

        period: Time period granularity - 'monthly' or 'quarterly' (default: 'monthly')

        period_number: Specific month (1-12) or quarter (1-4) to analyze.
            Required for 'category_breakdown'. Optional for others (analyzes all periods if omitted).

        forecast_values: Required for 'forecast_comparison'. Dictionary mapping
            period numbers to forecast amounts. Example: {1: 55000, 2: 58000, ...}

        compare_year: Required for 'yoy_comparison'. The year to compare against.

    Returns:
        dict: Contains 'status' and analysis results specific to metric_type:
            - forecast_comparison: 'results' list with actual, forecast, variance, variance_pct, status
            - yoy_comparison: 'results' list with current_year, previous_year, change, change_pct
            - growth: 'results' list with current, previous, growth_pct per period
            - category_breakdown: 'results' list with category, amount, percentage_of_total

    Examples:
        # Compare 2025 sales with forecast
        calculate_metrics('forecast_comparison', 2025, forecast_values={1: 55000, 2: 58000, ...})

        # Compare 2025 vs 2024 year-over-year
        calculate_metrics('yoy_comparison', 2025, compare_year=2024)

        # Get month-over-month growth for 2025
        calculate_metrics('growth', 2025, 'monthly')

        # Get quarter-over-quarter growth for 2025
        calculate_metrics('growth', 2025, 'quarterly')

        # Break down January 2025 sales by category
        calculate_metrics('category_breakdown', 2025, period_number=1)
    """
    try:
        # Validate and coerce input types
        inputs = MetricsInput(
            metric_type=metric_type,
            year=year,
            period=period,
            period_number=period_number,
            forecast_values=forecast_values,
            compare_year=compare_year
        )

        if inputs.metric_type == 'forecast_comparison':
            return _forecast_comparison(inputs.year, inputs.period, inputs.period_number, inputs.forecast_values)
        elif inputs.metric_type == 'yoy_comparison':
            return _yoy_comparison(inputs.year, inputs.period, inputs.period_number, inputs.compare_year)
        elif inputs.metric_type == 'growth':
            return _growth(inputs.year, inputs.period, inputs.period_number)
        elif inputs.metric_type == 'category_breakdown':
            return _category_breakdown(inputs.year, inputs.period, inputs.period_number)
        else:
            return {
                "status": "error",
                "message": f"Unknown metric_type: {metric_type}. Use one of: forecast_comparison, yoy_comparison, growth, category_breakdown"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _get_sales_by_period(year: int, period: str = 'monthly') -> dict:
    """Get aggregated sales by period (month or quarter)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if period == 'quarterly':
        cursor.execute("""
            SELECT ((month - 1) / 3 + 1) as quarter, SUM(amount) as total
            FROM sales
            WHERE year = ?
            GROUP BY quarter
            ORDER BY quarter
        """, (year,))
    else:
        cursor.execute("""
            SELECT month, SUM(amount) as total
            FROM sales
            WHERE year = ?
            GROUP BY month
            ORDER BY month
        """, (year,))

    results = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return results


def _get_years_with_data() -> list[int]:
    """Get list of years that have sales data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM sales ORDER BY year")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    return years


def _forecast_comparison(year: int, period: str, period_number: int, forecast_values: dict) -> dict:
    """Compare actual sales vs forecast values."""
    if not forecast_values:
        return {"status": "error", "message": "forecast_values is required for forecast_comparison"}

    actuals = _get_sales_by_period(year, period)

    results = []
    period_label = "quarter" if period == 'quarterly' else "month"

    periods_to_check = [period_number] if period_number else sorted(set(actuals.keys()) | set(forecast_values.keys()))

    for p in periods_to_check:
        # Keys are already converted to int by Pydantic validator
        forecast = forecast_values.get(p, 0)
        actual = actuals.get(p, 0)
        variance = actual - forecast
        variance_pct = (variance / forecast * 100) if forecast else 0

        if variance > 0:
            status = "above_forecast"
        elif variance < 0:
            status = "below_forecast"
        else:
            status = "on_target"

        results.append({
            period_label: p,
            "actual": round(actual, 2),
            "forecast": round(forecast, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "status": status
        })

    total_actual = sum(r["actual"] for r in results)
    total_forecast = sum(r["forecast"] for r in results)
    total_variance = total_actual - total_forecast
    total_variance_pct = (total_variance / total_forecast * 100) if total_forecast else 0

    # Get data availability metadata
    available_years = _get_years_with_data()
    has_data = year in available_years

    return {
        "status": "success",
        "year": year,
        "period": period,
        "results": results,
        "summary": {
            "total_actual": round(total_actual, 2),
            "total_forecast": round(total_forecast, 2),
            "total_variance": round(total_variance, 2),
            "total_variance_pct": round(total_variance_pct, 2)
        },
        "data_available_for": [year] if has_data else [],
        "data_missing_for": [] if has_data else [year],
        "note": f"No data found for: [{year}]" if not has_data else None
    }


def _yoy_comparison(year: int, period: str, period_number: int, compare_year: int) -> dict:
    """Year-over-year comparison between two years."""
    if not compare_year:
        return {"status": "error", "message": "compare_year is required for yoy_comparison"}

    current = _get_sales_by_period(year, period)
    previous = _get_sales_by_period(compare_year, period)

    results = []
    period_label = "quarter" if period == 'quarterly' else "month"

    periods_to_check = [period_number] if period_number else sorted(set(current.keys()) | set(previous.keys()))

    for p in periods_to_check:
        curr_val = current.get(p, 0)
        prev_val = previous.get(p, 0)
        change = curr_val - prev_val
        change_pct = (change / prev_val * 100) if prev_val else 0

        results.append({
            period_label: p,
            f"year_{year}": round(curr_val, 2),
            f"year_{compare_year}": round(prev_val, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2)
        })

    total_current = sum(current.values())
    total_previous = sum(previous.values())
    total_change = total_current - total_previous
    total_change_pct = (total_change / total_previous * 100) if total_previous else 0

    # Get data availability metadata
    available_years = _get_years_with_data()
    years_requested = [year, compare_year]
    missing = [y for y in years_requested if y not in available_years]

    return {
        "status": "success",
        "current_year": year,
        "compare_year": compare_year,
        "period": period,
        "results": results,
        "summary": {
            f"total_{year}": round(total_current, 2),
            f"total_{compare_year}": round(total_previous, 2),
            "total_change": round(total_change, 2),
            "total_change_pct": round(total_change_pct, 2)
        },
        "data_available_for": [y for y in years_requested if y in available_years],
        "data_missing_for": missing,
        "note": f"No data found for: {missing}" if missing else None
    }


def _growth(year: int, period: str, period_number: int) -> dict:
    """Calculate period-over-period growth rates."""
    sales = _get_sales_by_period(year, period)

    results = []
    period_label = "quarter" if period == 'quarterly' else "month"
    sorted_periods = sorted(sales.keys())

    periods_to_report = [period_number] if period_number else sorted_periods

    for i, p in enumerate(sorted_periods):
        if p not in periods_to_report:
            continue

        current = sales[p]
        previous = sales.get(sorted_periods[i - 1]) if i > 0 else None
        growth_pct = ((current - previous) / previous * 100) if previous else None

        results.append({
            period_label: p,
            "current": round(current, 2),
            "previous": round(previous, 2) if previous is not None else None,
            "growth_pct": round(growth_pct, 2) if growth_pct is not None else None
        })

    # Calculate average growth rate (excluding first period)
    growth_rates = [r["growth_pct"] for r in results if r["growth_pct"] is not None]
    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else None

    # Get data availability metadata
    available_years = _get_years_with_data()
    has_data = year in available_years

    return {
        "status": "success",
        "year": year,
        "period": period,
        "results": results,
        "summary": {
            "average_growth_pct": round(avg_growth, 2) if avg_growth is not None else None
        },
        "data_available_for": [year] if has_data else [],
        "data_missing_for": [] if has_data else [year],
        "note": f"No data found for: [{year}]" if not has_data else None
    }


def _category_breakdown(year: int, period: str, period_number: int) -> dict:
    """Get sales breakdown by category for a specific period."""
    if not period_number:
        return {"status": "error", "message": "period_number is required for category_breakdown"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if period == 'quarterly':
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM sales
            WHERE year = ? AND ((month - 1) / 3 + 1) = ?
            GROUP BY category
            ORDER BY total DESC
        """, (year, period_number))
        period_label = f"Q{period_number}"
    else:
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM sales
            WHERE year = ? AND month = ?
            GROUP BY category
            ORDER BY total DESC
        """, (year, period_number))
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        period_label = month_names[period_number] if 1 <= period_number <= 12 else f"Month {period_number}"

    rows = cursor.fetchall()
    conn.close()

    total = sum(row[1] for row in rows)

    results = []
    for category, amount in rows:
        pct = (amount / total * 100) if total else 0
        results.append({
            "category": category,
            "amount": round(amount, 2),
            "percentage_of_total": round(pct, 2)
        })

    # Get data availability metadata
    available_years = _get_years_with_data()
    has_data = year in available_years and len(rows) > 0

    return {
        "status": "success",
        "year": year,
        "period": period_label,
        "results": results,
        "summary": {
            "total": round(total, 2),
            "category_count": len(results)
        },
        "data_available_for": [year] if has_data else [],
        "data_missing_for": [] if has_data else [year],
        "note": f"No data found for: [{year}]" if not has_data else None
    }
