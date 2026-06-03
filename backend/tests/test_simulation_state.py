from decimal import Decimal

from app.ui.state.simulation_state import SimulationState


def test_to_parameters_dict_returns_all_expected_keys() -> None:
    state = SimulationState(
        current_age=35,
        current_patrimony=Decimal("150000.50"),
        monthly_contribution=Decimal("3000.25"),
        desired_monthly_income=Decimal("10000.75"),
        retirement_age=55,
        life_expectancy=90,
        inflation_rate=Decimal("0.045"),
        annual_real_return=Decimal("0.06"),
        safe_withdrawal_rate=Decimal("0.04"),
        public_pension_enabled=True,
        public_pension_amount=Decimal("2500"),
        public_pension_start_age=65,
        public_pension_in_today_reais=True,
        private_pension_enabled=True,
        private_pension_amount=Decimal("3000"),
        private_pension_start_age=60,
        private_pension_modality="fixed_term",
        private_pension_term_years=20,
        private_pension_in_today_reais=False,
    )

    parameters = state.to_parameters_dict()

    assert set(parameters) == {
        "current_age",
        "current_patrimony",
        "monthly_contribution",
        "desired_monthly_income",
        "retirement_age",
        "life_expectancy",
        "inflation_rate",
        "annual_real_return",
        "safe_withdrawal_rate",
        "public_pension",
        "private_pension",
    }
    assert set(parameters["public_pension"]) == {
        "enabled",
        "monthly_amount",
        "start_age",
        "amount_in_today_reais",
    }
    assert set(parameters["private_pension"]) == {
        "enabled",
        "monthly_amount",
        "start_age",
        "modality",
        "term_years",
        "amount_in_today_reais",
    }
    assert parameters == {
        "current_age": 35,
        "current_patrimony": 150000.5,
        "monthly_contribution": 3000.25,
        "desired_monthly_income": 10000.75,
        "retirement_age": 55,
        "life_expectancy": 90,
        "inflation_rate": 0.045,
        "annual_real_return": 0.06,
        "safe_withdrawal_rate": 0.04,
        "public_pension": {
            "enabled": True,
            "monthly_amount": 2500.0,
            "start_age": 65,
            "amount_in_today_reais": True,
        },
        "private_pension": {
            "enabled": True,
            "monthly_amount": 3000.0,
            "start_age": 60,
            "modality": "fixed_term",
            "term_years": 20,
            "amount_in_today_reais": False,
        },
    }


def test_is_valid_returns_false_when_retirement_age_is_not_greater_than_current_age() -> None:
    state = SimulationState(current_age=55, retirement_age=55)

    is_valid, errors = state.is_valid()

    assert is_valid is False
    assert "Idade de aposentadoria deve ser maior que a idade atual" in errors


def test_is_valid_returns_false_when_public_pension_starts_before_retirement() -> None:
    state = SimulationState(
        public_pension_enabled=True,
        public_pension_amount=Decimal("2500"),
        public_pension_start_age=54,
        retirement_age=55,
    )

    is_valid, errors = state.is_valid()

    assert is_valid is False
    assert "Início do INSS não pode ser antes de parar de trabalhar" in errors


def test_is_valid_returns_true_with_valid_default_values() -> None:
    state = SimulationState()

    is_valid, errors = state.is_valid()

    assert is_valid is True
    assert errors == []


def test_is_valid_returns_descriptive_error_list_for_each_violation() -> None:
    state = SimulationState(
        current_age=60,
        monthly_contribution=Decimal("0"),
        retirement_age=55,
        life_expectancy=55,
        public_pension_enabled=True,
        public_pension_amount=Decimal("0"),
        public_pension_start_age=54,
        private_pension_enabled=True,
        private_pension_amount=Decimal("0"),
        private_pension_start_age=54,
    )

    is_valid, errors = state.is_valid()

    assert is_valid is False
    assert errors == [
        "Aporte mensal deve ser maior que zero",
        "Idade de aposentadoria deve ser maior que a idade atual",
        "Expectativa de vida deve ser maior que a idade de aposentadoria",
        "Início do INSS não pode ser antes de parar de trabalhar",
        "Valor do benefício público deve ser maior que zero",
        "Início da previdência não pode ser antes de parar de trabalhar",
        "Valor do benefício privado deve ser maior que zero",
    ]
