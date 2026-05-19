import re
import numpy as np


def sharpe_annualization_factor(
    time_interval: str, trading_days_per_year: int = 365, trading_hours_per_day: float = 24
) -> float:
    match = re.match(r"(\d+)([dhms])", time_interval.lower())
    if not match:
        raise ValueError("Interval incorrect format, must be like '1d', '6h', '30m', '15s'")

    value, unit = int(match.group(1)), match.group(2)

    if unit == "d":
        periods = trading_days_per_year / value
    elif unit == "h":
        periods = trading_days_per_year * (trading_hours_per_day / value)
    elif unit == "m":
        periods = trading_days_per_year * (trading_hours_per_day * 60 / value)
    elif unit == "s":
        periods = trading_days_per_year * (trading_hours_per_day * 3600 / value)
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    return np.sqrt(periods)
