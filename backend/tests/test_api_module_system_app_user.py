"""Admin management tests for the independent App user model."""

from uuid import uuid4

from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body.get("data")


def test_admin_manages_app_user_without_exposing_password(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    username = f"phase7_{uuid4().hex[:12]}"
    password = "Phase7Old!1"
    mobile = f"138{uuid4().int % 10**8:08d}"

    register_response = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": password, "nickname": "Phase 7 User"},
    )
    assert register_response.status_code == 200, register_response.text
    app_user = response_data(register_response)
    app_user_id = app_user["id"]

    app_login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    )
    assert app_login.status_code == 200, app_login.text
    app_headers = {"Authorization": f"Bearer {response_data(app_login)['access_token']}"}

    listed = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "username": username},
        headers=auth_headers,
    )
    assert listed.status_code == 200, listed.text
    list_data = response_data(listed)
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == app_user_id
    assert "password" not in list_data["items"][0]

    detail = test_client.get(f"/system/app_user/detail/{app_user_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert "password" not in response_data(detail)

    updated = test_client.put(
        f"/system/app_user/update/{app_user_id}",
        json={"nickname": "Phase 7 Edited", "mobile": mobile, "avatar": "https://example.com/avatar.png"},
        headers=auth_headers,
    )
    assert updated.status_code == 200, updated.text
    assert response_data(updated)["nickname"] == "Phase 7 Edited"
    assert "password" not in response_data(updated)

    profile = test_client.get("/app/auth/me", headers=app_headers)
    assert profile.status_code == 200, profile.text
    assert response_data(profile)["nickname"] == "Phase 7 Edited"
    assert response_data(profile)["mobile"] == mobile

    disabled = test_client.patch(
        "/system/app_user/status/batch",
        json={"ids": [app_user_id], "status": 1},
        headers=auth_headers,
    )
    assert disabled.status_code == 200, disabled.text
    assert test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    ).status_code == 401
    assert test_client.get("/app/auth/me", headers=app_headers).status_code == 401

    enabled = test_client.patch(
        "/system/app_user/status/batch",
        json={"ids": [app_user_id], "status": 0},
        headers=auth_headers,
    )
    assert enabled.status_code == 200, enabled.text
    assert test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    ).status_code == 200

    new_password = "Phase7New!2"
    reset = test_client.put(
        f"/system/app_user/password/reset/{app_user_id}",
        json={"password": new_password},
        headers=auth_headers,
    )
    assert reset.status_code == 200, reset.text
    assert "password" not in response_data(reset)
    assert test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    ).status_code == 401
    assert test_client.post(
        "/app/auth/login",
        json={"username": username, "password": new_password},
    ).status_code == 200

    assert test_client.get("/system/user/current/info", headers=auth_headers).status_code == 200
