from nicegui import ui


def create() -> None:
    """Registra a página pública de simulação compartilhada."""

    @ui.page("/compartilhado/{token}")
    def shared_page(token: str) -> None:
        """Renderiza uma simulação compartilhada em modo somente leitura."""
