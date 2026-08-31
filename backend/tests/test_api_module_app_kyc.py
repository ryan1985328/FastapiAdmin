"""Targeted App KYC submission and review flow tests."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    return body.get("data"), body


def app_user_token(test_client: TestClient, username: str) -> tuple[int, dict[str, str]]:
    password = "AppKyc123!"
    register = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": password, "nickname": "KYC Test User"},
    )
    assert register.status_code == 200, register.text
    user, _ = response_data(register)

    login = test_client.post(
        "/app/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    login_data, _ = response_data(login)
    return user["id"], {"Authorization": f"Bearer {login_data['access_token']}"}


def submission(front_user_id: int, *, name: str = "测试实名") -> dict[str, str]:
    return {
        "real_name": name,
        "id_card_no": "440305199001011234",
        "id_card_front": f"kyc/{front_user_id}/front.png",
        "id_card_back": f"kyc/{front_user_id}/back.png",
    }


def test_app_kyc_submit_review_resubmit_and_ownership(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    user_id, user_headers = app_user_token(test_client, f"kyc_{uuid4().hex[:12]}")

    with patch(
        "app.plugin.module_app.kyc.service.StorageFileService.exists",
        new=AsyncMock(return_value=True),
    ):
        first = test_client.post("/app/kyc/submit", headers=user_headers, json=submission(user_id))
        assert first.status_code == 200, first.text
        first_data, _ = response_data(first)
        assert first_data["status"] == 0
        kyc_id = first_data["id"]
        assert first_data["app_user_id"] == user_id

        duplicate = test_client.post("/app/kyc/submit", headers=user_headers, json=submission(user_id))
        assert duplicate.status_code != 200

        reject_without_remark = test_client.post(
            f"/system/kyc/review/{kyc_id}",
            headers=auth_headers,
            json={"status": 2, "review_remark": "   "},
        )
        assert reject_without_remark.status_code != 200

        reject = test_client.post(
            f"/system/kyc/review/{kyc_id}",
            headers=auth_headers,
            json={"status": 2, "review_remark": "请补充清晰证件图片"},
        )
        assert reject.status_code == 200, reject.text
        reject_data, _ = response_data(reject)
        assert reject_data["status"] == 2

        mine = test_client.get("/app/kyc/mine", headers=user_headers)
        assert mine.status_code == 200, mine.text
        mine_data, _ = response_data(mine)
        assert mine_data["id"] == kyc_id
        assert mine_data["review_remark"] == "请补充清晰证件图片"

        resubmit = test_client.post(
            "/app/kyc/resubmit",
            headers=user_headers,
            json=submission(user_id, name="测试实名修改"),
        )
        assert resubmit.status_code == 200, resubmit.text
        resubmit_data, _ = response_data(resubmit)
        assert resubmit_data["id"] == kyc_id
        assert resubmit_data["status"] == 0

        approve = test_client.post(
            f"/system/kyc/review/{kyc_id}",
            headers=auth_headers,
            json={"status": 1},
        )
        assert approve.status_code == 200, approve.text
        assert response_data(approve)[0]["status"] == 1

        locked = test_client.post(
            "/app/kyc/resubmit",
            headers=user_headers,
            json=submission(user_id, name="不应修改"),
        )
        assert locked.status_code != 200

        other_id, other_headers = app_user_token(test_client, f"kyc_other_{uuid4().hex[:10]}")
        assert test_client.get("/app/kyc/mine", headers=other_headers).json()["data"] is None
        spoof = test_client.post(
            "/app/kyc/submit",
            headers=other_headers,
            json=submission(user_id),
        )
        assert spoof.status_code != 200
        assert other_id != user_id
