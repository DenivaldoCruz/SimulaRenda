from decimal import ROUND_HALF_UP, Decimal, getcontext

from app.schemas.simulation import (
    ProjectionPoint,
    SimulationParameters,
    SimulationPhase,
    SimulationResults,
)

getcontext().prec = 28
MONEY_QUANT = Decimal("0.01")
MONTHS_IN_YEAR = Decimal(12)
ZERO_MONEY = Decimal("0.00")
ONE = Decimal(1)

PhaseResult = SimulationPhase


def quantize_money(value: Decimal) -> Decimal:
    """Round a monetary value to two decimal places."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_future_value(
    pv: Decimal,
    pmt: Decimal,
    annual_rate: Decimal,
    months: int,
) -> Decimal:
    """Calculate accumulated patrimony from an initial value and monthly contributions.

    Args:
        pv: Current patrimony, in reais.
        pmt: Monthly contribution, in reais.
        annual_rate: Annual real return rate as a decimal fraction.
        months: Number of accumulation months.

    Returns:
        Future value rounded to cents. If the annual rate is zero, returns the
        arithmetic sum of principal and contributions.
    """
    if months <= 0:
        return quantize_money(pv)
    if annual_rate == 0:
        return quantize_money(pv + pmt * Decimal(months))

    monthly_rate = annual_rate / MONTHS_IN_YEAR
    factor = (ONE + monthly_rate) ** months
    future_value = pv * factor + pmt * ((factor - ONE) / monthly_rate)
    return quantize_money(future_value)


def calculate_required_patrimony(
    desired_income: Decimal,
    safe_withdrawal_rate: Decimal,
    active_pensions_income: Decimal,
) -> Decimal:
    """Calculate patrimony required to complement active pensions at retirement.

    Args:
        desired_income: Desired monthly income in reais.
        safe_withdrawal_rate: Annual safe withdrawal rate as a decimal fraction.
        active_pensions_income: Monthly income already provided by active benefits.

    Returns:
        Required patrimony rounded to cents. The net need is clamped to zero when
        benefits already cover the desired income.
    """
    net_monthly_income = max(Decimal(0), desired_income - active_pensions_income)
    return quantize_money(net_monthly_income * MONTHS_IN_YEAR / safe_withdrawal_rate)


def calculate_required_contribution(
    target: Decimal,
    pv: Decimal,
    annual_rate: Decimal,
    months: int,
) -> Decimal:
    """Calculate the monthly contribution required to reach a target patrimony.

    Args:
        target: Target patrimony in reais.
        pv: Current patrimony in reais.
        annual_rate: Annual real return rate as a decimal fraction.
        months: Number of months available for accumulation.

    Returns:
        Required monthly contribution rounded to cents, never negative.
    """
    if months <= 0:
        return ZERO_MONEY
    if annual_rate == 0:
        gap = target - pv
        return quantize_money(max(Decimal(0), gap / Decimal(months)))

    monthly_rate = annual_rate / MONTHS_IN_YEAR
    factor = (ONE + monthly_rate) ** months
    projected_current = pv * factor
    if projected_current >= target:
        return ZERO_MONEY

    contribution = (target - projected_current) * monthly_rate / (factor - ONE)
    return quantize_money(max(Decimal(0), contribution))


def adjust_for_inflation(value: Decimal, inflation_rate: Decimal, years: int) -> Decimal:
    """Adjust a value by annual inflation over a whole-year period.

    Args:
        value: Value to adjust.
        inflation_rate: Annual inflation rate as a decimal fraction.
        years: Number of years to compound.

    Returns:
        Inflation-adjusted value rounded to cents.
    """
    if years <= 0 or inflation_rate == 0:
        return quantize_money(value)
    return quantize_money(value * ((ONE + inflation_rate) ** years))


def _private_pension_end_age(params: SimulationParameters) -> int | None:
    if (
        params.private_pension.modality != "fixed_term"
        or params.private_pension.term_years is None
    ):
        return None
    return params.private_pension.start_age + params.private_pension.term_years


def _is_public_pension_active(params: SimulationParameters, age: int) -> bool:
    return (
        params.public_pension.enabled
        and params.public_pension.start_age is not None
        and params.public_pension.start_age <= age
    )


def _is_private_pension_active(params: SimulationParameters, age: int) -> bool:
    if not params.private_pension.enabled or params.private_pension.start_age is None:
        return False
    if age < params.private_pension.start_age:
        return False

    end_age = _private_pension_end_age(params)
    return end_age is None or age < end_age


def _benefit_amount_at_age(params: SimulationParameters, age: int) -> Decimal:
    amount = Decimal(0)
    if _is_public_pension_active(params, age):
        amount += params.public_pension.monthly_amount
    if _is_private_pension_active(params, age):
        amount += params.private_pension.monthly_amount
    return amount


def _sources_at_age(params: SimulationParameters, age: int, withdrawal: Decimal) -> list[str]:
    sources: list[str] = []
    if withdrawal > 0:
        sources.append("patrimony")
    if _is_private_pension_active(params, age):
        sources.append("private_pension")
    if _is_public_pension_active(params, age):
        sources.append("public_pension")
    return sources


def _event_ages(params: SimulationParameters) -> list[int]:
    ages = {params.retirement_age, params.life_expectancy}
    if params.public_pension.enabled and params.public_pension.start_age is not None:
        ages.add(params.public_pension.start_age)
    if params.private_pension.enabled and params.private_pension.start_age is not None:
        ages.add(params.private_pension.start_age)
        private_end_age = _private_pension_end_age(params)
        if private_end_age is not None:
            ages.add(private_end_age)
    return sorted(age for age in ages if params.retirement_age <= age <= params.life_expectancy)


def simulate_phases(params: SimulationParameters) -> list[PhaseResult]:
    """Build retirement income phases from enabled pension start and end events.

    Args:
        params: Simulation inputs validated by the Pydantic schema.

    Returns:
        Ordered phases from retirement age to life expectancy without gaps or overlaps.
    """
    phases: list[PhaseResult] = []
    ages = _event_ages(params)
    for from_age, to_age in zip(ages, ages[1:], strict=False):
        benefits = _benefit_amount_at_age(params, from_age)
        withdrawal = max(Decimal(0), params.desired_monthly_income - benefits)
        phases.append(
            PhaseResult(
                from_age=from_age,
                to_age=to_age,
                monthly_withdrawal_from_patrimony=quantize_money(withdrawal),
                monthly_income_total=quantize_money(params.desired_monthly_income),
                sources=_sources_at_age(params, from_age, withdrawal),
            )
        )
    return phases


def simulate_projection(
    params: SimulationParameters,
) -> tuple[list[ProjectionPoint], bool, int | None]:
    """Simulate accumulation and withdrawals month by month.

    Args:
        params: Simulation inputs validated by the Pydantic schema.

    Returns:
        A tuple with yearly projection points, whether patrimony was exhausted, and
        the age at first exhaustion when applicable.
    """
    patrimony = params.current_patrimony
    monthly_rate = params.annual_real_return / MONTHS_IN_YEAR
    projection_series = [
        ProjectionPoint(
            age=params.current_age,
            patrimony=quantize_money(patrimony),
            monthly_income=ZERO_MONEY,
        )
    ]

    for age in range(params.current_age + 1, params.retirement_age + 1):
        for _month in range(12):
            patrimony = patrimony * (ONE + monthly_rate) + params.monthly_contribution
        patrimony = max(Decimal(0), patrimony)
        projection_series.append(
            ProjectionPoint(age=age, patrimony=quantize_money(patrimony), monthly_income=ZERO_MONEY)
        )

    patrimony_exhausted = False
    exhaustion_age: int | None = None
    for age in range(params.retirement_age, params.life_expectancy):
        benefits = _benefit_amount_at_age(params, age)
        withdrawal = max(Decimal(0), params.desired_monthly_income - benefits)
        for _month in range(12):
            patrimony = patrimony * (ONE + monthly_rate) - withdrawal
            if patrimony < 0:
                patrimony = Decimal(0)
                if not patrimony_exhausted:
                    patrimony_exhausted = True
                    exhaustion_age = age
        next_age = age + 1
        next_age_income = max(
            params.desired_monthly_income,
            _benefit_amount_at_age(params, next_age),
        )
        projection_series.append(
            ProjectionPoint(
                age=next_age,
                patrimony=quantize_money(patrimony),
                monthly_income=quantize_money(next_age_income),
            )
        )

    return projection_series, patrimony_exhausted, exhaustion_age


def run_full_simulation(params: SimulationParameters) -> SimulationResults:
    """Run the complete SimulaRenda financial simulation.

    Args:
        params: Simulation inputs validated by the Pydantic schema.

    Returns:
        Full simulation results, including contribution needs, phase breakdown,
        yearly projection, viability status, and exhaustion warning.
    """
    accumulation_months = (params.retirement_age - params.current_age) * 12
    active_pensions_at_retirement = _benefit_amount_at_age(params, params.retirement_age)
    required_patrimony = calculate_required_patrimony(
        desired_income=params.desired_monthly_income,
        safe_withdrawal_rate=params.safe_withdrawal_rate,
        active_pensions_income=active_pensions_at_retirement,
    )
    projected_patrimony = calculate_future_value(
        pv=params.current_patrimony,
        pmt=params.monthly_contribution,
        annual_rate=params.annual_real_return,
        months=accumulation_months,
    )
    required_contribution = calculate_required_contribution(
        target=required_patrimony,
        pv=params.current_patrimony,
        annual_rate=params.annual_real_return,
        months=accumulation_months,
    )

    warning_threshold = required_patrimony * Decimal("0.80")
    if projected_patrimony >= required_patrimony:
        feasibility_status = "viable"
    elif projected_patrimony >= warning_threshold:
        feasibility_status = "warning"
    else:
        feasibility_status = "unviable"

    projection_series, patrimony_exhausted, exhaustion_age = simulate_projection(params)

    return SimulationResults(
        required_patrimony=required_patrimony,
        projected_patrimony=projected_patrimony,
        required_monthly_contribution=required_contribution,
        feasibility_status=feasibility_status,
        patrimony_gap=quantize_money(max(Decimal(0), required_patrimony - projected_patrimony)),
        phases=simulate_phases(params),
        projection_series=projection_series,
        patrimony_exhausted=patrimony_exhausted,
        exhaustion_age=exhaustion_age,
    )
