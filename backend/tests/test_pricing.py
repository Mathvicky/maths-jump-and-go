import pytest

from app.pricing import calculate_car_price


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


def test_evening_or_weekend_supplement() -> None:
    assert calculate_car_price(
        driving_miles=4,
        evening_or_weekend=True,
    ) == 55


def test_distance_over_15_miles_requires_manual_quote() -> None:
    assert calculate_car_price(15.1) is None


def test_negative_distance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Driving distance cannot be negative",
    ):
        calculate_car_price(-1)
