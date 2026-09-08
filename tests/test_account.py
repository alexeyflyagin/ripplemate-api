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


async def test_check_account_exists_returns_true_for_registered_email(client):
    await client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "password123",
            "display_name": "Existing User",
        },
    )

    response = await client.get("/account/exists", params={"email": "existing@example.com"})

    assert response.status_code == 200
    assert response.json() == {"exists": True}


async def test_check_account_exists_returns_false_for_unknown_email(client):
    response = await client.get("/account/exists", params={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert response.json() == {"exists": False}


async def test_check_account_exists_is_case_insensitive(client):
    await client.post(
        "/auth/register",
        json={
            "email": "MixedCase@Example.com",
            "password": "password123",
            "display_name": "Mixed Case",
        },
    )

    response = await client.get("/account/exists", params={"email": "mixedcase@example.com"})

    assert response.status_code == 200
    assert response.json() == {"exists": True}


async def test_check_account_exists_does_not_require_auth(client):
    response = await client.get("/account/exists", params={"email": "nobody@example.com"})

    assert response.status_code != 401


async def test_check_account_exists_rejects_invalid_email(client):
    response = await client.get("/account/exists", params={"email": "not-an-email"})

    assert response.status_code == 422


async def test_check_account_exists_does_not_require_password(client):
    response = await client.get("/account/exists", params={"email": "nobody@example.com"})

    assert response.status_code == 200
    assert "password" not in response.json()
