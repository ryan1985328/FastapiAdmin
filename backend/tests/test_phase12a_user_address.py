"""Phase 12A User Address Foundation regression tests."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config.setting import settings


@pytest.fixture(autouse=True)
def disable_operation_logging_for_phase12a():
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


def register_user(test_client: TestClient, prefix: str, mobile: str) -> dict:
    username = f"{prefix}_{uuid4().hex[:12]}"
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": username,
            "password": "Phase12A!123",
            "nickname": f"{prefix} nickname",
            "mobile": mobile,
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def app_user_headers(test_client: TestClient, username: str) -> dict[str, str]:
    response = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": "Phase12A!123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response_data(response)['access_token']}"}


def address_payload(name: str, suffix: str, *, is_default: bool = False) -> dict:
    return {
        "receiver_name": name,
        "receiver_mobile": f"138{suffix:0>8}",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "detail_address": f"科技园 {suffix} 号",
        "postal_code": "518000",
        "is_default": is_default,
    }


def create_address(test_client: TestClient, headers: dict[str, str], name: str, suffix: str, *, is_default=False) -> dict:
    response = test_client.post(
        "/app/user/addresses",
        headers=headers,
        json=address_payload(name, suffix, is_default=is_default),
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def test_default_address_lifecycle_and_app_crud(test_client: TestClient) -> None:
    user = register_user(test_client, "phase12a_lifecycle", "13812120001")
    headers = app_user_headers(test_client, user["username"])

    first = create_address(test_client, headers, "张三", "1001")
    assert first["is_default"] is True

    second = create_address(test_client, headers, "李四", "1002")
    third = create_address(test_client, headers, "王五", "1003", is_default=True)
    assert second["is_default"] is False
    assert third["is_default"] is True

    listed = response_data(test_client.get("/app/user/addresses", headers=headers))
    assert [item["id"] for item in listed][:3] == [third["id"], second["id"], first["id"]]
    assert sum(item["is_default"] for item in listed) == 1

    detail = test_client.get(f"/app/user/addresses/{second['id']}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert response_data(detail)["receiver_name"] == "李四"
    assert "user_id" not in response_data(detail)

    updated = test_client.put(
        f"/app/user/addresses/{second['id']}",
        headers=headers,
        json={"detail_address": "后海中心 2002 号"},
    )
    assert updated.status_code == 200, updated.text
    assert response_data(updated)["detail_address"] == "后海中心 2002 号"

    switched = test_client.put(f"/app/user/addresses/{second['id']}/default", headers=headers, json={})
    assert switched.status_code == 200, switched.text
    assert response_data(switched)["is_default"] is True
    listed = response_data(test_client.get("/app/user/addresses", headers=headers))
    assert sum(item["is_default"] for item in listed) == 1
    assert next(item for item in listed if item["id"] == second["id"])["is_default"] is True

    deleted_default = test_client.delete(f"/app/user/addresses/{second['id']}", headers=headers)
    assert deleted_default.status_code == 200, deleted_default.text
    listed = response_data(test_client.get("/app/user/addresses", headers=headers))
    assert all(item["id"] != second["id"] for item in listed)
    assert next(item for item in listed if item["id"] == first["id"])["is_default"] is True

    deleted_non_default = test_client.delete(f"/app/user/addresses/{third['id']}", headers=headers)
    assert deleted_non_default.status_code == 200, deleted_non_default.text
    listed = response_data(test_client.get("/app/user/addresses", headers=headers))
    assert [item["id"] for item in listed] == [first["id"]]
    assert listed[0]["is_default"] is True


def test_address_ownership_rejects_cross_user_read_edit_delete_and_spoofed_create(
    test_client: TestClient,
) -> None:
    owner = register_user(test_client, "phase12a_owner", "13812120002")
    other = register_user(test_client, "phase12a_other", "13812120003")
    owner_headers = app_user_headers(test_client, owner["username"])
    other_headers = app_user_headers(test_client, other["username"])
    owner_address = create_address(test_client, owner_headers, "归属用户", "2001")

    cross_read = test_client.get(f"/app/user/addresses/{owner_address['id']}", headers=other_headers)
    assert cross_read.status_code == 404, cross_read.text

    cross_edit = test_client.put(
        f"/app/user/addresses/{owner_address['id']}",
        headers=other_headers,
        json={"receiver_name": "越权修改"},
    )
    assert cross_edit.status_code == 404, cross_edit.text

    cross_delete = test_client.delete(f"/app/user/addresses/{owner_address['id']}", headers=other_headers)
    assert cross_delete.status_code == 404, cross_delete.text

    cross_default = test_client.put(f"/app/user/addresses/{owner_address['id']}/default", headers=other_headers, json={})
    assert cross_default.status_code == 404, cross_default.text

    spoofed = test_client.post(
        "/app/user/addresses",
        headers=other_headers,
        json={**address_payload("伪造归属", "2002"), "user_id": owner["id"]},
    )
    assert spoofed.status_code == 422, spoofed.text

    owner_detail = test_client.get(f"/app/user/addresses/{owner_address['id']}", headers=owner_headers)
    assert owner_detail.status_code == 200, owner_detail.text
    assert response_data(owner_detail)["receiver_name"] == "归属用户"


def test_admin_address_query_detail_and_default_filter(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    user = register_user(test_client, "phase12a_admin", "13812120004")
    app_headers = app_user_headers(test_client, user["username"])
    address = create_address(test_client, app_headers, "管理员查询", "3001")

    by_keyword = test_client.get(
        "/system/app_user_address/list",
        headers=auth_headers,
        params={
            "page_no": 1,
            "page_size": 10,
            "keyword": user["username"],
            "created_time": ["2000-01-01 00:00:00", "2100-01-01 00:00:00"],
        },
    )
    assert by_keyword.status_code == 200, by_keyword.text
    page = response_data(by_keyword)
    assert page["total"] == 1
    row = page["items"][0]
    assert row["app_user"]["username"] == user["username"]
    assert row["app_user"]["mobile"] == user["mobile"]
    assert row["receiver_name"] == "管理员查询"
    assert row["user_id"] == user["id"]

    by_id = test_client.get(
        "/system/app_user_address/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 10, "keyword": str(user["id"])},
    )
    assert by_id.status_code == 200, by_id.text
    assert any(item["user_id"] == user["id"] for item in response_data(by_id)["items"])

    default_only = test_client.get(
        "/system/app_user_address/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 10, "is_default": "true"},
    )
    assert default_only.status_code == 200, default_only.text
    assert response_data(default_only)["total"] >= 1
    assert all(item["is_default"] is True for item in response_data(default_only)["items"])

    detail = test_client.get(f"/system/app_user_address/detail/{address['id']}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    detail_data = response_data(detail)
    assert detail_data["app_user"]["nickname"] == user["nickname"]
    assert detail_data["province"] == "广东省"
    assert detail_data["created_time"]
