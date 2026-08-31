"""Phase 11B App authentication contract tests."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.common.enums import EnvironmentEnum
from app.config.setting import settings
from app.plugin.module_system.sms.constants import get_fixed_sms_code


@pytest.fixture(autouse=True)
def phase11b_test_settings():
    """Keep this focused API suite deterministic and free of log-writer locks."""

    original_methods = settings.OPERATION_RECORD_METHOD
    original_fixed_enabled = settings.APP_SMS_FIXED_CODE_ENABLED
    original_fixed_code = settings.APP_SMS_FIXED_CODE
    original_environment = settings.ENVIRONMENT
    settings.OPERATION_RECORD_METHOD = []
    settings.APP_SMS_FIXED_CODE_ENABLED = True
    settings.APP_SMS_FIXED_CODE = "888888"
    settings.ENVIRONMENT = EnvironmentEnum.DEV
    try:
        yield
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods
        settings.APP_SMS_FIXED_CODE_ENABLED = original_fixed_enabled
        settings.APP_SMS_FIXED_CODE = original_fixed_code
        settings.ENVIRONMENT = original_environment


@pytest.fixture
def phase11b_auth_headers(test_client):
    """Authenticate the seeded admin without enabling the log-writer path."""

    original_methods = settings.OPERATION_RECORD_METHOD
    settings.OPERATION_RECORD_METHOD = []
    try:
        with patch("app.api.v1.module_system.auth.service._write_login_log", new=AsyncMock(return_value=None)):
            response = test_client.post(
                "/system/auth/login",
                data={"username": "admin", "password": "admin123"},
            )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response_data(response)['access_token']}"}
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def new_mobile() -> str:
    return f"138{uuid4().int % 100_000_000:08d}"


def send_code(test_client, mobile: str, scene: str) -> dict:
    response = test_client.post("/app/sms/send-code", json={"mobile": mobile, "scene": scene})
    assert response.status_code == 200, response.text
    data = response_data(response)
    assert data["expires_in"] > 0
    assert data["resend_after"] == 60
    assert data["debug_code"] == "888888"
    return data


def register_mobile(test_client, mobile: str | None = None, *, referral_code: str | None = None) -> dict:
    mobile = mobile or new_mobile()
    send_code(test_client, mobile, "register_code")
    body = {
        "mobile": mobile,
        "code": "888888",
        "password": "Phase11B!123",
        "nickname": "Phase 11B User",
    }
    if referral_code:
        body["referral_code"] = referral_code
    response = test_client.post("/app/auth/register", json=body)
    assert response.status_code == 200, response.text
    return response_data(response)


def test_mobile_registration_password_sms_login_and_single_use(test_client):
    mobile = new_mobile()
    user = register_mobile(test_client, mobile)
    assert user["mobile"] == mobile
    assert user["status"] == 0
    assert user["referral_code"]

    duplicate = test_client.post(
        "/app/auth/register",
        json={
            "mobile": mobile,
            "code": "888888",
            "password": "Phase11B!123",
        },
    )
    assert duplicate.status_code == 409, duplicate.text

    password_login = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert password_login.status_code == 200, password_login.text
    password_data = response_data(password_login)
    assert password_data["user_info"]["mobile"] == mobile

    wrong_password = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401, wrong_password.text

    send_code(test_client, mobile, "login_code")
    sms_login = test_client.post(
        "/app/auth/login/sms",
        json={"mobile": mobile, "code": "888888"},
    )
    assert sms_login.status_code == 200, sms_login.text
    reused_code = test_client.post(
        "/app/auth/login/sms",
        json={"mobile": mobile, "code": "888888"},
    )
    assert reused_code.status_code == 422, reused_code.text


def test_mobile_registration_binds_valid_referral_and_rejects_invalid_referral(test_client):
    referrer = register_mobile(test_client)
    child = register_mobile(test_client, referral_code=referrer["referral_code"].lower())
    assert child["referrer_id"] == referrer["id"]
    assert child["has_referrer"] is True
    assert child["referrer"]["referral_code"] == referrer["referral_code"]
    assert child["referrer_bound_at"]

    invalid_mobile = new_mobile()
    send_code(test_client, invalid_mobile, "register_code")
    invalid = test_client.post(
        "/app/auth/register",
        json={
            "mobile": invalid_mobile,
            "code": "888888",
            "password": "Phase11B!123",
            "referral_code": "NOT-A-REAL-CODE",
        },
    )
    assert invalid.status_code != 200, invalid.text


def test_reset_password_consumes_code_and_invalidates_existing_sessions(test_client):
    mobile = new_mobile()
    register_mobile(test_client, mobile)
    login = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert login.status_code == 200, login.text
    login_data = response_data(login)
    old_headers = {"Authorization": f"Bearer {login_data['access_token']}"}

    send_code(test_client, mobile, "reset_password_code")
    reset = test_client.post(
        "/app/auth/reset-password",
        json={"mobile": mobile, "code": "888888", "new_password": "Phase11B!456"},
    )
    assert reset.status_code == 200, reset.text
    assert test_client.get("/app/auth/me", headers=old_headers).status_code == 401
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    ).status_code == 401

    old_password = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert old_password.status_code == 401, old_password.text
    new_password = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!456"},
    )
    assert new_password.status_code == 200, new_password.text


def test_admin_reset_password_invalidates_app_sessions(test_client, phase11b_auth_headers):
    mobile = new_mobile()
    user = register_mobile(test_client, mobile)
    login = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert login.status_code == 200, login.text
    login_data = response_data(login)
    old_headers = {"Authorization": f"Bearer {login_data['access_token']}"}

    reset = test_client.put(
        f"/system/app_user/password/reset/{user['id']}",
        headers=phase11b_auth_headers,
        json={"password": "Phase11B!789"},
    )
    assert reset.status_code == 200, reset.text
    assert test_client.get("/app/auth/me", headers=old_headers).status_code == 401
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    ).status_code == 401


def test_disabled_rejects_all_auth_paths_but_frozen_can_login_and_refresh(
    test_client,
    phase11b_auth_headers,
):
    mobile = new_mobile()
    user = register_mobile(test_client, mobile)
    password_login = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert password_login.status_code == 200, password_login.text
    password_data = response_data(password_login)
    existing_headers = {"Authorization": f"Bearer {password_data['access_token']}"}

    frozen = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=phase11b_auth_headers,
        json={"action": "freeze"},
    )
    assert frozen.status_code == 200, frozen.text
    frozen_password = test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    )
    assert frozen_password.status_code == 200, frozen_password.text
    assert response_data(frozen_password)["user_info"]["status"] == 2
    send_code(test_client, mobile, "login_code")
    frozen_sms = test_client.post(
        "/app/auth/login/sms",
        json={"mobile": mobile, "code": "888888"},
    )
    assert frozen_sms.status_code == 200, frozen_sms.text
    assert test_client.get("/app/auth/me", headers=existing_headers).status_code == 200
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": password_data["refresh_token"]},
    ).status_code == 200

    unfreeze = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=phase11b_auth_headers,
        json={"action": "unfreeze"},
    )
    assert unfreeze.status_code == 200, unfreeze.text
    disable = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=phase11b_auth_headers,
        json={"action": "disable"},
    )
    assert disable.status_code == 200, disable.text
    assert test_client.post(
        "/app/auth/login/password",
        json={"mobile": mobile, "password": "Phase11B!123"},
    ).status_code == 401
    disabled_sms_mobile = new_mobile()
    disabled_sms_user = register_mobile(test_client, disabled_sms_mobile)
    disabled_sms = test_client.patch(
        f"/system/app_user/status/{disabled_sms_user['id']}",
        headers=phase11b_auth_headers,
        json={"action": "disable"},
    )
    assert disabled_sms.status_code == 200, disabled_sms.text
    send_code(test_client, disabled_sms_mobile, "login_code")
    assert test_client.post(
        "/app/auth/login/sms",
        json={"mobile": disabled_sms_mobile, "code": "888888"},
    ).status_code == 401
    assert test_client.get("/app/auth/me", headers=existing_headers).status_code == 401
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": password_data["refresh_token"]},
    ).status_code == 401


def test_fixed_code_is_enabled_in_dev_and_protected_in_production():
    assert get_fixed_sms_code() == "888888"
    settings.ENVIRONMENT = EnvironmentEnum.PROD
    assert get_fixed_sms_code() is None
    settings.ENVIRONMENT = "test"
    assert get_fixed_sms_code() == "888888"
    settings.ENVIRONMENT = "staging"
    assert get_fixed_sms_code() is None
