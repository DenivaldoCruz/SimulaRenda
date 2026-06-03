from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.simulation import PrivatePension, PublicPension, SimulationParameters
from app.services.calculator import (
    adjust_for_inflation,
    calculate_future_value,
    calculate_required_contribution,
    calculate_required_patrimony,
    run_full_simulation,
    simulate_phases,
    simulate_projection,
)


def make_params(**overrides: object) -> SimulationParameters:
    data: dict[str, object] = {
        "current_age": 35,
        "current_patrimony": Decimal("100000.00"),
        "monthly_contribution": Decimal("1000.00"),
        "desired_monthly_income": Decimal("8000.00"),
        "retirement_age": 55,
        "life_expectancy": 90,
        "inflation_rate": Decimal("0.04"),
        "annual_real_return": Decimal("0.06"),
        "safe_withdrawal_rate": Decimal("0.04"),
        "public_pension": PublicPension(
            enabled=True,
            monthly_amount=Decimal("2500.00"),
            start_age=65,
        ),
        "private_pension": PrivatePension(
            enabled=True,
            monthly_amount=Decimal("3000.00"),
            start_age=60,
            modality="lifetime",
        ),
    }
    data.update(overrides)
    return SimulationParameters(**data)


def test_calculate_future_value_compounds_patrimony_and_contributions() -> None:
    result = calculate_future_value(
        pv=Decimal("10000.00"),
        pmt=Decimal("1000.00"),
        annual_rate=Decimal("0.12"),
        months=12,
    )

    assert result == Decimal("23950.75")


def test_calculate_future_value_with_zero_rate_only_adds_contributions() -> None:
    result = calculate_future_value(
        pv=Decimal("10000.00"),
        pmt=Decimal("750.00"),
        annual_rate=Decimal("0"),
        months=24,
    )

    assert result == Decimal("28000.00")


def test_calculate_future_value_with_no_months_returns_current_patrimony() -> None:
    assert (
        calculate_future_value(Decimal("1234.567"), Decimal("999"), Decimal("0.10"), 0)
        == Decimal("1234.57")
    )


def test_calculate_required_patrimony_deducts_active_pensions() -> None:
    required = calculate_required_patrimony(
        desired_income=Decimal("10000.00"),
        safe_withdrawal_rate=Decimal("0.04"),
        active_pensions_income=Decimal("2500.00"),
    )

    assert required == Decimal("2250000.00")


def test_calculate_required_patrimony_clamps_when_pensions_cover_income() -> None:
    required = calculate_required_patrimony(
        desired_income=Decimal("5000.00"),
        safe_withdrawal_rate=Decimal("0.04"),
        active_pensions_income=Decimal("7000.00"),
    )

    assert required == Decimal("0.00")


def test_calculate_required_contribution_uses_reverse_pmt_formula() -> None:
    result = calculate_required_contribution(
        target=Decimal("500000.00"),
        pv=Decimal("100000.00"),
        annual_rate=Decimal("0.06"),
        months=120,
    )

    assert result == Decimal("1940.82")


def test_calculate_required_contribution_is_zero_when_patrimony_is_already_sufficient() -> None:
    result = calculate_required_contribution(
        target=Decimal("100000.00"),
        pv=Decimal("100000.00"),
        annual_rate=Decimal("0.12"),
        months=12,
    )

    assert result == Decimal("0.00")


def test_calculate_required_contribution_with_zero_rate_divides_gap_by_months() -> None:
    result = calculate_required_contribution(
        target=Decimal("22000.00"),
        pv=Decimal("10000.00"),
        annual_rate=Decimal("0"),
        months=24,
    )

    assert result == Decimal("500.00")


def test_calculate_required_contribution_with_no_months_is_zero() -> None:
    assert (
        calculate_required_contribution(Decimal("50000"), Decimal("10000"), Decimal("0.06"), 0)
        == Decimal("0.00")
    )


def test_adjust_for_inflation_compounds_value() -> None:
    assert adjust_for_inflation(Decimal("1000.00"), Decimal("0.05"), 3) == Decimal("1157.63")


def test_adjust_for_inflation_with_zero_rate_keeps_value_unchanged() -> None:
    assert adjust_for_inflation(Decimal("1000.00"), Decimal("0"), 30) == Decimal("1000.00")


def test_simulate_phases_when_both_pensions_start_at_retirement_has_no_gap() -> None:
    params = make_params(
        retirement_age=60,
        public_pension=PublicPension(
            enabled=True,
            monthly_amount=Decimal("3000.00"),
            start_age=60,
        ),
        private_pension=PrivatePension(
            enabled=True,
            monthly_amount=Decimal("2500.00"),
            start_age=60,
        ),
    )

    phases = simulate_phases(params)

    assert [(phase.from_age, phase.to_age) for phase in phases] == [(60, 90)]
    assert phases[0].sources == ["patrimony", "private_pension", "public_pension"]
    assert phases[0].monthly_withdrawal_from_patrimony == Decimal("2500.00")


def test_simulate_phases_creates_gap_and_event_phases_without_lacunas() -> None:
    params = make_params()

    phases = simulate_phases(params)

    assert [(phase.from_age, phase.to_age, phase.sources) for phase in phases] == [
        (55, 60, ["patrimony"]),
        (60, 65, ["patrimony", "private_pension"]),
        (65, 90, ["patrimony", "private_pension", "public_pension"]),
    ]
    assert [phase.monthly_withdrawal_from_patrimony for phase in phases] == [
        Decimal("8000.00"),
        Decimal("5000.00"),
        Decimal("2500.00"),
    ]


def test_simulate_phases_ignores_disabled_pensions_when_income_is_covered() -> None:
    params = make_params(
        public_pension=PublicPension(
            enabled=False,
            monthly_amount=Decimal("9999.00"),
            start_age=56,
        ),
        private_pension=PrivatePension(
            enabled=True,
            monthly_amount=Decimal("9000.00"),
            start_age=60,
        ),
    )

    phases = simulate_phases(params)

    assert [(phase.from_age, phase.to_age, phase.sources) for phase in phases] == [
        (55, 60, ["patrimony"]),
        (60, 90, ["private_pension"]),
    ]
    assert phases[1].monthly_withdrawal_from_patrimony == Decimal("0.00")


def test_fixed_term_private_pension_ceases_after_term_and_next_phase_recalculates() -> None:
    params = make_params(
        desired_monthly_income=Decimal("7000.00"),
        public_pension=PublicPension(enabled=False),
        private_pension=PrivatePension(
            enabled=True,
            monthly_amount=Decimal("4000.00"),
            start_age=60,
            modality="fixed_term",
            term_years=10,
        ),
    )

    phases = simulate_phases(params)

    assert [(phase.from_age, phase.to_age, phase.sources) for phase in phases] == [
        (55, 60, ["patrimony"]),
        (60, 70, ["patrimony", "private_pension"]),
        (70, 90, ["patrimony"]),
    ]
    assert [phase.monthly_withdrawal_from_patrimony for phase in phases] == [
        Decimal("7000.00"),
        Decimal("3000.00"),
        Decimal("7000.00"),
    ]


def test_simulate_projection_accumulates_and_withdraws_without_negative_values() -> None:
    params = make_params(
        current_age=40,
        current_patrimony=Decimal("0.00"),
        monthly_contribution=Decimal("1000.00"),
        desired_monthly_income=Decimal("6000.00"),
        retirement_age=41,
        life_expectancy=43,
        annual_real_return=Decimal("0"),
        public_pension=PublicPension(enabled=False),
        private_pension=PrivatePension(enabled=False),
    )

    series, exhausted, exhaustion_age = simulate_projection(params)

    assert [point.age for point in series] == [40, 41, 42, 43]
    assert series[1].patrimony == Decimal("12000.00")
    assert all(point.patrimony >= Decimal("0.00") for point in series)
    assert exhausted is True
    assert exhaustion_age == 41
    assert series[-1].patrimony == Decimal("0.00")


def test_simulate_projection_keeps_fixed_term_pension_only_until_term_end() -> None:
    params = make_params(
        current_age=50,
        current_patrimony=Decimal("0.00"),
        monthly_contribution=Decimal("0.00"),
        desired_monthly_income=Decimal("4000.00"),
        retirement_age=51,
        life_expectancy=53,
        annual_real_return=Decimal("0"),
        public_pension=PublicPension(enabled=False),
        private_pension=PrivatePension(
            enabled=True,
            monthly_amount=Decimal("4000.00"),
            start_age=51,
            modality="fixed_term",
            term_years=1,
        ),
    )

    series, exhausted, exhaustion_age = simulate_projection(params)

    assert series[2].monthly_income == Decimal("4000.00")
    assert series[3].monthly_income == Decimal("4000.00")
    assert exhausted is True
    assert exhaustion_age == 52


def test_run_full_simulation_returns_viable_results_when_projected_meets_required() -> None:
    params = make_params(
        current_patrimony=Decimal("3000000.00"),
        monthly_contribution=Decimal("0.00"),
        public_pension=PublicPension(
            enabled=True,
            monthly_amount=Decimal("4000.00"),
            start_age=55,
        ),
        private_pension=PrivatePension(
            enabled=True,
            monthly_amount=Decimal("4000.00"),
            start_age=55,
        ),
    )

    result = run_full_simulation(params)

    assert result.required_patrimony == Decimal("0.00")
    assert result.required_monthly_contribution == Decimal("0.00")
    assert result.feasibility_status == "viable"
    assert result.patrimony_gap == Decimal("0.00")
    assert result.phases[0].from_age == params.retirement_age


def test_run_full_simulation_returns_warning_at_eighty_percent_threshold() -> None:
    params = make_params(
        current_age=54,
        current_patrimony=Decimal("1000000.00"),
        monthly_contribution=Decimal("0.00"),
        desired_monthly_income=Decimal("4166.666666"),
        retirement_age=55,
        annual_real_return=Decimal("0"),
        public_pension=PublicPension(enabled=False),
        private_pension=PrivatePension(enabled=False),
    )

    result = run_full_simulation(params)

    assert result.required_patrimony == Decimal("1250000.00")
    assert result.projected_patrimony == Decimal("1000000.00")
    assert result.feasibility_status == "warning"


def test_run_full_simulation_returns_unviable_and_exhaustion_for_fifteen_year_gap() -> None:
    params = make_params(
        current_age=54,
        current_patrimony=Decimal("180000.00"),
        monthly_contribution=Decimal("0.00"),
        desired_monthly_income=Decimal("10000.00"),
        retirement_age=55,
        life_expectancy=90,
        annual_real_return=Decimal("0"),
        public_pension=PublicPension(enabled=True, monthly_amount=Decimal("3000.00"), start_age=70),
        private_pension=PrivatePension(enabled=False),
    )

    result = run_full_simulation(params)

    assert [(phase.from_age, phase.to_age) for phase in result.phases] == [(55, 70), (70, 90)]
    assert result.phases[0].sources == ["patrimony"]
    assert result.patrimony_exhausted is True
    assert result.exhaustion_age == 56
    assert result.feasibility_status == "unviable"


def test_schema_validation_makes_safe_withdrawal_rate_division_by_zero_impossible() -> None:
    with pytest.raises(ValidationError):
        make_params(safe_withdrawal_rate=Decimal("0"))
