from nicegui import ui


def create() -> None:
    """Registra a página de detalhe e edição de uma simulação."""

    @ui.page("/simulacao/{id}")
    def simulation_detail_page(id: str) -> None:
        """Renderiza o detalhe de uma simulação."""
