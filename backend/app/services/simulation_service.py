from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import Simulation
from app.models.user import User
from app.schemas.simulation import SimulationCreate, SimulationParameters, SimulationResults
from app.services.calculator import run_full_simulation


def calculate_simulation(parameters: SimulationParameters) -> SimulationResults:
    return run_full_simulation(parameters)


async def create_simulation(
    db: AsyncSession,
    payload: SimulationCreate,
    user: User | None = None,
) -> Simulation:
    results = calculate_simulation(payload.parameters)
    simulation = Simulation(
        user_id=user.id if user else None,
        name=payload.name.strip() or "Simulação sem título",
        parameters=payload.parameters.model_dump(mode="json"),
        results=results.model_dump(mode="json"),
    )
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)
    return simulation


def generate_share_token() -> str:
    return token_urlsafe(32)
