import os
from typing import Any

import httpx
from nicegui import ui

from app.formatting import format_brl, percent_to_rate_string, to_decimal_string

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1").rstrip("/")


def _default_payload() -> dict[str, Any]:
    return {
        "current_age": 35,
        "current_patrimony": "150000",
        "monthly_contribution": "3000",
        "desired_monthly_income": "10000",
        "retirement_age": 55,
        "life_expectancy": 90,
        "inflation_rate": "0.045",
        "annual_real_return": "0.06",
        "safe_withdrawal_rate": "0.04",
        "public_pension": {
            "enabled": True,
            "monthly_amount": "2500",
            "start_age": 65,
            "amount_in_today_reais": True,
        },
        "private_pension": {
            "enabled": True,
            "monthly_amount": "3000",
            "start_age": 60,
            "modality": "lifetime",
            "term_years": None,
            "amount_in_today_reais": True,
        },
    }


async def _calculate(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{BACKEND_API_URL}/simulations/calculate", json=payload)
        response.raise_for_status()
        return response.json()


def _metric_card(title: str, value: str, caption: str = "") -> None:
    with ui.card().classes("p-4 gap-1 bg-white shadow-sm border border-slate-200"):
        ui.label(title).classes("text-sm text-slate-500")
        ui.label(value).classes("text-2xl font-bold text-slate-900")
        if caption:
            ui.label(caption).classes("text-xs text-slate-500")


def _render_results(results: dict[str, Any]) -> None:
    status_labels = {
        "viable": "Viável",
        "warning": "Atenção",
        "unviable": "Inviável",
    }
    with ui.column().classes("w-full gap-6"):
        ui.label("Resultado da simulação").classes("text-2xl font-bold text-slate-900")
        with ui.grid(columns=4).classes("w-full gap-4 max-lg:grid-cols-2 max-sm:grid-cols-1"):
            _metric_card("Patrimônio necessário", format_brl(results["required_patrimony"]), "Meta para sustentar a renda desejada")
            _metric_card("Patrimônio projetado", format_brl(results["projected_patrimony"]), "Valor estimado ao parar de trabalhar")
            _metric_card("Aporte mensal necessário", format_brl(results["required_monthly_contribution"]), "Nunca é retornado negativo")
            _metric_card("Status", status_labels.get(results["feasibility_status"], results["feasibility_status"]), "Compara patrimônio projetado e necessário")

        if results.get("patrimony_exhausted"):
            with ui.banner().props("inline-actions").classes("bg-red-50 text-red-900 border border-red-200"):
                ui.label(
                    f"O patrimônio se esgota aos {results.get('exhaustion_age')} anos. Ajuste aportes, renda desejada ou datas previdenciárias."
                )
        else:
            with ui.banner().props("inline-actions").classes("bg-emerald-50 text-emerald-900 border border-emerald-200"):
                ui.label("O patrimônio não fica negativo na projeção até a expectativa de vida informada.")

        ui.label("Fases da renda e gap previdenciário").classes("text-xl font-semibold text-slate-900")
        ui.label(
            "As fases mudam quando INSS/RPPS ou previdência privada começam. Antes do primeiro benefício, a renda vem exclusivamente do patrimônio."
        ).classes("text-sm text-slate-600")
        rows = [
            {
                "periodo": f"{phase['from_age']}–{phase['to_age']} anos",
                "retirada": format_brl(phase["monthly_withdrawal_from_patrimony"]),
                "renda": format_brl(phase["monthly_income_total"]),
                "fontes": ", ".join(phase["sources"]),
            }
            for phase in results["phases"]
        ]
        ui.table(
            columns=[
                {"name": "periodo", "label": "Período", "field": "periodo", "align": "left"},
                {"name": "retirada", "label": "Retirada do patrimônio", "field": "retirada", "align": "right"},
                {"name": "renda", "label": "Renda mensal", "field": "renda", "align": "right"},
                {"name": "fontes", "label": "Fontes", "field": "fontes", "align": "left"},
            ],
            rows=rows,
        ).classes("w-full")

        series = results["projection_series"]
        ui.echart(
            {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": [point["age"] for point in series], "name": "Idade"},
                "yAxis": {"type": "value", "name": "Patrimônio"},
                "series": [
                    {
                        "name": "Patrimônio",
                        "type": "line",
                        "areaStyle": {},
                        "smooth": True,
                        "data": [float(point["patrimony"]) for point in series],
                    }
                ],
            }
        ).classes("w-full h-96").props('aria-label="Gráfico de evolução do patrimônio por idade"')


@ui.page("/")
def index() -> None:
    defaults = _default_payload()

    ui.add_head_html("""
    <style>
      body { background: #f8fafc; }
      .nicegui-content { max-width: 1180px; margin: 0 auto; padding: 32px 20px; }
    </style>
    """)

    with ui.column().classes("w-full gap-8"):
        with ui.column().classes("gap-2"):
            ui.label("SimulaRenda").classes("text-4xl font-bold text-slate-950")
            ui.label(
                "Planeje sua independência financeira considerando o gap previdenciário entre parar de trabalhar e começar a receber benefícios."
            ).classes("text-lg text-slate-600 max-w-3xl")

        with ui.card().classes("w-full p-6 gap-5 bg-white shadow-sm border border-slate-200"):
            ui.label("Parâmetros da simulação").classes("text-2xl font-semibold text-slate-900")
            ui.label("Valores monetários são informados em reais de hoje; taxas são percentuais ao ano.").classes("text-sm text-slate-600")

            with ui.grid(columns=3).classes("w-full gap-4 max-md:grid-cols-1"):
                current_age = ui.number("Idade atual", value=defaults["current_age"], min=18, max=100, step=1).props("aria-required=true")
                retirement_age = ui.number("Idade para parar de trabalhar", value=defaults["retirement_age"], min=19, max=100, step=1).props("aria-required=true")
                life_expectancy = ui.number("Expectativa de vida", value=defaults["life_expectancy"], min=retirement_age.value + 1, max=120, step=1).props("aria-required=true")
                current_patrimony = ui.number("Patrimônio atual (R$)", value=150000, min=0, step=1000).props("aria-required=true")
                monthly_contribution = ui.number("Aporte mensal (R$)", value=3000, min=0, step=100).props("aria-required=true")
                desired_monthly_income = ui.number("Renda mensal desejada (R$)", value=10000, min=1, step=100).props("aria-required=true")
                inflation_rate = ui.number("Inflação anual (%)", value=4.5, min=0, step=0.1).props("aria-required=true")
                annual_real_return = ui.number("Retorno real anual (%)", value=6, step=0.1).props("aria-required=true")
                safe_withdrawal_rate = ui.number("Taxa de retirada segura (%)", value=4, min=0.1, step=0.1).props("aria-required=true")

            with ui.grid(columns=2).classes("w-full gap-4 max-md:grid-cols-1"):
                with ui.card().classes("p-4 bg-slate-50"):
                    public_enabled = ui.checkbox("Considerar INSS/RPPS", value=True)
                    public_amount = ui.number("Valor mensal público (R$)", value=2500, min=0, step=100)
                    public_start_age = ui.number("Início do benefício público", value=65, min=retirement_age.value, max=120, step=1)
                with ui.card().classes("p-4 bg-slate-50"):
                    private_enabled = ui.checkbox("Considerar previdência privada", value=True)
                    private_amount = ui.number("Valor mensal privado (R$)", value=3000, min=0, step=100)
                    private_start_age = ui.number("Início da previdência privada", value=60, min=retirement_age.value, max=120, step=1)
                    private_modality = ui.select(
                        {"lifetime": "Renda vitalícia", "fixed_term": "Prazo certo"},
                        value="lifetime",
                        label="Modalidade",
                    )
                    private_term_years = ui.number("Prazo em anos (se prazo certo)", value=None, min=1, max=60, step=1)

            result_area = ui.column().classes("w-full")
            error_area = ui.column().classes("w-full")

            async def submit() -> None:
                error_area.clear()
                result_area.clear()
                payload = {
                    "current_age": int(current_age.value or 0),
                    "current_patrimony": to_decimal_string(current_patrimony.value),
                    "monthly_contribution": to_decimal_string(monthly_contribution.value),
                    "desired_monthly_income": to_decimal_string(desired_monthly_income.value),
                    "retirement_age": int(retirement_age.value or 0),
                    "life_expectancy": int(life_expectancy.value or 0),
                    "inflation_rate": percent_to_rate_string(inflation_rate.value),
                    "annual_real_return": percent_to_rate_string(annual_real_return.value),
                    "safe_withdrawal_rate": percent_to_rate_string(safe_withdrawal_rate.value, default="4"),
                    "public_pension": {
                        "enabled": bool(public_enabled.value),
                        "monthly_amount": to_decimal_string(public_amount.value),
                        "start_age": int(public_start_age.value or retirement_age.value or 0),
                        "amount_in_today_reais": True,
                    },
                    "private_pension": {
                        "enabled": bool(private_enabled.value),
                        "monthly_amount": to_decimal_string(private_amount.value),
                        "start_age": int(private_start_age.value or retirement_age.value or 0),
                        "modality": private_modality.value,
                        "term_years": int(private_term_years.value) if private_term_years.value else None,
                        "amount_in_today_reais": True,
                    },
                }
                try:
                    results = await _calculate(payload)
                except httpx.HTTPStatusError as exc:
                    detail = exc.response.json().get("detail", exc.response.text)
                    with error_area:
                        with ui.banner().classes("bg-red-50 text-red-900 border border-red-200"):
                            ui.label(f"Erro de validação ou API: {detail}")
                    return
                except httpx.HTTPError as exc:
                    with error_area:
                        with ui.banner().classes("bg-red-50 text-red-900 border border-red-200"):
                            ui.label(f"Não foi possível chamar a API: {exc}")
                    return
                with result_area:
                    _render_results(results)

            ui.button("Calcular independência financeira", on_click=submit).props("color=primary").classes("self-start")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host="0.0.0.0", port=int(os.getenv("PORT", "5173")), title="SimulaRenda")
