async def test_get_settings_requires_auth(client):
    response = await client.get("/settings")
    assert response.status_code == 401


async def test_get_settings_returns_object(authenticated_client):
    response = await authenticated_client.get("/settings")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "updated_at" in data


async def test_patch_settings_with_empty_body_returns_ok(authenticated_client):
    response = await authenticated_client.patch("/settings", json={})

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "updated_at" in data


async def test_patch_settings_requires_auth(client):
    response = await client.patch("/settings", json={})
    assert response.status_code == 401