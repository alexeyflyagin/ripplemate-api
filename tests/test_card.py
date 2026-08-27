async def test_create_card_requires_auth(client, workspace_id):
    del client.headers["Authorization"]
    response = await client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Test"})
    assert response.status_code == 401


async def test_create_card_without_category(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Hello"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["term"] == "Hello"
    assert data["category_id"] is None
    assert "id" in data
    assert "created_at" in data


async def test_create_card_with_category(authenticated_client, workspace_id, category_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Hello", "category_id": category_id}
    )

    assert response.status_code == 201
    assert response.json()["category_id"] == category_id


async def test_create_card_rejects_blank_term(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "   "}
    )
    assert response.status_code == 422


async def test_create_card_rejects_term_too_long(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "x" * 256}
    )
    assert response.status_code == 422


async def test_create_card_rejects_nonexistent_category(authenticated_client, workspace_id):
    response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Hello", "category_id": "nonexistent"}
    )
    assert response.status_code == 404


async def test_create_card_rejects_category_from_different_workspace(
        authenticated_client, workspace_id, category_id
):
    other_workspace = await authenticated_client.post("/workspaces", json={"name": "Other"})
    other_workspace_id = other_workspace.json()["id"]

    response = await authenticated_client.post(
        f"/workspaces/{other_workspace_id}/cards",
        json={"term": "Hello", "category_id": category_id},
    )
    assert response.status_code == 404


async def test_create_card_workspace_not_found(authenticated_client):
    response = await authenticated_client.post("/workspaces/999999/cards", json={"term": "Hello"})
    assert response.status_code == 404


async def test_cannot_create_card_in_other_users_workspace(client, workspace_id):
    await client.post(
        "/auth/register",
        json={"email": "cardintruder@example.com", "password": "password123", "display_name": "Intruder"},
    )
    login = await client.post(
        "/auth/jwt/login", data={"username": "cardintruder@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Hijacked"})
    assert response.status_code == 404


async def test_list_cards_empty(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0


async def test_list_cards_returns_all_regardless_of_category(
        authenticated_client, workspace_id, category_id
):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Uncategorized"})
    await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Categorized", "category_id": category_id}
    )

    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    terms = {card["term"] for card in data["items"]}
    assert terms == {"Uncategorized", "Categorized"}


async def test_list_cards_filters_by_category(authenticated_client, workspace_id, category_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Uncategorized"})
    await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Categorized", "category_id": category_id}
    )

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"category_id": category_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["term"] == "Categorized"


async def test_list_cards_pagination(authenticated_client, workspace_id):
    for i in range(5):
        await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": f"Card {i}"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"limit": 2, "offset": 0}
    )
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"limit": 2, "offset": 4}
    )
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 1


async def test_list_cards_rejects_limit_too_low(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards", params={"limit": 0})
    assert response.status_code == 422


async def test_list_cards_rejects_limit_too_high(authenticated_client, workspace_id):
    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"limit": 301}
    )
    assert response.status_code == 422


async def test_list_cards_rejects_negative_offset(authenticated_client, workspace_id):
    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"offset": -1}
    )
    assert response.status_code == 422


async def test_get_card(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards/{card_id}")

    assert response.status_code == 200
    assert response.json()["id"] == card_id


async def test_get_card_not_found(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards/999999")
    assert response.status_code == 404


async def test_cannot_get_card_in_other_users_workspace(client, workspace_id, card_id):
    await client.post(
        "/auth/register",
        json={"email": "cardintruder2@example.com", "password": "password123", "display_name": "Intruder"},
    )
    login = await client.post(
        "/auth/jwt/login", data={"username": "cardintruder2@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.get(f"/workspaces/{workspace_id}/cards/{card_id}")
    assert response.status_code == 404


async def test_update_card_term(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"term": "Updated"}
    )

    assert response.status_code == 200
    assert response.json()["term"] == "Updated"


async def test_update_card_assigns_category(authenticated_client, workspace_id, category_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"category_id": category_id}
    )

    assert response.status_code == 200
    assert response.json()["category_id"] == category_id


async def test_update_card_unassigns_category(authenticated_client, workspace_id, category_id):
    create_response = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Hello", "category_id": category_id}
    )
    card_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"category_id": None}
    )

    assert response.status_code == 200
    assert response.json()["category_id"] is None


async def test_update_card_with_empty_body_changes_nothing(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(f"/workspaces/{workspace_id}/cards/{card_id}", json={})

    assert response.status_code == 200
    assert response.json()["term"] == "My Term"


async def test_update_card_rejects_explicit_null_term(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"term": None}
    )
    assert response.status_code == 422


async def test_update_card_rejects_blank_term(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"term": "   "}
    )
    assert response.status_code == 422


async def test_update_card_rejects_nonexistent_category(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"category_id": "nonexistent"}
    )
    assert response.status_code == 404


async def test_update_card_not_found(authenticated_client, workspace_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/999999", json={"term": "New"}
    )
    assert response.status_code == 404


async def test_cannot_update_card_in_other_users_workspace(client, workspace_id, card_id):
    await client.post(
        "/auth/register",
        json={"email": "cardintruder3@example.com", "password": "password123", "display_name": "Intruder"},
    )
    login = await client.post(
        "/auth/jwt/login", data={"username": "cardintruder3@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"term": "Hijacked"}
    )
    assert response.status_code == 404


async def test_delete_card(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}/cards/{card_id}")
    assert response.status_code == 204

    follow_up = await authenticated_client.get(f"/workspaces/{workspace_id}/cards/{card_id}")
    assert follow_up.status_code == 404


async def test_delete_card_not_found(authenticated_client, workspace_id):
    response = await authenticated_client.delete(f"/workspaces/{workspace_id}/cards/999999")
    assert response.status_code == 404


async def test_cannot_delete_card_in_other_users_workspace(client, workspace_id, card_id):
    await client.post(
        "/auth/register",
        json={"email": "cardintruder4@example.com", "password": "password123", "display_name": "Intruder"},
    )
    login = await client.post(
        "/auth/jwt/login", data={"username": "cardintruder4@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.delete(f"/workspaces/{workspace_id}/cards/{card_id}")
    assert response.status_code == 404


async def test_get_random_card_requires_auth(client, workspace_id):
    del client.headers["Authorization"]
    response = await client.get(f"/workspaces/{workspace_id}/cards/random")
    assert response.status_code == 401


async def test_get_random_card_no_cards_returns_404(authenticated_client, workspace_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards/random")
    assert response.status_code == 404


async def test_get_random_card_returns_a_card(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.get(f"/workspaces/{workspace_id}/cards/random")

    assert response.status_code == 200
    assert response.json()["id"] == card_id


async def test_get_random_card_filters_by_category(authenticated_client, workspace_id, category_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Uncategorized"})
    categorized = await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Categorized", "category_id": category_id}
    )
    categorized_id = categorized.json()["id"]

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards/random", params={"category_id": category_id}
    )

    assert response.status_code == 200
    assert response.json()["id"] == categorized_id


async def test_get_random_card_rejects_nonexistent_category(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards/random", params={"category_id": "nonexistent"}
    )
    assert response.status_code == 404


async def test_get_random_card_workspace_not_found(authenticated_client):
    response = await authenticated_client.get("/workspaces/999999/cards/random")
    assert response.status_code == 404


async def test_cannot_get_random_card_in_other_users_workspace(client, workspace_id, card_id):
    await client.post(
        "/auth/register",
        json={"email": "randomintruder@example.com", "password": "password123", "display_name": "Intruder"},
    )
    login = await client.post(
        "/auth/jwt/login", data={"username": "randomintruder@example.com", "password": "password123"}
    )
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    response = await client.get(f"/workspaces/{workspace_id}/cards/random")
    assert response.status_code == 404


async def test_list_cards_search_finds_matching_term(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Apple"})
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Banana"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"search": "App"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["term"] == "Apple"


async def test_list_cards_search_is_case_insensitive(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Apple"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"search": "apple"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_list_cards_search_matches_substring(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Pineapple"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"search": "apple"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_list_cards_search_no_match_returns_empty(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Apple"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"search": "zzz"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


async def test_list_cards_search_combined_with_category_filter(
        authenticated_client, workspace_id, category_id
):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Apple"})
    await authenticated_client.post(
        f"/workspaces/{workspace_id}/cards", json={"term": "Apple", "category_id": category_id}
    )

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards",
        params={"search": "Apple", "category_id": category_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category_id"] == category_id


async def test_list_cards_search_escapes_special_characters(authenticated_client, workspace_id):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "cat"})
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "c_t literal"})

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards", params={"search": "c_t"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["term"] == "c_t literal"


async def test_update_card_favorite(authenticated_client, workspace_id, card_id):
    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}", json={"is_favorite": True}
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is True

    response = await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{card_id}",
        json={"is_favorite": False},
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is False


async def test_list_cards_with_favorite_filter(
        authenticated_client, workspace_id
):
    await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Watermelon"})
    apple_card = await authenticated_client.post(f"/workspaces/{workspace_id}/cards", json={"term": "Apple"})
    await authenticated_client.patch(
        f"/workspaces/{workspace_id}/cards/{apple_card.json()["id"]}", json={"is_favorite": True}
    )

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards",
        params={"is_favorite": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["term"] == "Apple"

    response = await authenticated_client.get(
        f"/workspaces/{workspace_id}/cards",
        params={"is_favorite": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["term"] == "Watermelon"
