from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any


class FeasibilityStatus(StrEnum):
    VIABLE = "viable"
    WARNING = "warning"
    UNVIABLE = "unviable"


@dataclass
class SimulationState:
    """Estado reativo compartilhado pelos componentes de simulação da UI."""

    # --- Inputs: Situação Atual ---
    current_age: int = 30
    current_patrimony: Decimal = Decimal("0")
    monthly_contribution: Decimal = Decimal("1000")

    # --- Inputs: Metas ---
    desired_monthly_income: Decimal = Decimal("10000")
    retirement_age: int = 55
    life_expectancy: int = 90

    # --- Inputs: Parâmetros Econômicos ---
    inflation_rate: Decimal = Decimal("0.045")
    annual_real_return: Decimal = Decimal("0.06")
    safe_withdrawal_rate: Decimal = Decimal("0.04")

    # --- Inputs: Aposentadoria Pública ---
    public_pension_enabled: bool = False
    public_pension_amount: Decimal = Decimal("0")
    public_pension_start_age: int = 65
    public_pension_in_today_reais: bool = True

    # --- Inputs: Previdência Privada ---
    private_pension_enabled: bool = False
    private_pension_amount: Decimal = Decimal("0")
    private_pension_start_age: int = 60
    private_pension_modality: str = "lifetime"
    private_pension_term_years: int | None = None
    private_pension_in_today_reais: bool = True

    # --- Outputs (preenchidos pelo calculator) ---
    results: dict[str, Any] | None = None
    is_calculating: bool = False

    # --- Metadados de persistência ---
    is_dirty: bool = False
    saved_simulation_id: str | None = None
    saved_simulation_name: str | None = None

    def to_parameters_dict(self) -> dict[str, Any]:
        """Converte state para o schema SimulationParameters (usado no save)."""
        return {
            "current_age": self.current_age,
            "current_patrimony": float(self.current_patrimony),
            "monthly_contribution": float(self.monthly_contribution),
            "desired_monthly_income": float(self.desired_monthly_income),
            "retirement_age": self.retirement_age,
            "life_expectancy": self.life_expectancy,
            "inflation_rate": float(self.inflation_rate),
            "annual_real_return": float(self.annual_real_return),
            "safe_withdrawal_rate": float(self.safe_withdrawal_rate),
            "public_pension": {
                "enabled": self.public_pension_enabled,
                "monthly_amount": float(self.public_pension_amount),
                "start_age": self.public_pension_start_age,
                "amount_in_today_reais": self.public_pension_in_today_reais,
            },
            "private_pension": {
                "enabled": self.private_pension_enabled,
                "monthly_amount": float(self.private_pension_amount),
                "start_age": self.private_pension_start_age,
                "modality": self.private_pension_modality,
                "term_years": self.private_pension_term_years,
                "amount_in_today_reais": self.private_pension_in_today_reais,
            },
        }

    def is_valid(self) -> tuple[bool, list[str]]:
        """Retorna (valido, lista_de_erros)."""
        errors: list[str] = []

        if self.monthly_contribution <= 0:
            errors.append("Aporte mensal deve ser maior que zero")
        if self.retirement_age <= self.current_age:
            errors.append("Idade de aposentadoria deve ser maior que a idade atual")
        if self.life_expectancy <= self.retirement_age:
            errors.append("Expectativa de vida deve ser maior que a idade de aposentadoria")
        if self.public_pension_enabled:
            if self.public_pension_start_age < self.retirement_age:
                errors.append("Início do INSS não pode ser antes de parar de trabalhar")
            if self.public_pension_amount <= 0:
                errors.append("Valor do benefício público deve ser maior que zero")
        if self.private_pension_enabled:
            if self.private_pension_start_age < self.retirement_age:
                errors.append("Início da previdência não pode ser antes de parar de trabalhar")
            if self.private_pension_amount <= 0:
                errors.append("Valor do benefício privado deve ser maior que zero")

        return len(errors) == 0, errors
