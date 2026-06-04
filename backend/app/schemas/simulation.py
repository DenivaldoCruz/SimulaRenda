from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PublicPension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    monthly_amount: Decimal = Decimal("0.00")
    start_age: int | None = None
    amount_in_today_reais: bool = True


class PrivatePension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    monthly_amount: Decimal = Decimal("0.00")
    start_age: int | None = None
    modality: Literal["lifetime", "fixed_term", "lump_sum"] = "lifetime"
    term_years: int | None = None
    amount_in_today_reais: bool = True


class SimulationParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_age: int = Field(gt=0)
    current_patrimony: Decimal = Field(ge=0)
    monthly_contribution: Decimal = Field(ge=0)
    desired_monthly_income: Decimal = Field(gt=0)
    retirement_age: int = Field(gt=0)
    life_expectancy: int = Field(gt=0)
    inflation_rate: Decimal = Field(ge=0)
    annual_real_return: Decimal
    safe_withdrawal_rate: Decimal = Field(gt=0, le=Decimal("0.10"))
    public_pension: PublicPension = Field(default_factory=PublicPension)
    private_pension: PrivatePension = Field(default_factory=PrivatePension)

    @model_validator(mode="after")
    def validate_age_invariants(self) -> "SimulationParameters":
        if self.retirement_age <= self.current_age:
            raise ValueError("retirement_age must be greater than current_age")
        if self.life_expectancy <= self.retirement_age:
            raise ValueError("life_expectancy must be greater than retirement_age")
        if self.public_pension.enabled and (
            self.public_pension.start_age is None
            or self.public_pension.start_age < self.retirement_age
        ):
            raise ValueError("public_pension.start_age must be greater than or equal to retirement_age")
        if self.private_pension.enabled and (
            self.private_pension.start_age is None
            or self.private_pension.start_age < self.retirement_age
        ):
            raise ValueError("private_pension.start_age must be greater than or equal to retirement_age")
        return self


class SimulationPhase(BaseModel):
    from_age: int
    to_age: int
    monthly_withdrawal_from_patrimony: Decimal
    monthly_income_total: Decimal
    sources: list[str]


class ProjectionPoint(BaseModel):
    age: int
    patrimony: Decimal
    monthly_income: Decimal


class SimulationResults(BaseModel):
    required_patrimony: Decimal
    projected_patrimony: Decimal
    required_monthly_contribution: Decimal
    feasibility_status: Literal["viable", "warning", "unviable"]
    patrimony_gap: Decimal
    phases: list[SimulationPhase]
    projection_series: list[ProjectionPoint]
    patrimony_exhausted: bool
    exhaustion_age: int | None = None


class SimulationCreate(BaseModel):
    name: str = "Simulação sem título"
    parameters: SimulationParameters


class SimulationResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    name: str
    parameters: dict
    results: dict
    share_token: str | None = None
    is_public: bool

    model_config = ConfigDict(from_attributes=True)
