from httpx import AsyncClient


async def test_simulations_calculate_route_exists(async_client: AsyncClient) -> None:
    response = await async_client.post("/api/v1/simulations/calculate", json={})

    assert response.status_code == 422
