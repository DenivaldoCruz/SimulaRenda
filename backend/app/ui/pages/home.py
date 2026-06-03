from nicegui import ui


def create() -> None:
    """Registra a página principal de formulário e resultados."""

    @ui.page("/")
    def home_page() -> None:
        """Renderiza a página principal do SimulaRenda."""
