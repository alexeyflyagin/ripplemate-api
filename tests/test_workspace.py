from tests.conftest import verify_user

async def test_create_workspace_requires_auth(client):
    response = await client.post("/workspaces", json={"name": "Test"})
    assert response.status_code == 401


async def test_create_workspace(authenticated_client):
    response = await authenticated_client.post("/workspaces", json={"name": "My Workspace"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Workspace"
    assert "id" in data
    assert "created_at" in data


async def test_create_workspace_rejects_blank_name(authenticated_client):
    response = await authenticated_client.post("/workspaces", json={"name": "   "})
    assert response.status_code == 422


async def test_create_workspace_rejects_name_too_long(authenticated_client):
    response = await authenticated_client.post("/workspaces", json={"name": "x" * 25})
    assert response.status_code == 422


async def test_create_workspace_rejects_duplicate_name_for_same_owner(authenticated_client):
    await authenticated_client.post("/workspaces", json={"name": "Duplicate"})
    response = await authenticated_client.post("/workspaces", json={"name": "Duplicate"})

    assert response.status_code == 409


async def test_create_workspace_allows_same_name_for_different_owners(client, db_session):
    await client.post(
        "/auth/register",
        json={"email": "wsowner1@example.com", "password": "password123", "display_name": "Owner One"},
    )
    await verify_user(db_session, "wsowner1@example.com")
    login_one = await client.post(
        "/auth/jwt/login", data={"username": "wsowner1@example.com", "password": "password123"}
    )
    token_one = login_one.json()["access_token"]

    await client.post(
        "/auth/register",
        json={"email": "wsowner2@example.com", "password": "password123", "display_name": "Owner Two"},
    )
    await verify_user(db_session, "wsowner2@example.com")
    login_two = await client.post(
        "/auth/jwt/login", data={"username": "wsowner2@example.com", "password": "password123"}
    )
    token_two = login_two.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token_one}"
    response_one = await client.post("/workspaces", json={"name": "Shared Name"})
    assert response_one.status_code == 201

    client.headers["Authorization"] = f"Bearer {token_two}"
    response_two = await client.post("/workspaces", json={"name": "Shared Name"})
    assert response_two.status_code == 201


async def test_rename_workspace_requires_auth(authenticated_client, workspace_id):
    del authenticated_client.headers["Authorization"]
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}", json={"name": "New Name"}
    )
    assert response.status_code == 401


async def test_rename_workspace(authenticated_client, workspace_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}", json={"name": "Renamed"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


async def test_rename_workspace_with_empty_body_changes_nothing(authenticated_client, workspace_id):
    response = await authenticated_client.patch(f"/workspaces/{workspace_id}", json={})

    assert response.status_code == 200
    assert response.json()["name"] == "My Workspace"


async def test_rename_workspace_rejects_explicit_null(authenticated_client, workspace_id):
    response = await authenticated_client.patch(f"/workspaces/{workspace_id}", json={"name": None})
    assert response.status_code == 422


async def test_rename_workspace_rejects_blank_name(authenticated_client, workspace_id):
    response = await authenticated_client.patch(f"/workspaces/{workspace_id}", json={"name": "   "})
    assert response.status_code == 422


async def test_rename_workspace_not_found(authenticated_client):
    response = await authenticated_client.patch("/workspaces/999999", json={"name": "New Name"})
    assert response.status_code == 404


async def test_rename_workspace_rejects_duplicate_name(authenticated_client, workspace_id):
    await authenticated_client.post("/workspaces", json={"name": "Existing"})

    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}", json={"name": "Existing"}
    )
    assert response.status_code == 409


async def test_cannot_rename_other_users_workspace(client, db_session, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "intruder@example.com", "password": "password123", "display_name": "Intruder"},
    )
    await verify_user(db_session, "intruder@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "intruder@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.patch(f"/workspaces/{workspace_id}", json={"name": "Hijacked"})
    assert response.status_code == 404


async def test_delete_workspace_requires_auth(authenticated_client, workspace_id):
    del authenticated_client.headers["Authorization"]
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}")
    assert response.status_code == 401


async def test_delete_workspace(authenticated_client, workspace_id):
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}")
    assert response.status_code == 204

    follow_up = await authenticated_client.patch(
        f"/workspaces/{workspace_id}", json={"name": "Should Not Exist"}
    )
    assert follow_up.status_code == 404


async def test_delete_workspace_not_found(authenticated_client):
    response = await authenticated_client.delete("/workspaces/999999")
    assert response.status_code == 404


async def test_cannot_delete_other_users_workspace(client, db_session, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "intruder2@example.com", "password": "password123", "display_name": "Intruder"},
    )
    await verify_user(db_session, "intruder2@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "intruder2@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.delete(f"/workspaces/{workspace_id}")
    assert response.status_code == 404


async def test_list_workspaces_requires_auth(client):
    response = await client.get("/workspaces")
    assert response.status_code == 401


async def test_list_workspaces_includes_default_workspace(authenticated_client):
    response = await authenticated_client.get("/workspaces")

    assert response.status_code == 200
    names = {workspace["name"] for workspace in response.json()}
    assert names == {"My workspace"}


async def test_list_workspaces_returns_owned(authenticated_client):
    await authenticated_client.post("/workspaces", json={"name": "First"})
    await authenticated_client.post("/workspaces", json={"name": "Second"})

    response = await authenticated_client.get("/workspaces")

    assert response.status_code == 200
    names = {workspace["name"] for workspace in response.json()}
    assert names == {"My workspace", "First", "Second"}


async def test_list_workspaces_excludes_other_users_workspaces(client, db_session, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "listviewer@example.com", "password": "password123", "display_name": "Viewer"},
    )
    await verify_user(db_session, "listviewer@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "listviewer@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.get("/workspaces")

    assert response.status_code == 200
    names = {workspace["name"] for workspace in response.json()}
    assert names == {"My workspace"}


async def test_get_workspace_requires_auth(authenticated_client, workspace_id):
    del authenticated_client.headers["Authorization"]
    response = await authenticated_client.get(f"/workspaces/{workspace_id}")
    assert response.status_code == 401


async def test_get_workspace(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workspace_id
    assert data["name"] == "My Workspace"


async def test_get_workspace_not_found(authenticated_client):
    response = await authenticated_client.get("/workspaces/999999")
    assert response.status_code == 404


async def test_cannot_get_other_users_workspace(client, db_session, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "viewer2@example.com", "password": "password123", "display_name": "Viewer Two"},
    )
    await verify_user(db_session, "viewer2@example.com")
    login = await client.post(
        "/auth/jwt/login", data={"username": "viewer2@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.get(f"/workspaces/{workspace_id}")
    assert response.status_code == 404


async def test_cannot_delete_last_workspace(authenticated_client):
    response = await authenticated_client.get("/workspaces")
    assert response.status_code == 200

    workspaces = response.json()
    assert len(workspaces) == 1

    workspace_id = workspaces[0]["id"]

    response = await authenticated_client.delete(
        f"/workspaces/{workspace_id}"
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot delete the last workspace"
