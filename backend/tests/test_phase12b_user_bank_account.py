"""Phase 12B User Bank Account Foundation targeted tests."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config.setting import settings
from app.core.database import engine
from app.core.sensitive import REDACTED_VALUE, redact_sensitive_payload, redact_sensitive_text


@pytest.fixture(autouse=True)
def disable_operation_logging_for_phase12b():
    """Keep this focused suite free of unrelated SQLite background log locks."""

    original_methods = settings.OPERATION_RECORD_METHOD
    settings.OPERATION_RECORD_METHOD = []
    try:
        yield
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def register_user(test_client: TestClient, prefix: str) -> dict:
    username = f"{prefix}_{uuid4().hex[:12]}"
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": username,
            "password": "Phase12B!123",
            "nickname": f"{prefix} nickname",
            "mobile": f"138{uuid4().int % 100_000_000:08d}",
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def app_user_headers(test_client: TestClient, username: str) -> dict[str, str]:
    response = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": "Phase12B!123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response_data(response)['access_token']}"}


def create_bank_account(
    test_client: TestClient,
    headers: dict[str, str],
    card_number: str,
    *,
    is_default: bool = False,
) -> dict:
    response = test_client.post(
        "/app/user/bank-accounts",
        headers=headers,
        json={
            "bank_name": "招商银行",
            "account_name": "张三",
            "card_number": card_number,
            "branch_name": "科技园支行",
            "is_default": is_default,
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def test_app_bank_account_lifecycle_encrypts_card_and_masks_responses(test_client: TestClient) -> None:
    user = register_user(test_client, "phase12b_lifecycle")
    headers = app_user_headers(test_client, user["username"])
    first_card = "6222021234567890"
    second_card = "6217009876543210"
    replacement_card = "6234567890123456"

    first = create_bank_account(test_client, headers, first_card)
    assert first["is_default"] is True
    assert first["masked_card_number"] == "**** **** **** 7890"
    assert "card_number" not in first
    assert "card_last4" not in first
    assert first_card not in str(first)

    second = create_bank_account(test_client, headers, second_card)
    assert second["is_default"] is False

    listed = response_data(test_client.get("/app/user/bank-accounts", headers=headers))
    assert [item["id"] for item in listed] == [first["id"], second["id"]]
    assert sum(item["is_default"] for item in listed) == 1
    assert first_card not in str(listed)
    assert second_card not in str(listed)

    switched = test_client.put(f"/app/user/bank-accounts/{second['id']}/default", headers=headers, json={})
    assert switched.status_code == 200, switched.text
    assert response_data(switched)["is_default"] is True

    listed = response_data(test_client.get("/app/user/bank-accounts", headers=headers))
    assert next(item for item in listed if item["id"] == first["id"])["is_default"] is False
    assert next(item for item in listed if item["id"] == second["id"])["is_default"] is True

    deleted = test_client.delete(f"/app/user/bank-accounts/{second['id']}", headers=headers)
    assert deleted.status_code == 200, deleted.text
    listed = response_data(test_client.get("/app/user/bank-accounts", headers=headers))
    assert [item["id"] for item in listed] == [first["id"]]
    assert listed[0]["is_default"] is True

    replaced = test_client.put(
        f"/app/user/bank-accounts/{first['id']}",
        headers=headers,
        json={"card_number": replacement_card, "account_name": "张三"},
    )
    assert replaced.status_code == 200, replaced.text
    replacement_data = response_data(replaced)
    assert replacement_data["masked_card_number"] == "**** **** **** 3456"
    assert replacement_card not in replaced.text

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT card_number, card_last4 FROM app_user_bank_account WHERE id = :id"),
            {"id": first["id"]},
        ).mappings().one()
    assert row["card_last4"] == "3456"
    assert row["card_number"] != replacement_card
    assert replacement_card not in row["card_number"]
    assert str(row["card_number"]).startswith("gAAAA")


def test_disabled_default_replacement_admin_status_and_safe_admin_views(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    user = register_user(test_client, "phase12b_admin")
    app_headers = app_user_headers(test_client, user["username"])
    first = create_bank_account(test_client, app_headers, "6222333344445555")
    second = create_bank_account(test_client, app_headers, "6211111122223333")

    disabled = test_client.patch(
        f"/system/app_user_bank_account/status/{first['id']}",
        headers=auth_headers,
        json={"action": "disable"},
    )
    assert disabled.status_code == 200, disabled.text
    disabled_data = response_data(disabled)
    assert disabled_data["status"] == 1
    assert disabled_data["is_default"] is False
    assert "6222333344445555" not in disabled.text

    listed = response_data(test_client.get("/app/user/bank-accounts", headers=app_headers))
    disabled_row = next(item for item in listed if item["id"] == first["id"])
    active_row = next(item for item in listed if item["id"] == second["id"])
    assert disabled_row["status"] == 1
    assert active_row["is_default"] is True

    cannot_default = test_client.put(f"/app/user/bank-accounts/{first['id']}/default", headers=app_headers, json={})
    assert cannot_default.status_code == 409, cannot_default.text
    assert "6222333344445555" not in cannot_default.text

    enabled = test_client.patch(
        f"/system/app_user_bank_account/status/{first['id']}",
        headers=auth_headers,
        json={"action": "enable"},
    )
    assert enabled.status_code == 200, enabled.text
    assert response_data(enabled)["status"] == 0
    assert response_data(enabled)["is_default"] is False

    admin_list = test_client.get(
        "/system/app_user_bank_account/list",
        headers=auth_headers,
        params={
            "page_no": 1,
            "page_size": 10,
            "keyword": "3333",
            "status": 0,
            "created_time": ["2000-01-01 00:00:00", "2100-01-01 00:00:00"],
        },
    )
    assert admin_list.status_code == 200, admin_list.text
    admin_page = response_data(admin_list)
    assert admin_page["total"] == 1
    admin_row = admin_page["items"][0]
    assert admin_row["masked_card_number"] == "**** **** **** 3333"
    assert "card_number" not in admin_row
    assert "card_last4" not in admin_row
    assert "6211111122223333" not in admin_list.text

    detail = test_client.get(
        f"/system/app_user_bank_account/detail/{second['id']}",
        headers=auth_headers,
    )
    assert detail.status_code == 200, detail.text
    detail_data = response_data(detail)
    assert detail_data["app_user"]["kyc_status"] == "unverified"
    assert detail_data["masked_card_number"] == "**** **** **** 3333"
    assert "6211111122223333" not in detail.text

    no_admin_create = test_client.post(
        "/system/app_user_bank_account",
        headers=auth_headers,
        json={"user_id": user["id"], "card_number": "6222000011112222"},
    )
    assert no_admin_create.status_code == 404, no_admin_create.text


def test_bank_account_ownership_and_sensitive_error_redaction(test_client: TestClient) -> None:
    owner = register_user(test_client, "phase12b_owner")
    other = register_user(test_client, "phase12b_other")
    owner_headers = app_user_headers(test_client, owner["username"])
    other_headers = app_user_headers(test_client, other["username"])
    card_number = "6222999988887777"
    account = create_bank_account(test_client, owner_headers, card_number)

    cross_read = test_client.get(f"/app/user/bank-accounts/{account['id']}", headers=other_headers)
    assert cross_read.status_code == 404, cross_read.text

    cross_edit = test_client.put(
        f"/app/user/bank-accounts/{account['id']}",
        headers=other_headers,
        json={"account_name": "越权修改", "card_number": card_number},
    )
    assert cross_edit.status_code == 404, cross_edit.text
    assert card_number not in cross_edit.text

    cross_delete = test_client.delete(f"/app/user/bank-accounts/{account['id']}", headers=other_headers)
    assert cross_delete.status_code == 404, cross_delete.text

    cross_default = test_client.put(f"/app/user/bank-accounts/{account['id']}/default", headers=other_headers, json={})
    assert cross_default.status_code == 404, cross_default.text

    spoofed = test_client.post(
        "/app/user/bank-accounts",
        headers=other_headers,
        json={
            "user_id": owner["id"],
            "bank_name": "招商银行",
            "account_name": "伪造归属",
            "card_number": card_number,
        },
    )
    assert spoofed.status_code == 422, spoofed.text
    assert card_number not in spoofed.text

    invalid = test_client.post(
        "/app/user/bank-accounts",
        headers=other_headers,
        json={
            "bank_name": "招商银行",
            "account_name": "错误卡号",
            "card_number": "not-a-card-number",
        },
    )
    assert invalid.status_code == 422, invalid.text
    assert "not-a-card-number" not in invalid.text

    other_list = response_data(test_client.get("/app/user/bank-accounts", headers=other_headers))
    assert other_list == []

    payload = redact_sensitive_payload({"card_number": card_number, "nested": [{"card_number": card_number}]})
    assert payload == {"card_number": REDACTED_VALUE, "nested": [{"card_number": REDACTED_VALUE}]}
    assert card_number not in redact_sensitive_text(f"card_number={card_number}")


def test_bank_account_operation_log_contains_no_plaintext_card_number(
    test_client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = register_user(test_client, "phase12b_log")
    app_headers = app_user_headers(test_client, user["username"])
    card_number = "6222888877776666"
    account = create_bank_account(test_client, app_headers, card_number)
    captured: dict = {}

    async def capture_operation_log(log_data: dict) -> None:
        captured.update(log_data)

    monkeypatch.setattr("app.core.router_class._write_operation_log_async", capture_operation_log)
    original_methods = settings.OPERATION_RECORD_METHOD
    settings.OPERATION_RECORD_METHOD = ["PATCH"]
    try:
        response = test_client.patch(
            f"/system/app_user_bank_account/status/{account['id']}",
            headers=auth_headers,
            json={"action": "disable"},
        )
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods

    assert response.status_code == 200, response.text
    assert captured
    assert card_number not in str(captured)
    assert "**** **** **** 6666" in captured["response_json"]
