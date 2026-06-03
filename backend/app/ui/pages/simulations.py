from nicegui import ui


def create() -> None:
    """Registra a página de histórico e comparação de simulações."""

    @ui.page("/minhas-simulacoes")
    def simulations_page() -> None:
        """Renderiza a lista de simulações salvas."""
