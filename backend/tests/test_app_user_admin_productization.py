"""Focused checks for the App User Admin presentation/query foundation."""

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def register_user(test_client: TestClient, prefix: str, mobile: str) -> dict:
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": f"{prefix}_{uuid4().hex[:12]}",
            "password": "Phase11C123!",
            "nickname": f"{prefix} nickname",
            "mobile": mobile,
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def test_admin_app_user_keyword_and_business_filters(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    referrer = register_user(test_client, "phase11c_referrer", "13821110001")
    child = register_user(test_client, "phase11c_child", "13821110002")

    bind = test_client.post(
        f"/system/app_user/referrer/bind/{child['id']}",
        headers=auth_headers,
        json={"referral_code": referrer["referral_code"]},
    )
    assert bind.status_code == 200, bind.text

    for keyword in (
        str(child["id"]),
        child["username"],
        child["mobile"],
        child["nickname"],
        child["referral_code"],
    ):
        response = test_client.get(
            "/system/app_user/list",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 100, "keyword": keyword},
        )
        assert response.status_code == 200, response.text
        assert child["id"] in {item["id"] for item in response_data(response)["items"]}

    bound = test_client.get(
        "/system/app_user/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 100, "has_referrer": "true"},
    )
    assert bound.status_code == 200, bound.text
    assert child["id"] in {item["id"] for item in response_data(bound)["items"]}

    unbound = test_client.get(
        "/system/app_user/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 100, "has_referrer": "false"},
    )
    assert unbound.status_code == 200, unbound.text
    assert referrer["id"] in {item["id"] for item in response_data(unbound)["items"]}

    created = datetime.fromisoformat(child["created_time"].replace("Z", "+00:00"))
    date_range = test_client.get(
        "/system/app_user/list",
        headers=auth_headers,
        params=[
            ("page_no", "1"),
            ("page_size", "100"),
            ("created_time", (created - timedelta(minutes=1)).isoformat()),
            ("created_time", (created + timedelta(minutes=1)).isoformat()),
            ("status", "0"),
            ("kyc_status", "unverified"),
        ],
    )
    assert date_range.status_code == 200, date_range.text
    assert child["id"] in {item["id"] for item in response_data(date_range)["items"]}


def test_app_user_admin_dictionaries_are_seeded(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    expected = {
        "app_user_status": {"0": "正常", "1": "禁用", "2": "冻结"},
        "app_user_kyc_status": {
            "unverified": "未实名",
            "pending": "待审核",
            "verified": "已实名",
            "rejected": "已驳回",
        },
    }

    for dict_type, expected_entries in expected.items():
        response = test_client.get(
            f"/system/dict/data/info/{dict_type}",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        actual = {item["dict_value"]: item["dict_label"] for item in response_data(response)}
        assert actual == expected_entries
