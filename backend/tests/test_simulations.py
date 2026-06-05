from copy import deepcopy

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def simulation_parameters() -> dict[str, object]:
    return {
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


async def register_and_authorize(async_client: AsyncClient, email: str) -> dict[str, str]:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strong-password", "name": "Tester"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


async def create_simulation(
    async_client: AsyncClient,
    headers: dict[str, str],
    parameters: dict[str, object],
    name: str = "Plano original",
) -> dict[str, object]:
    response = await async_client.post(
        "/api/v1/simulations",
        headers=headers,
        json={"name": name, "parameters": parameters},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def test_calculate_runs_without_persisting_or_authentication(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    calculate_response = await async_client.post(
        "/api/v1/simulations/calculate",
        json=simulation_parameters,
    )
    list_response = await async_client.get("/api/v1/simulations")

    assert calculate_response.status_code == status.HTTP_200_OK
    body = calculate_response.json()
    assert body["required_patrimony"]
    assert body["projection_series"]
    assert list_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_calculate_rejects_invalid_parameters(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    invalid = deepcopy(simulation_parameters)
    invalid["retirement_age"] = 30

    response = await async_client.post("/api/v1/simulations/calculate", json=invalid)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_requires_authentication(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    response = await async_client.post(
        "/api/v1/simulations",
        json={"name": "Sem login", "parameters": simulation_parameters},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_persists_recalculated_server_results_and_rejects_client_results(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "create@example.com")

    response = await async_client.post(
        "/api/v1/simulations",
        headers=headers,
        json={
            "name": "  Plano recalculado  ",
            "parameters": simulation_parameters,
            "results": {"required_patrimony": "1.00"},
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    created = await create_simulation(
        async_client, headers, simulation_parameters, name="  Plano recalculado  "
    )
    calculated = await async_client.post(
        "/api/v1/simulations/calculate", json=simulation_parameters
    )

    assert created["name"] == "Plano recalculado"
    assert created["results"] == calculated.json()
    assert created["is_public"] is False
    assert created["share_token"] is None


async def test_list_returns_only_authenticated_users_paginated_simulations(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    first_headers = await register_and_authorize(async_client, "list-a@example.com")
    second_headers = await register_and_authorize(async_client, "list-b@example.com")
    first = await create_simulation(
        async_client, first_headers, simulation_parameters, name="Primeira"
    )
    second = await create_simulation(
        async_client, first_headers, simulation_parameters, name="Segunda"
    )
    await create_simulation(
        async_client, second_headers, simulation_parameters, name="Outra pessoa"
    )

    response = await async_client.get(
        "/api/v1/simulations?page=1&size=1",
        headers=first_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["page"] == 1
    assert body["size"] == 1
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] in {first["id"], second["id"]}


async def test_get_detail_enforces_ownership(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    owner_headers = await register_and_authorize(async_client, "detail-owner@example.com")
    other_headers = await register_and_authorize(async_client, "detail-other@example.com")
    created = await create_simulation(async_client, owner_headers, simulation_parameters)

    owner_response = await async_client.get(
        f"/api/v1/simulations/{created['id']}", headers=owner_headers
    )
    other_response = await async_client.get(
        f"/api/v1/simulations/{created['id']}", headers=other_headers
    )
    anonymous_response = await async_client.get(f"/api/v1/simulations/{created['id']}")

    assert owner_response.status_code == status.HTTP_200_OK
    assert owner_response.json()["id"] == created["id"]
    assert other_response.status_code == status.HTTP_404_NOT_FOUND
    assert anonymous_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_update_recalculates_when_parameters_change_and_rejects_client_results(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "update@example.com")
    created = await create_simulation(async_client, headers, simulation_parameters)
    updated_parameters = deepcopy(simulation_parameters)
    updated_parameters["desired_monthly_income"] = "12000.00"

    rejected_response = await async_client.put(
        f"/api/v1/simulations/{created['id']}",
        headers=headers,
        json={"results": {"required_patrimony": "1.00"}},
    )
    update_response = await async_client.put(
        f"/api/v1/simulations/{created['id']}",
        headers=headers,
        json={"name": "Plano atualizado", "parameters": updated_parameters},
    )
    calculated = await async_client.post("/api/v1/simulations/calculate", json=updated_parameters)

    assert rejected_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert update_response.status_code == status.HTTP_200_OK
    body = update_response.json()
    assert body["name"] == "Plano atualizado"
    assert body["parameters"]["desired_monthly_income"] == "12000.00"
    assert body["results"] == calculated.json()
    assert body["results"] != created["results"]


async def test_update_name_only_keeps_existing_results_snapshot(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "update-name@example.com")
    created = await create_simulation(async_client, headers, simulation_parameters)

    response = await async_client.put(
        f"/api/v1/simulations/{created['id']}",
        headers=headers,
        json={"name": "Novo nome"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Novo nome"
    assert response.json()["results"] == created["results"]


async def test_share_enable_exposes_public_token_and_disable_revokes_it(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "share@example.com")
    created = await create_simulation(async_client, headers, simulation_parameters)

    enable_response = await async_client.post(
        f"/api/v1/simulations/{created['id']}/share",
        headers=headers,
        json={"enable": True},
    )
    token = enable_response.json()["share_token"]
    public_response = await async_client.get(f"/api/v1/simulations/shared/{token}")
    disable_response = await async_client.post(
        f"/api/v1/simulations/{created['id']}/share",
        headers=headers,
        json={"enable": False},
    )
    revoked_response = await async_client.get(f"/api/v1/simulations/shared/{token}")

    assert enable_response.status_code == status.HTTP_200_OK
    assert enable_response.json()["is_public"] is True
    assert token
    assert public_response.status_code == status.HTTP_200_OK
    assert public_response.json()["id"] == created["id"]
    assert disable_response.status_code == status.HTTP_200_OK
    assert disable_response.json()["is_public"] is False
    assert disable_response.json()["share_token"] is None
    assert revoked_response.status_code == status.HTTP_404_NOT_FOUND


async def test_share_requires_owner(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    owner_headers = await register_and_authorize(async_client, "share-owner@example.com")
    other_headers = await register_and_authorize(async_client, "share-other@example.com")
    created = await create_simulation(async_client, owner_headers, simulation_parameters)

    response = await async_client.post(
        f"/api/v1/simulations/{created['id']}/share",
        headers=other_headers,
        json={"enable": True},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_removes_owned_simulation_and_blocks_later_access(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "delete@example.com")
    created = await create_simulation(async_client, headers, simulation_parameters)

    delete_response = await async_client.delete(
        f"/api/v1/simulations/{created['id']}", headers=headers
    )
    get_response = await async_client.get(f"/api/v1/simulations/{created['id']}", headers=headers)

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


async def test_missing_and_malformed_resources_return_errors(
    async_client: AsyncClient,
    simulation_parameters: dict[str, object],
) -> None:
    headers = await register_and_authorize(async_client, "errors@example.com")

    bad_id_response = await async_client.get("/api/v1/simulations/not-a-uuid", headers=headers)
    missing_public_response = await async_client.get("/api/v1/simulations/shared/unknown-token")
    bad_page_response = await async_client.get("/api/v1/simulations?page=0", headers=headers)

    assert bad_id_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert missing_public_response.status_code == status.HTTP_404_NOT_FOUND
    assert bad_page_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
