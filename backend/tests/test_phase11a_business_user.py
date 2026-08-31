"""Phase 11A Business User Foundation regression tests."""

import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.plugin.module_app.user.constants import AppUserStatus
from app.plugin.module_app.user.policy import assert_asset_operation_allowed, is_asset_operation_allowed


@pytest.fixture(autouse=True)
def disable_operation_logging_for_phase11a() -> None:
    """Avoid SQLite lock contention from the unrelated background log writer."""

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


def register_user(test_client: TestClient, prefix: str, *, mobile: str | None = None) -> dict:
    username = f"{prefix}_{uuid4().hex[:12]}"
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": username,
            "password": "Phase11A!123",
            "nickname": f"{prefix} nickname",
            "mobile": mobile,
        },
    )
    assert response.status_code == 200, response.text
    data = response_data(response)
    assert "password" not in data
    return data


def app_user_headers(test_client: TestClient, username: str) -> tuple[dict, dict]:
    response = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": "Phase11A!123"},
    )
    assert response.status_code == 200, response.text
    data = response_data(response)
    return data, {"Authorization": f"Bearer {data['access_token']}"}


def test_referral_binding_cycle_protection_and_admin_summary(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    referrer = register_user(test_client, "phase11a_referrer", mobile="13811110001")
    child = register_user(test_client, "phase11a_child", mobile="13811110002")

    assert referrer["referral_code"] != child["referral_code"]
    assert len(referrer["referral_code"]) == 10
    assert referrer["referral_code"].isalnum()
    assert referrer["has_referrer"] is False
    assert referrer["kyc_status"] == "unverified"

    bind = test_client.post(
        f"/system/app_user/referrer/bind/{child['id']}",
        headers=auth_headers,
        json={"referral_code": referrer["referral_code"].lower()},
    )
    assert bind.status_code == 200, bind.text
    bound = response_data(bind)
    assert bound["referrer_id"] == referrer["id"]
    assert bound["has_referrer"] is True
    assert bound["referrer"]["username"] == referrer["username"]
    assert bound["referrer"]["mobile"] == "13811110001"
    assert bound["referrer_bound_at"]

    duplicate = test_client.post(
        f"/system/app_user/referrer/bind/{child['id']}",
        headers=auth_headers,
        json={"referral_code": referrer["referral_code"]},
    )
    assert duplicate.status_code == 409, duplicate.text

    self_bind = test_client.post(
        f"/system/app_user/referrer/bind/{referrer['id']}",
        headers=auth_headers,
        json={"referral_code": referrer["referral_code"]},
    )
    assert self_bind.status_code == 409, self_bind.text

    invalid_user = register_user(test_client, "phase11a_invalid")
    invalid_code = test_client.post(
        f"/system/app_user/referrer/bind/{invalid_user['id']}",
        headers=auth_headers,
        json={"referral_code": "NOT-A-REAL-CODE"},
    )
    assert invalid_code.status_code != 200, invalid_code.text

    cycle_a = register_user(test_client, "phase11a_cycle_a")
    cycle_b = register_user(test_client, "phase11a_cycle_b")
    first_edge = test_client.post(
        f"/system/app_user/referrer/bind/{cycle_a['id']}",
        headers=auth_headers,
        json={"referral_code": cycle_b["referral_code"]},
    )
    assert first_edge.status_code == 200, first_edge.text
    cycle = test_client.post(
        f"/system/app_user/referrer/bind/{cycle_b['id']}",
        headers=auth_headers,
        json={"referral_code": cycle_a["referral_code"]},
    )
    assert cycle.status_code == 409, cycle.text

    by_code = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "referral_code": child["referral_code"]},
        headers=auth_headers,
    )
    assert by_code.status_code == 200, by_code.text
    assert response_data(by_code)["total"] == 1

    by_referrer = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "referrer": referrer["username"]},
        headers=auth_headers,
    )
    assert by_referrer.status_code == 200, by_referrer.text
    assert [item["id"] for item in response_data(by_referrer)["items"]] == [child["id"]]

    detail = test_client.get(f"/system/app_user/detail/{child['id']}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    detail_data = response_data(detail)
    assert detail_data["referral_code"] == child["referral_code"]
    assert detail_data["referrer"]["username"] == referrer["username"]
    assert "id_card_no" not in detail_data

    _, child_headers = app_user_headers(test_client, child["username"])
    me = test_client.get("/app/auth/me", headers=child_headers)
    assert me.status_code == 200, me.text
    me_data = response_data(me)
    assert me_data["referral_code"] == child["referral_code"]
    assert me_data["has_referrer"] is True
    assert me_data["referrer"]["username"] == referrer["username"]


def test_business_user_status_auth_boundary_and_asset_policy(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    user = register_user(test_client, "phase11a_status")
    login_data, app_headers = app_user_headers(test_client, user["username"])

    assert is_asset_operation_allowed(AppUserStatus.ACTIVE) is True
    assert is_asset_operation_allowed(AppUserStatus.FROZEN) is False
    assert is_asset_operation_allowed(AppUserStatus.DISABLED) is False
    with pytest.raises(CustomException):
        assert_asset_operation_allowed(AppUserStatus.FROZEN)

    frozen = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=auth_headers,
        json={"action": "freeze"},
    )
    assert frozen.status_code == 200, frozen.text
    assert response_data(frozen)["status"] == AppUserStatus.FROZEN
    assert test_client.get("/app/auth/me", headers=app_headers).status_code == 200
    frozen_login = test_client.post(
        "/app/auth/login",
        json={"username": user["username"], "password": "Phase11A!123"},
    )
    assert frozen_login.status_code == 200, frozen_login.text
    assert response_data(frozen_login)["user_info"]["status"] == AppUserStatus.FROZEN

    illegal_disable = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=auth_headers,
        json={"action": "disable"},
    )
    assert illegal_disable.status_code == 409, illegal_disable.text

    unfreeze = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=auth_headers,
        json={"action": "unfreeze"},
    )
    assert unfreeze.status_code == 200, unfreeze.text
    disable = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=auth_headers,
        json={"action": "disable"},
    )
    assert disable.status_code == 200, disable.text
    assert response_data(disable)["status"] == AppUserStatus.DISABLED
    assert test_client.post(
        "/app/auth/login",
        json={"username": user["username"], "password": "Phase11A!123"},
    ).status_code == 401
    assert test_client.get("/app/auth/me", headers=app_headers).status_code == 401
    assert test_client.post(
        "/app/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    ).status_code == 401

    enable = test_client.patch(
        f"/system/app_user/status/{user['id']}",
        headers=auth_headers,
        json={"action": "enable"},
    )
    assert enable.status_code == 200, enable.text
    assert response_data(enable)["status"] == AppUserStatus.ACTIVE
    assert test_client.post(
        "/app/auth/login",
        json={"username": user["username"], "password": "Phase11A!123"},
    ).status_code == 200


def test_kyc_status_aggregation_in_admin_user_summary(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    pending_user = register_user(test_client, "phase11a_pending")
    _, pending_headers = app_user_headers(test_client, pending_user["username"])

    initial = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "username": pending_user["username"], "kyc_status": "unverified"},
        headers=auth_headers,
    )
    assert initial.status_code == 200, initial.text
    assert response_data(initial)["total"] == 1

    kyc_payload = {
        "real_name": "Phase 11A User",
        "id_card_no": "440305199001011234",
        "id_card_front": f"kyc/{pending_user['id']}/front.png",
        "id_card_back": f"kyc/{pending_user['id']}/back.png",
    }
    with patch(
        "app.plugin.module_app.kyc.service.StorageFileService.exists",
        new=AsyncMock(return_value=True),
    ):
        submitted = test_client.post("/app/kyc/submit", headers=pending_headers, json=kyc_payload)
    assert submitted.status_code == 200, submitted.text
    kyc_id = response_data(submitted)["id"]

    pending = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "username": pending_user["username"], "kyc_status": "pending"},
        headers=auth_headers,
    )
    assert pending.status_code == 200, pending.text
    assert response_data(pending)["items"][0]["kyc_status"] == "pending"

    approved = test_client.post(
        f"/system/kyc/review/{kyc_id}",
        headers=auth_headers,
        json={"status": 1},
    )
    assert approved.status_code == 200, approved.text

    detail = test_client.get(f"/system/app_user/detail/{pending_user['id']}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    detail_data = response_data(detail)
    assert detail_data["kyc_status"] == "verified"
    assert detail_data["kyc_reviewed_at"]

    rejected_user = register_user(test_client, "phase11a_rejected")
    _, rejected_headers = app_user_headers(test_client, rejected_user["username"])
    rejected_payload = {**kyc_payload, "id_card_front": f"kyc/{rejected_user['id']}/front.png", "id_card_back": f"kyc/{rejected_user['id']}/back.png"}
    with patch(
        "app.plugin.module_app.kyc.service.StorageFileService.exists",
        new=AsyncMock(return_value=True),
    ):
        rejected_submission = test_client.post("/app/kyc/submit", headers=rejected_headers, json=rejected_payload)
    assert rejected_submission.status_code == 200, rejected_submission.text
    rejected_id = response_data(rejected_submission)["id"]
    rejected = test_client.post(
        f"/system/kyc/review/{rejected_id}",
        headers=auth_headers,
        json={"status": 2, "review_remark": "资料不清晰"},
    )
    assert rejected.status_code == 200, rejected.text

    rejected_list = test_client.get(
        "/system/app_user/list",
        params={"page_no": 1, "page_size": 10, "username": rejected_user["username"], "kyc_status": "rejected"},
        headers=auth_headers,
    )
    assert rejected_list.status_code == 200, rejected_list.text
    assert response_data(rejected_list)["items"][0]["kyc_status"] == "rejected"


def test_existing_user_referral_backfill_migration_is_non_destructive() -> None:
    migration_path = Path(__file__).parents[1] / "app/alembic/versions/11a_business_user_foundation.py"
    spec = importlib.util.spec_from_file_location("phase11a_migration_test", migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        metadata = sa.MetaData()
        users = sa.Table(
            "app_user",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("username", sa.String(64), nullable=False),
            sa.Column("password", sa.String(255), nullable=False),
            sa.Column("nickname", sa.String(128), nullable=False),
            sa.Column("status", sa.Integer, nullable=False, server_default="0"),
            sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.false()),
        )
        metadata.create_all(connection)
        connection.execute(
            users.insert(),
            [
                {"id": 1, "username": "legacy_a", "password": "hash-a", "nickname": "A"},
                {"id": 2, "username": "legacy_b", "password": "hash-b", "nickname": "B"},
            ],
        )
        operations = Operations(MigrationContext.configure(connection))
        original_op = migration.op
        migration.op = operations
        try:
            migration.upgrade()
        finally:
            migration.op = original_op

        rows = connection.execute(
            sa.text("SELECT id, username, password, referral_code, referrer_id FROM app_user ORDER BY id")
        ).all()
        assert len(rows) == 2
        assert [row.username for row in rows] == ["legacy_a", "legacy_b"]
        assert [row.password for row in rows] == ["hash-a", "hash-b"]
        assert all(row.referral_code and len(row.referral_code) == 10 for row in rows)
        assert len({row.referral_code for row in rows}) == 2
        assert all(row.referrer_id is None for row in rows)
