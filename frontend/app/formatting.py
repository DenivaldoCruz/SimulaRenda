from decimal import Decimal, InvalidOperation
from typing import Any


def to_decimal_string(value: Any, default: str = "0") -> str:
    """Convert a NiceGUI numeric value to a decimal string for API payloads."""
    if value is None or value == "":
        return default
    try:
        return str(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return default


def percent_to_rate_string(value: Any, default: str = "0") -> str:
    """Convert a percentage shown to users into the decimal rate expected by the API."""
    percentage = Decimal(to_decimal_string(value, default="0"))
    return str(percentage / Decimal("100"))


def format_brl(value: Any) -> str:
    """Format a numeric API value as Brazilian reais."""
    amount = Decimal(str(value or "0")).quantize(Decimal("0.01"))
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    inteiro, centavos = f"{amount:.2f}".split(".")
    grupos: list[str] = []
    while inteiro:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    return f"{sign}R$ {'.'.join(grupos)},{centavos}"
