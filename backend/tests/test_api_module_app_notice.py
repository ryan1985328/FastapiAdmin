"""Public App Notice integration tests."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body.get("data")


def test_public_notice_list_detail_and_visibility(
    test_client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def skip_operation_log(_log_data: dict) -> None:
        return None

    monkeypatch.setattr("app.core.router_class._write_operation_log_async", skip_operation_log)
    suffix = uuid4().hex[:12]
    enabled_id = None
    disabled_id = None

    enabled_response = test_client.post(
        "/system/notice/create",
        headers=auth_headers,
        json={
            "notice_title": f"Public Notice {suffix}",
            "notice_type": "1",
            "notice_content": "This content is public.",
            "description": "Public summary",
            "status": 0,
        },
    )
    assert enabled_response.status_code == 200, enabled_response.text
    enabled_id = response_data(enabled_response)["id"]

    disabled_response = test_client.post(
        "/system/notice/create",
        headers=auth_headers,
        json={
            "notice_title": f"Disabled Notice {suffix}",
            "notice_type": "2",
            "notice_content": "This content must stay private.",
            "status": 1,
        },
    )
    assert disabled_response.status_code == 200, disabled_response.text
    disabled_id = response_data(disabled_response)["id"]

    try:
        list_response = test_client.get(
            "/app/notices",
            params={"page_no": 1, "page_size": 10},
        )
        assert list_response.status_code == 200, list_response.text
        page = response_data(list_response)
        assert page["total"] >= 1
        enabled_item = next(item for item in page["items"] if item["id"] == enabled_id)
        assert enabled_item["notice_title"] == f"Public Notice {suffix}"
        assert set(enabled_item) <= {"id", "notice_title", "notice_type", "description", "created_time"}
        assert all(item["id"] != disabled_id for item in page["items"])

        detail_response = test_client.get(f"/app/notices/{enabled_id}")
        assert detail_response.status_code == 200, detail_response.text
        detail = response_data(detail_response)
        assert detail["notice_content"] == "This content is public."
        assert set(detail) <= {
            "id",
            "notice_title",
            "notice_type",
            "description",
            "created_time",
            "notice_content",
        }

        disabled_detail_response = test_client.get(f"/app/notices/{disabled_id}")
        assert disabled_detail_response.status_code == 404, disabled_detail_response.text
        assert disabled_detail_response.json()["success"] is False
    finally:
        ids = [notice_id for notice_id in (enabled_id, disabled_id) if notice_id is not None]
        if ids:
            delete_response = test_client.request(
                "DELETE",
                "/system/notice/delete",
                headers=auth_headers,
                json=ids,
            )
            assert delete_response.status_code == 200, delete_response.text
