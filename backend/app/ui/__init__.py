from app.ui.pages import home, login, register, shared, simulation_detail, simulations


def register_pages() -> None:
    """Registra todas as rotas NiceGUI na aplicação."""
    home.create()
    simulations.create()
    simulation_detail.create()
    shared.create()
    login.create()
    register.create()
