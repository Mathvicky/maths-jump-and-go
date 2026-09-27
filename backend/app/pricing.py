from math import ceil


def calculate_car_price(
    driving_miles: float,
    night_rate: bool = False,
) -> int:
    """Return the car call-out price for a driving distance."""

    if driving_miles < 0:
        raise ValueError("Driving distance cannot be negative.")

    if driving_miles <= 5:
        base_price = 45
    elif driving_miles <= 10:
        base_price = 55
    elif driving_miles <= 15:
        base_price = 60
    else:
        base_price = ceil(driving_miles / 15) * 60

    multiplier = 2 if night_rate else 1
    return base_price * multiplier


def is_night_time(
    callout_time: str,
    start_hour: int,
    end_hour: int,
) -> bool:
    """Return whether a local HH:MM call-out time falls in the night window."""

    hour_text, minute_text = callout_time.split(":", maxsplit=1)
    minutes = int(hour_text) * 60 + int(minute_text)
    start_minutes = start_hour * 60
    end_minutes = end_hour * 60

    if start_minutes < end_minutes:
        return start_minutes <= minutes < end_minutes
    if start_minutes > end_minutes:
        return minutes >= start_minutes or minutes < end_minutes
    return True
