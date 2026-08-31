"""Targeted App personal-center and authenticated password tests."""

from uuid import uuid4


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def test_profile_exposes_business_user_summary_without_credentials(test_client):
    username = f"profile_{uuid4().hex[:12]}"
    password = "Profile123!"
    register = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": password, "nickname": "Profile User"},
    )
    assert register.status_code == 200, register.text
    user = response_data(register)

    login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    token = response_data(login)["access_token"]

    profile = test_client.get(
        "/app/user/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile.status_code == 200, profile.text
    profile_data = response_data(profile)
    assert profile_data["id"] == user["id"]
    assert profile_data["referral_code"]
    assert profile_data["has_referrer"] is False
    assert profile_data["kyc_status"] == "unverified"
    assert "password" not in profile_data


def test_authenticated_password_change_revokes_existing_sessions(test_client):
    username = f"password_{uuid4().hex[:12]}"
    old_password = "Password123!"
    new_password = "Password456!"
    register = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": old_password},
    )
    assert register.status_code == 200, register.text

    first_login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": old_password},
    )
    assert first_login.status_code == 200, first_login.text
    first_tokens = response_data(first_login)
    first_headers = {"Authorization": f"Bearer {first_tokens['access_token']}"}

    second_login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": old_password},
    )
    assert second_login.status_code == 200, second_login.text
    second_tokens = response_data(second_login)

    wrong_current = test_client.post(
        "/app/auth/change-password",
        headers=first_headers,
        json={"current_password": "wrong-password", "new_password": new_password},
    )
    assert wrong_current.status_code == 401, wrong_current.text

    changed = test_client.post(
        "/app/auth/change-password",
        headers=first_headers,
        json={"current_password": old_password, "new_password": new_password},
    )
    assert changed.status_code == 200, changed.text
    assert test_client.get("/app/auth/me", headers=first_headers).status_code == 401
    assert test_client.get(
        "/app/auth/me",
        headers={"Authorization": f"Bearer {second_tokens['access_token']}"},
    ).status_code == 401
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": first_tokens["refresh_token"]},
    ).status_code == 401

    old_login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": old_password},
    )
    assert old_login.status_code == 401, old_login.text
    new_login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": new_password},
    )
    assert new_login.status_code == 200, new_login.text
