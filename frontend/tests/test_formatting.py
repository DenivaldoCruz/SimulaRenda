from app.formatting import format_brl, percent_to_rate_string, to_decimal_string


def test_format_brl_uses_brazilian_separators() -> None:
    assert format_brl("1234567.89") == "R$ 1.234.567,89"


def test_percent_to_rate_string_converts_display_percentage() -> None:
    assert percent_to_rate_string("4.5") == "0.045"


def test_to_decimal_string_falls_back_for_empty_values() -> None:
    assert to_decimal_string(None, default="10") == "10"
