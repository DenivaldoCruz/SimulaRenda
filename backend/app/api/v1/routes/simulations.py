from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.simulation import (
    SimulationCreate,
    SimulationListResponse,
    SimulationParameters,
    SimulationResponse,
    SimulationResults,
    SimulationShareRequest,
    SimulationUpdate,
)
from app.services.simulation_service import (
    calculate_simulation,
    create_simulation,
    delete_simulation,
    get_public_simulation_by_token,
    get_user_simulation,
    list_user_simulations,
    set_simulation_sharing,
    update_simulation,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/calculate", response_model=SimulationResults)
@limiter.limit("30/minute")
async def calculate(request: Request, payload: SimulationParameters) -> SimulationResults:
    del request
    return calculate_simulation(payload)


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: SimulationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationResponse:
    simulation = await create_simulation(db, payload, current_user)
    return SimulationResponse.model_validate(simulation)


@router.get("", response_model=SimulationListResponse)
async def list_simulations(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationListResponse:
    simulations, total = await list_user_simulations(db, current_user, page, size)
    return SimulationListResponse(
        items=[SimulationResponse.model_validate(simulation) for simulation in simulations],
        page=page,
        size=size,
        total=total,
    )


@router.get("/shared/{token}", response_model=SimulationResponse)
async def get_shared_simulation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> SimulationResponse:
    simulation = await get_public_simulation_by_token(db, token)
    return SimulationResponse.model_validate(simulation)


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationResponse:
    simulation = await get_user_simulation(db, simulation_id, current_user)
    return SimulationResponse.model_validate(simulation)


@router.put("/{simulation_id}", response_model=SimulationResponse)
async def update(
    simulation_id: UUID,
    payload: SimulationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationResponse:
    simulation = await update_simulation(db, simulation_id, payload, current_user)
    return SimulationResponse.model_validate(simulation)


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    simulation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await delete_simulation(db, simulation_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{simulation_id}/share", response_model=SimulationResponse)
async def share(
    simulation_id: UUID,
    payload: SimulationShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SimulationResponse:
    simulation = await set_simulation_sharing(db, simulation_id, current_user, payload.enable)
    return SimulationResponse.model_validate(simulation)
