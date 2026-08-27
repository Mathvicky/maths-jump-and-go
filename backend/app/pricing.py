def calculate_car_price(
    driving_miles: float,
    evening_or_weekend: bool = False,
) -> int | None:
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
        return None

    supplement = 10 if evening_or_weekend else 0

    return base_price + supplement
