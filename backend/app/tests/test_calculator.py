from decimal import Decimal

from app.services.calculator import calculate_required_patrimony


def test_calculate_required_patrimony_clamps_active_benefits() -> None:
    required = calculate_required_patrimony(
        desired_monthly_income=Decimal("10000.00"),
        monthly_active_benefits=Decimal("2500.00"),
        safe_withdrawal_rate=Decimal("0.04"),
    )

    assert required == Decimal("2250000.00")
