async def test_get_my_account_requires_auth(client):
    response = await client.get("/account")
    assert response.status_code == 401


async def test_get_my_account(authenticated_client):
    response = await authenticated_client.get("/account")

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Settings User"
    assert "id" in data
    assert "created_at" in data


async def test_get_my_account_returns_own_account_not_someone_elses(client):
    await client.post(
        "/auth/register",
        json={"email": "accountone@example.com", "password": "password123", "display_name": "First"},
    )
    login_one = await client.post(
        "/auth/jwt/login", data={"username": "accountone@example.com", "password": "password123"}
    )
    token_one = login_one.json()["access_token"]

    await client.post(
        "/auth/register",
        json={"email": "accounttwo@example.com", "password": "password123", "display_name": "Second"},
    )
    login_two = await client.post(
        "/auth/jwt/login", data={"username": "accounttwo@example.com", "password": "password123"}
    )
    token_two = login_two.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token_one}"
    response_one = await client.get("/account")
    assert response_one.json()["display_name"] == "First"

    client.headers["Authorization"] = f"Bearer {token_two}"
    response_two = await client.get("/account")
    assert response_two.json()["display_name"] == "Second"
