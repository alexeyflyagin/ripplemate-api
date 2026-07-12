async def test_get_settings_requires_auth(client):
    response = await client.get("/settings")
    assert response.status_code == 401


async def test_get_settings_returns_defaults(authenticated_client):
    response = await authenticated_client.get("/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["font"] == "sans-serif"
    assert data["language"] == "auto"
    assert data["theme"] == "auto"


async def test_patch_settings_updates_only_provided_field(authenticated_client):
    response = await authenticated_client.patch("/settings", json={"theme": "dark"})

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["font"] == "sans-serif"
    assert data["language"] == "auto"


async def test_patch_settings_updates_multiple_fields(authenticated_client):
    response = await authenticated_client.patch(
        "/settings", json={"theme": "light", "font": "serif"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["font"] == "serif"
    assert data["language"] == "auto"


async def test_patch_settings_rejects_invalid_theme(authenticated_client):
    response = await authenticated_client.patch("/settings", json={"theme": "purple"})
    assert response.status_code == 422


async def test_patch_settings_rejects_invalid_font(authenticated_client):
    response = await authenticated_client.patch("/settings", json={"font": "comic-sans"})
    assert response.status_code == 422


async def test_patch_settings_rejects_invalid_language(authenticated_client):
    response = await authenticated_client.patch("/settings", json={"language": "fr"})
    assert response.status_code == 422


async def test_patch_settings_rejects_explicit_null(authenticated_client):
    response = await authenticated_client.patch("/settings", json={"theme": None})
    assert response.status_code == 422


async def test_patch_settings_requires_auth(client):
    response = await client.patch("/settings", json={"theme": "dark"})
    assert response.status_code == 401


async def test_patch_settings_persists_changes(authenticated_client):
    await authenticated_client.patch("/settings", json={"theme": "dark"})

    response = await authenticated_client.get("/settings")

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


async def test_patch_settings_does_not_affect_other_users(client):
    await client.post(
        "/auth/register",
        json={
            "email": "userone@example.com",
            "password": "password123",
            "display_name": "User One",
        },
    )
    login_one = await client.post(
        "/auth/jwt/login",
        data={"username": "userone@example.com", "password": "password123"},
    )
    token_one = login_one.json()["access_token"]

    await client.post(
        "/auth/register",
        json={
            "email": "usertwo@example.com",
            "password": "password123",
            "display_name": "User Two",
        },
    )
    login_two = await client.post(
        "/auth/jwt/login",
        data={"username": "usertwo@example.com", "password": "password123"},
    )
    token_two = login_two.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token_one}"
    await client.patch("/settings", json={"theme": "dark"})

    client.headers["Authorization"] = f"Bearer {token_two}"
    response = await client.get("/settings")

    assert response.status_code == 200
    assert response.json()["theme"] == "auto"


async def test_patch_settings_with_empty_body_changes_nothing(authenticated_client):
    response = await authenticated_client.patch("/settings", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["font"] == "sans-serif"
    assert data["language"] == "auto"
    assert data["theme"] == "auto"
