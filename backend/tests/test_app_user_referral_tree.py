"""Targeted checks for the Admin Referral Tree relationship explorer."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.config.setting import settings
from app.core.database import async_db_session
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_system.kyc.model import AppUserKycModel


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


def register_user(test_client: TestClient, prefix: str, mobile: str) -> dict:
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": f"{prefix}_{uuid4().hex[:12]}",
            "password": "ReferralTree123!",
            "nickname": f"{prefix} nickname",
            "mobile": mobile,
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)


def bind_user(test_client: TestClient, auth_headers: dict[str, str], user: dict, referrer: dict) -> None:
    response = test_client.post(
        f"/system/app_user/referrer/bind/{user['id']}",
        headers=auth_headers,
        json={"referral_code": referrer["referral_code"]},
    )
    assert response.status_code == 200, response.text


async def add_pending_kyc(user_id: int) -> None:
    async with async_db_session() as db:
        db.add(
            AppUserKycModel(
                app_user_id=user_id,
                id_card_no=f"REFERRAL-{user_id}",
                status=0,
            )
        )
        await db.commit()


async def create_cycle(first_id: int, second_id: int) -> None:
    now = datetime.now(UTC)
    async with async_db_session() as db:
        await db.execute(
            update(AppUserModel)
            .where(AppUserModel.id == first_id)
            .values(referrer_id=second_id, referrer_bound_at=now)
        )
        await db.execute(
            update(AppUserModel)
            .where(AppUserModel.id == second_id)
            .values(referrer_id=first_id, referrer_bound_at=now)
        )
        await db.commit()


def test_referral_tree_search_summary_children_and_lazy_levels(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    original_methods = settings.OPERATION_RECORD_METHOD
    settings.OPERATION_RECORD_METHOD = []
    try:
        root = register_user(test_client, "referral_tree_root", "13921110001")
        child_a = register_user(test_client, "referral_tree_child_a", "13921110002")
        child_b = register_user(test_client, "referral_tree_child_b", "13921110003")
        grandchild = register_user(test_client, "referral_tree_grandchild", "13921110004")

        bind_user(test_client, auth_headers, child_a, root)
        bind_user(test_client, auth_headers, child_b, root)
        bind_user(test_client, auth_headers, grandchild, child_a)
        asyncio.run(add_pending_kyc(child_a["id"]))

        frozen = test_client.patch(
            f"/system/app_user/status/{child_b['id']}",
            headers=auth_headers,
            json={"action": "freeze"},
        )
        assert frozen.status_code == 200, frozen.text
        assert response_data(frozen)["status"] == 2

        for keyword in (
            str(root["id"]),
            root["username"],
            root["nickname"],
            root["mobile"],
            root["referral_code"],
        ):
            search = test_client.get(
                "/system/app_user/referral/search",
                headers=auth_headers,
                params={"keyword": keyword, "page_no": 1, "page_size": 20},
            )
            assert search.status_code == 200, search.text
            page = response_data(search)
            assert root["id"] in {item["user_id"] for item in page["items"]}
            assert page["items"][0]["mobile"] == "139****0001"

        multiple = test_client.get(
            "/system/app_user/referral/search",
            headers=auth_headers,
            params={"keyword": "referral_tree", "page_no": 1, "page_size": 100},
        )
        assert multiple.status_code == 200, multiple.text
        multiple_page = response_data(multiple)
        assert multiple_page["total"] >= 4
        assert {root["id"], child_a["id"], child_b["id"], grandchild["id"]} <= {
            item["user_id"] for item in multiple_page["items"]
        }

        root_summary_response = test_client.get(
            f"/system/app_user/referral/{root['id']}",
            headers=auth_headers,
        )
        assert root_summary_response.status_code == 200, root_summary_response.text
        root_summary = response_data(root_summary_response)
        assert root_summary["user_id"] == root["id"]
        assert root_summary["mobile"] == "139****0001"
        assert root_summary["referrer_id"] is None
        assert root_summary["referrer"] is None
        assert root_summary["direct_count"] == 2
        assert root_summary["total_descendant_count"] == 3
        assert root_summary["kyc_status"] == "unverified"

        child_summary_response = test_client.get(
            f"/system/app_user/referral/{child_a['id']}",
            headers=auth_headers,
        )
        assert child_summary_response.status_code == 200, child_summary_response.text
        child_summary = response_data(child_summary_response)
        assert child_summary["referrer_id"] == root["id"]
        assert child_summary["referrer"]["user_id"] == root["id"]
        assert child_summary["referrer"]["mobile"] == "139****0001"
        assert child_summary["referrer_bound_at"]
        assert child_summary["direct_count"] == 1
        assert child_summary["total_descendant_count"] == 1
        assert child_summary["kyc_status"] == "pending"

        first_children = test_client.get(
            f"/system/app_user/referral/{root['id']}/children",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 1},
        )
        assert first_children.status_code == 200, first_children.text
        first_page = response_data(first_children)
        assert first_page["total"] == 2
        assert first_page["has_next"] is True
        assert len(first_page["items"]) == 1

        second_children = test_client.get(
            f"/system/app_user/referral/{root['id']}/children",
            headers=auth_headers,
            params={"page_no": 2, "page_size": 1},
        )
        assert second_children.status_code == 200, second_children.text
        second_page = response_data(second_children)
        assert second_page["total"] == 2
        assert second_page["has_next"] is False
        assert len(second_page["items"]) == 1

        child_a_children = test_client.get(
            f"/system/app_user/referral/{child_a['id']}/children",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 50},
        )
        assert child_a_children.status_code == 200, child_a_children.text
        child_a_page = response_data(child_a_children)
        assert child_a_page["total"] == 1
        assert child_a_page["items"][0]["user_id"] == grandchild["id"]

        no_children = test_client.get(
            f"/system/app_user/referral/{child_b['id']}/children",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 50},
        )
        assert no_children.status_code == 200, no_children.text
        no_children_page = response_data(no_children)
        assert no_children_page["total"] == 0
        assert no_children_page["items"] == []
        assert no_children_page["has_next"] is False

        descendant_count = test_client.get(
            f"/system/app_user/referral/{root['id']}/descendant-count",
            headers=auth_headers,
        )
        assert descendant_count.status_code == 200, descendant_count.text
        assert response_data(descendant_count)["total_descendant_count"] == 3

        assert response_data(
            test_client.get(
                f"/system/app_user/referral/{child_b['id']}",
                headers=auth_headers,
            )
        )["status"] == 2
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods


def test_referral_tree_cycle_defense_and_runtime_menu_contract(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    original_methods = settings.OPERATION_RECORD_METHOD
    settings.OPERATION_RECORD_METHOD = []
    try:
        first = register_user(test_client, "referral_tree_cycle_first", "13921110101")
        second = register_user(test_client, "referral_tree_cycle_second", "13921110102")
        asyncio.run(create_cycle(first["id"], second["id"]))

        summary = test_client.get(
            f"/system/app_user/referral/{first['id']}",
            headers=auth_headers,
        )
        assert summary.status_code == 200, summary.text
        assert response_data(summary)["total_descendant_count"] == 1

        second_children = test_client.get(
            f"/system/app_user/referral/{second['id']}/children",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 50},
        )
        assert second_children.status_code == 200, second_children.text
        assert response_data(second_children)["items"][0]["user_id"] == first["id"]

        menu_tree = test_client.get("/system/menu/tree", headers=auth_headers)
        assert menu_tree.status_code == 200, menu_tree.text

        def walk(nodes: list[dict]) -> list[dict]:
            result: list[dict] = []
            for node in nodes:
                result.append(node)
                result.extend(walk(node.get("children") or []))
            return result

        menus = walk(response_data(menu_tree))
        referral_page = next(
            menu
            for menu in menus
            if menu.get("permission") == "module_system:app_user:referral"
            and menu.get("route_name") == "AppUserReferralTree"
        )
        assert referral_page["route_path"] == "referrals"
        assert referral_page["component_path"] == "module_system/app_user/referral"
    finally:
        settings.OPERATION_RECORD_METHOD = original_methods
