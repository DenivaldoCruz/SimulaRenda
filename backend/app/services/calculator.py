from decimal import Decimal, ROUND_HALF_UP, getcontext

from app.schemas.simulation import ProjectionPoint, SimulationParameters, SimulationPhase, SimulationResults

getcontext().prec = 28
MONEY_QUANT = Decimal("0.01")
RATE_QUANT = Decimal("0.000001")
MONTHS_IN_YEAR = Decimal(12)


def quantize_money(value: Decimal) -> Decimal:
    """Round a monetary value to two decimal places."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_required_patrimony(
    desired_monthly_income: Decimal,
    monthly_active_benefits: Decimal,
    safe_withdrawal_rate: Decimal,
) -> Decimal:
    """Calculate required patrimony using the safe withdrawal rate."""
    net_monthly_income = max(Decimal(0), desired_monthly_income - monthly_active_benefits)
    return quantize_money(net_monthly_income * MONTHS_IN_YEAR / safe_withdrawal_rate)


def _monthly_rate(annual_real_return: Decimal) -> Decimal:
    return (annual_real_return / MONTHS_IN_YEAR).quantize(RATE_QUANT)


def _future_value(
    current_patrimony: Decimal,
    monthly_contribution: Decimal,
    monthly_rate: Decimal,
    months: int,
) -> Decimal:
    if months <= 0:
        return quantize_money(current_patrimony)
    if monthly_rate == 0:
        return quantize_money(current_patrimony + monthly_contribution * Decimal(months))

    factor = (Decimal(1) + monthly_rate) ** months
    value = current_patrimony * factor + monthly_contribution * ((factor - Decimal(1)) / monthly_rate)
    return quantize_money(value)


def _required_monthly_contribution(
    required_patrimony: Decimal,
    current_patrimony: Decimal,
    monthly_rate: Decimal,
    months: int,
) -> Decimal:
    if months <= 0:
        return Decimal("0.00")
    if monthly_rate == 0:
        gap = required_patrimony - current_patrimony
        return quantize_money(max(Decimal(0), gap / Decimal(months)))

    factor = (Decimal(1) + monthly_rate) ** months
    projected_current = current_patrimony * factor
    if projected_current >= required_patrimony:
        return Decimal("0.00")
    contribution = (required_patrimony - projected_current) * monthly_rate / (factor - Decimal(1))
    return quantize_money(max(Decimal(0), contribution))


def _benefit_amount_at_age(params: SimulationParameters, age: int) -> Decimal:
    amount = Decimal(0)
    if params.public_pension.enabled and params.public_pension.start_age is not None:
        if params.public_pension.start_age <= age:
            amount += params.public_pension.monthly_amount
    if params.private_pension.enabled and params.private_pension.start_age is not None:
        if params.private_pension.start_age <= age:
            amount += params.private_pension.monthly_amount
    return amount


def _build_phases(params: SimulationParameters) -> list[SimulationPhase]:
    event_ages = {params.retirement_age, params.life_expectancy}
    if params.public_pension.enabled and params.public_pension.start_age is not None:
        event_ages.add(params.public_pension.start_age)
    if params.private_pension.enabled and params.private_pension.start_age is not None:
        event_ages.add(params.private_pension.start_age)

    sorted_ages = sorted(age for age in event_ages if params.retirement_age <= age <= params.life_expectancy)
    phases: list[SimulationPhase] = []
    for from_age, to_age in zip(sorted_ages, sorted_ages[1:], strict=False):
        if from_age == to_age:
            continue
        benefits = _benefit_amount_at_age(params, from_age)
        withdrawal = max(Decimal(0), params.desired_monthly_income - benefits)
        sources = ["patrimony"] if withdrawal > 0 else []
        if params.private_pension.enabled and params.private_pension.start_age is not None and params.private_pension.start_age <= from_age:
            sources.append("private_pension")
        if params.public_pension.enabled and params.public_pension.start_age is not None and params.public_pension.start_age <= from_age:
            sources.append("public_pension")
        phases.append(
            SimulationPhase(
                from_age=from_age,
                to_age=to_age,
                monthly_withdrawal_from_patrimony=quantize_money(withdrawal),
                monthly_income_total=quantize_money(params.desired_monthly_income),
                sources=sources,
            )
        )
    return phases


def run_full_simulation(params: SimulationParameters) -> SimulationResults:
    """Run the accumulation and withdrawal projection for a simulation."""
    accumulation_months = (params.retirement_age - params.current_age) * 12
    monthly_rate = _monthly_rate(params.annual_real_return)
    active_benefits_at_start = _benefit_amount_at_age(params, params.retirement_age + 1)
    required_patrimony = calculate_required_patrimony(
        params.desired_monthly_income,
        active_benefits_at_start,
        params.safe_withdrawal_rate,
    )
    projected_patrimony = _future_value(
        params.current_patrimony,
        params.monthly_contribution,
        monthly_rate,
        accumulation_months,
    )
    required_contribution = _required_monthly_contribution(
        required_patrimony,
        params.current_patrimony,
        monthly_rate,
        accumulation_months,
    )

    warning_threshold = required_patrimony * Decimal("0.80")
    if projected_patrimony >= required_patrimony:
        feasibility_status = "viable"
    elif projected_patrimony >= warning_threshold:
        feasibility_status = "warning"
    else:
        feasibility_status = "unviable"

    patrimony = projected_patrimony
    projection_series = [
        ProjectionPoint(age=params.current_age, patrimony=quantize_money(params.current_patrimony), monthly_income=Decimal("0.00")),
        ProjectionPoint(age=params.retirement_age, patrimony=projected_patrimony, monthly_income=Decimal("0.00")),
    ]
    patrimony_exhausted = False
    exhaustion_age: int | None = None

    for age in range(params.retirement_age + 1, params.life_expectancy + 1):
        for _month in range(12):
            benefits = _benefit_amount_at_age(params, age)
            withdrawal = max(Decimal(0), params.desired_monthly_income - benefits)
            patrimony = patrimony * (Decimal(1) + monthly_rate) - withdrawal
            if patrimony < 0:
                patrimony = Decimal(0)
                if not patrimony_exhausted:
                    patrimony_exhausted = True
                    exhaustion_age = age
        projection_series.append(
            ProjectionPoint(
                age=age,
                patrimony=quantize_money(patrimony),
                monthly_income=quantize_money(params.desired_monthly_income),
            )
        )

    return SimulationResults(
        required_patrimony=required_patrimony,
        projected_patrimony=projected_patrimony,
        required_monthly_contribution=required_contribution,
        feasibility_status=feasibility_status,
        patrimony_gap=quantize_money(max(Decimal(0), required_patrimony - projected_patrimony)),
        phases=_build_phases(params),
        projection_series=projection_series,
        patrimony_exhausted=patrimony_exhausted,
        exhaustion_age=exhaustion_age,
    )
