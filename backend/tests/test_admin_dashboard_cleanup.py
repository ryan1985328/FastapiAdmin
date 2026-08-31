"""Focused checks for the real data used by the Admin home dashboard."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def test_dashboard_business_user_metric_uses_app_users(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """The home card's business-user total must come from the App User list."""
    username = f"dashboard_{uuid4().hex[:12]}"
    register = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": "Dashboard123!", "nickname": "Dashboard User"},
    )
    assert register.status_code == 200, register.text

    listed = test_client.get(
        "/system/app_user/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 1},
    )
    assert listed.status_code == 200, listed.text

    with patch(
        "app.api.v1.module_monitor.online.service.OnlineService.get_online_list",
        new=AsyncMock(return_value=[]),
    ):
        stats = test_client.get("/monitor/online/stats", headers=auth_headers)
    assert stats.status_code == 200, stats.text
    assert response_data(stats)["total_users"] == response_data(listed)["total"]
