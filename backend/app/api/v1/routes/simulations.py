from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.simulation import SimulationCreate, SimulationParameters, SimulationResponse, SimulationResults
from app.services.simulation_service import calculate_simulation, create_simulation

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/calculate", response_model=SimulationResults)
async def calculate(payload: SimulationParameters) -> SimulationResults:
    return calculate_simulation(payload)


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: SimulationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationResponse:
    simulation = await create_simulation(db, payload, current_user)
    return SimulationResponse.model_validate(simulation)
