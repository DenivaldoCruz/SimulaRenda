from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class SimulationState:
    """Estado reativo compartilhado pelos componentes de simulação."""

    current_age: int = 30
    current_patrimony: Decimal = Decimal("0")
    monthly_contribution: Decimal = Decimal("0")
    desired_monthly_income: Decimal = Decimal("0")
    retirement_age: int = 55
    life_expectancy: int = 90
    inflation_rate: Decimal = Decimal("0.045")
    annual_real_return: Decimal = Decimal("0.06")
    safe_withdrawal_rate: Decimal = Decimal("0.04")
    public_pension_enabled: bool = False
    public_pension_amount: Decimal = Decimal("0")
    public_pension_start_age: int = 65
    private_pension_enabled: bool = False
    private_pension_amount: Decimal = Decimal("0")
    private_pension_start_age: int = 60
    private_pension_modality: str = "lifetime"
    private_pension_term_years: int | None = None
    results: dict[str, Any] | None = None
    is_calculating: bool = False
    is_dirty: bool = False
    saved_simulation_id: str | None = None
    saved_simulation_name: str | None = None
