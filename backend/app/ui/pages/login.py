from nicegui import ui


def create() -> None:
    """Registra a página de entrada do usuário."""

    @ui.page("/entrar")
    def login_page() -> None:
        """Renderiza o formulário de login."""
