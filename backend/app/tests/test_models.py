from datetime import UTC, date, datetime

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import Simulation, User


VALID_PARAMETERS = {
    "current_age": 35,
    "current_patrimony": "150000.00",
    "monthly_contribution": "3000.00",
    "desired_monthly_income": "10000.00",
    "retirement_age": 55,
    "life_expectancy": 90,
    "inflation_rate": "0.045",
    "annual_real_return": "0.06",
    "safe_withdrawal_rate": "0.04",
    "public_pension": {
        "enabled": True,
        "monthly_amount": "2500.00",
        "start_age": 65,
        "amount_in_today_reais": True,
    },
    "private_pension": {
        "enabled": True,
        "monthly_amount": "3000.00",
        "start_age": 60,
        "modality": "lifetime",
        "term_years": None,
        "amount_in_today_reais": True,
    },
}

VALID_RESULTS = {
    "required_patrimony": "1500000.00",
    "projected_patrimony": "1250000.00",
    "required_monthly_contribution": "3800.00",
    "feasibility_status": "warning",
    "patrimony_gap": "250000.00",
    "phases": [],
    "projection_series": [],
    "patrimony_exhausted": False,
    "exhaustion_age": None,
}


@pytest.fixture
async def foreign_key_db() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield TestingSessionLocal
    finally:
        await engine.dispose()


async def test_create_user(test_db: async_sessionmaker[AsyncSession]) -> None:
    async with test_db() as session:
        user = User(
            email="ana@example.com",
            name="Ana",
            hashed_password="hashed-password",
            birth_date=date(1990, 1, 10),
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.email == "ana@example.com"
        assert user.name == "Ana"
        assert user.hashed_password == "hashed-password"
        assert user.birth_date == date(1990, 1, 10)
        assert user.created_at is not None
        assert user.deleted_at is None


async def test_create_simulation_linked_to_user(test_db: async_sessionmaker[AsyncSession]) -> None:
    async with test_db() as session:
        user = User(email="bruno@example.com")
        simulation = Simulation(
            user=user,
            name="Plano com gap previdenciário",
            parameters=VALID_PARAMETERS,
            results=VALID_RESULTS,
            share_token="unique-token",
            is_public=True,
        )

        session.add(simulation)
        await session.commit()
        await session.refresh(simulation)

        assert simulation.id is not None
        assert simulation.user_id == user.id
        assert simulation.user == user
        assert simulation in user.simulations
        assert simulation.parameters["public_pension"]["start_age"] == 65
        assert simulation.is_public is True


async def test_soft_deleted_user_keeps_simulations_linked(
    test_db: async_sessionmaker[AsyncSession],
) -> None:
    async with test_db() as session:
        user = User(email="carla@example.com")
        simulation = Simulation(user=user, parameters=VALID_PARAMETERS, results=VALID_RESULTS)
        session.add(simulation)
        await session.commit()

        user.deleted_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(simulation)

        assert simulation.user_id == user.id
        assert simulation.user == user


async def test_deleted_user_sets_simulation_user_id_to_null(
    foreign_key_db: async_sessionmaker[AsyncSession],
) -> None:
    async with foreign_key_db() as session:
        user = User(email="daniela@example.com")
        simulation = Simulation(user=user, parameters=VALID_PARAMETERS, results=VALID_RESULTS)
        session.add(simulation)
        await session.commit()
        user_id = user.id
        simulation_id = simulation.id
        session.expunge_all()

        persisted_user = await session.get(User, user_id)
        assert persisted_user is not None

        await session.delete(persisted_user)
        await session.commit()
        session.expunge_all()

        result = await session.execute(select(Simulation).where(Simulation.id == simulation_id))
        persisted_simulation = result.scalar_one()

        assert persisted_simulation.user_id is None


async def test_share_token_must_be_unique(test_db: async_sessionmaker[AsyncSession]) -> None:
    async with test_db() as session:
        first = Simulation(parameters=VALID_PARAMETERS, results=VALID_RESULTS, share_token="duplicated-token")
        second = Simulation(parameters=VALID_PARAMETERS, results=VALID_RESULTS, share_token="duplicated-token")
        session.add_all([first, second])

        with pytest.raises(IntegrityError):
            await session.commit()
