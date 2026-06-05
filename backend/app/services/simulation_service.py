from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import Simulation
from app.models.user import User
from app.schemas.simulation import (
    SimulationCreate,
    SimulationParameters,
    SimulationResults,
    SimulationUpdate,
)
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
        name=payload.normalized_name,
        parameters=payload.parameters.model_dump(mode="json"),
        results=results.model_dump(mode="json"),
    )
    db.add(simulation)
    await db.commit()
    await db.refresh(simulation)
    return simulation


async def list_user_simulations(
    db: AsyncSession,
    user: User,
    page: int,
    size: int,
) -> tuple[list[Simulation], int]:
    offset = (page - 1) * size
    base_filter = Simulation.user_id == user.id
    total_result = await db.execute(select(func.count()).select_from(Simulation).where(base_filter))
    total = int(total_result.scalar_one())
    result = await db.execute(
        select(Simulation)
        .where(base_filter)
        .order_by(Simulation.created_at.desc(), Simulation.id.desc())
        .offset(offset)
        .limit(size)
    )
    return list(result.scalars().all()), total


async def get_user_simulation(db: AsyncSession, simulation_id: UUID, user: User) -> Simulation:
    simulation = await db.get(Simulation, simulation_id)
    if simulation is None or simulation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação não encontrada",
        )
    return simulation


async def update_simulation(
    db: AsyncSession,
    simulation_id: UUID,
    payload: SimulationUpdate,
    user: User,
) -> Simulation:
    simulation = await get_user_simulation(db, simulation_id, user)
    if "name" in payload.model_fields_set:
        simulation.name = payload.normalized_name

    if payload.parameters is not None:
        current_parameters = SimulationParameters.model_validate(simulation.parameters)
        if payload.parameters != current_parameters:
            results = calculate_simulation(payload.parameters)
            simulation.parameters = payload.parameters.model_dump(mode="json")
            simulation.results = results.model_dump(mode="json")

    await db.commit()
    await db.refresh(simulation)
    return simulation


async def delete_simulation(db: AsyncSession, simulation_id: UUID, user: User) -> None:
    simulation = await get_user_simulation(db, simulation_id, user)
    await db.delete(simulation)
    await db.commit()


async def set_simulation_sharing(
    db: AsyncSession,
    simulation_id: UUID,
    user: User,
    enable: bool,
) -> Simulation:
    simulation = await get_user_simulation(db, simulation_id, user)
    simulation.is_public = enable
    simulation.share_token = await _create_unique_share_token(db) if enable else None
    await db.commit()
    await db.refresh(simulation)
    return simulation


async def get_public_simulation_by_token(db: AsyncSession, token: str) -> Simulation:
    result = await db.execute(
        select(Simulation).where(Simulation.share_token == token, Simulation.is_public.is_(True))
    )
    simulation = result.scalar_one_or_none()
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulação pública não encontrada",
        )
    return simulation


async def _create_unique_share_token(db: AsyncSession) -> str:
    while True:
        token = generate_share_token()
        result = await db.execute(select(Simulation.id).where(Simulation.share_token == token))
        if result.scalar_one_or_none() is None:
            return token


def generate_share_token() -> str:
    return token_urlsafe(32)
