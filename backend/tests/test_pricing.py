import pytest

from app.pricing import calculate_car_price, is_night_time


@pytest.mark.parametrize(
    ("driving_miles", "expected_price"),
    [
        (0, 45),
        (3.5, 45),
        (5, 45),
        (5.1, 55),
        (10, 55),
        (10.1, 60),
        (15, 60),
    ],
)
def test_standard_car_prices(
    driving_miles: float,
    expected_price: int,
) -> None:
    assert calculate_car_price(driving_miles) == expected_price


def test_night_rate_doubles_base_price() -> None:
    assert calculate_car_price(
        driving_miles=4,
        night_rate=True,
    ) == 90


def test_exactly_15_miles_uses_standard_highest_band() -> None:
    assert calculate_car_price(15) == 60


def test_first_out_of_area_band_starts_after_15_miles() -> None:
    assert calculate_car_price(15.1) == 120


@pytest.mark.parametrize(
    ("driving_miles", "expected_price"),
    [
        (18, 120),
        (30, 120),
        (30.1, 180),
        (35, 180),
        (60, 240),
        (60.1, 300),
        (100, 420),
        (120, 480),
        (300, 1200),
        (376.3, 1560),
    ],
)
def test_long_distance_15_mile_bands(
    driving_miles: float,
    expected_price: int,
) -> None:
    assert calculate_car_price(driving_miles) == expected_price


def test_night_doubles_long_distance_band_once() -> None:
    assert calculate_car_price(376.3, night_rate=True) == 3120


@pytest.mark.parametrize(
    ("callout_time", "expected"),
    [
        ("21:59", False),
        ("22:00", True),
        ("23:45", True),
        ("05:59", True),
        ("06:00", True),
        ("06:59", True),
        ("07:00", False),
        ("12:00", False),
    ],
)
def test_configurable_overnight_window(callout_time: str, expected: bool) -> None:
    assert is_night_time(callout_time, start_hour=22, end_hour=7) is expected


def test_negative_distance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Driving distance cannot be negative",
    ):
        calculate_car_price(-1)
