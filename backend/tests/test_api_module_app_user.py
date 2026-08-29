"""Independent App user authentication flow tests."""

from uuid import uuid4

from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body.get("data")


def test_app_user_register_login_profile_refresh_logout(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """The App auth flow is independent while the admin login remains available."""
    assert test_client.get("/system/user/current/info", headers=auth_headers).status_code == 200

    username = f"phase5_{uuid4().hex[:12]}"
    password = "AppUser123!"
    register_response = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": password, "nickname": "Phase 5 User"},
    )
    assert register_response.status_code == 200, register_response.text
    registered = response_data(register_response)
    assert registered["username"] == username
    assert registered["nickname"] == "Phase 5 User"
    assert "password" not in registered

    login_response = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    login_data = response_data(login_response)
    assert login_data["user_info"]["username"] == username
    assert "password" not in login_data["user_info"]
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    app_headers = {"Authorization": f"Bearer {access_token}"}

    me_response = test_client.get("/app/auth/me", headers=app_headers)
    assert me_response.status_code == 200, me_response.text
    assert response_data(me_response)["nickname"] == "Phase 5 User"

    profile_response = test_client.get("/app/user/profile", headers=app_headers)
    assert profile_response.status_code == 200, profile_response.text
    assert response_data(profile_response)["username"] == username

    refresh_response = test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    refreshed = response_data(refresh_response)
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    logout_response = test_client.post("/app/auth/logout", headers=app_headers, json={})
    assert logout_response.status_code == 200, logout_response.text
    assert test_client.get("/app/auth/me", headers=app_headers).status_code == 401
