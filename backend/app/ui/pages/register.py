from nicegui import ui


def create() -> None:
    """Registra a página de cadastro do usuário."""

    @ui.page("/cadastrar")
    def register_page() -> None:
        """Renderiza o formulário de cadastro."""
