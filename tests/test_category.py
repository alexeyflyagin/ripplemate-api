from tests.conftest import verify_user

async def test_create_category_requires_auth(client, workspace_id):
    del client.headers["Authorization"]
    response = await client.post(f"/workspaces/{workspace_id}/categories", json={"name": "Test"})
    assert response.status_code == 401


async def test_create_category(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "My Category"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Category"
    assert "id" in data
    assert "created_at" in data


async def test_create_category_rejects_blank_name(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "   "}
    )
    assert response.status_code == 422


async def test_create_category_rejects_name_too_long(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "x" * 25}
    )
    assert response.status_code == 422


async def test_create_category_rejects_duplicate_name_in_same_workspace(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/categories", json={"name": "Duplicate"})
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "Duplicate"}
    )
    assert response.status_code == 409


async def test_create_category_allows_same_name_in_different_workspaces(authenticated_client, workspace_id):
    other_workspace = await authenticated_client.post("/workspaces", json={"name": "Other Workspace"})
    other_workspace_id = other_workspace.json()["id"]

    response_one = await authenticated_client.post(
        f"/workspaces/{workspace_id}/categories", json={"name": "Shared Name"}
    )
    response_two = await authenticated_client.post(
        f"/workspaces/{other_workspace_id}/categories", json={"name": "Shared Name"}
    )

    assert response_one.status_code == 201
    assert response_two.status_code == 201


async def test_create_category_workspace_not_found(authenticated_client):
    response = await authenticated_client.post("/workspaces/999999/categories", json={"name": "Test"})
    assert response.status_code == 404


async def test_cannot_create_category_in_other_users_workspace(client, db_session, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "catintruder@example.com", "password": "password123", "display_name": "Intruder"},
    )
    await verify_user(db_session, "catintruder@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "catintruder@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.post(f"/workspaces/{workspace_id}/categories", json={"name": "Hijacked"})
    assert response.status_code == 404


async def test_list_categories_empty(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/categories")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_categories_returns_owned(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/categories", json={"name": "First"})
    await authenticated_client.post(f"/workspaces/{workspace_id}/categories", json={"name": "Second"})

    response = await authenticated_client.get(f"/workspaces/{workspace_id}/categories")

    assert response.status_code == 200
    names = {category["name"] for category in response.json()}
    assert names == {"First", "Second"}


async def test_get_category(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/categories/{category_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "My Category"


async def test_get_category_not_found(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/categories/999999")
    assert response.status_code == 404


async def test_get_category_wrong_workspace_returns_404(authenticated_client, workspace_id, category_id):
    other_workspace = await authenticated_client.post("/workspaces", json={"name": "Other Workspace"})
    other_workspace_id = other_workspace.json()["id"]

    response = await authenticated_client.get(
        f"/workspaces/{other_workspace_id}/categories/{category_id}"
    )
    assert response.status_code == 404


async def test_rename_category(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/categories/{category_id}", json={"name": "Renamed"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


async def test_rename_category_with_empty_body_changes_nothing(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/categories/{category_id}", json={}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "My Category"


async def test_rename_category_rejects_explicit_null(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/categories/{category_id}", json={"name": None}
    )
    assert response.status_code == 422


async def test_rename_category_rejects_duplicate_name(authenticated_client, workspace_id, category_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/categories", json={"name": "Existing"})

    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/categories/{category_id}", json={"name": "Existing"}
    )
    assert response.status_code == 409


async def test_cannot_rename_category_in_other_users_workspace(client, db_session, workspace_id, category_id):
    await client.post(
        "/auth/register",
        json={"email": "catintruder2@example.com", "password": "password123", "display_name": "Intruder"},
    )
    await verify_user(db_session, "catintruder2@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "catintruder2@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.patch(
        f"/workspaces/{workspace_id}/categories/{category_id}", json={"name": "Hijacked"}
    )
    assert response.status_code == 404


async def test_delete_category(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}/categories/{category_id}")
    assert response.status_code == 204

    follow_up = await authenticated_client.get(f"/workspaces/{workspace_id}/categories/{category_id}")
    assert follow_up.status_code == 404


async def test_delete_category_not_found(authenticated_client, workspace_id):
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}/categories/999999")
    assert response.status_code == 404


async def test_cannot_delete_category_in_other_users_workspace(client, db_session, workspace_id, category_id):
    await client.post(
        "/auth/register",
        json={"email": "catintruder3@example.com", "password": "password123", "display_name": "Intruder"},
    )
    await verify_user(db_session, "catintruder3@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "catintruder3@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.delete(f"/workspaces/{workspace_id}/categories/{category_id}")
    assert response.status_code == 404
