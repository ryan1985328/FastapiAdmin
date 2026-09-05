"""Focused contracts for Admin default list ordering."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, update

from app.api.v1.module_monitor.resource.schema import ResourceItemSchema
from app.api.v1.module_monitor.resource.service import ResourceService
from app.api.v1.module_storage.core.base import StorageObject
from app.api.v1.module_storage.file.service import StorageFileService
from app.api.v1.module_system.dict.service import DictDataService
from app.api.v1.module_system.log.model import LoginLogModel
from app.core.base_schema import PaginationQueryParam
from app.core.database import async_db_session
from app.plugin.module_app.user.model import AppUserModel
from app.plugin.module_product.order.model import ProductOrderItemModel, ProductOrderModel
from app.plugin.module_product.product.model import ProductModel


def _response_data(response) -> Any:
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


@pytest.fixture(autouse=True)
def _skip_audit_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    async def skip_operation_log(_log_data: dict) -> None:
        return None

    monkeypatch.setattr("app.core.router_class._write_operation_log_async", skip_operation_log)
    monkeypatch.setattr("app.api.v1.module_system.auth.service._write_login_log", skip_operation_log)


async def _set_created_times(model: Any, values: dict[int, datetime]) -> None:
    async with async_db_session() as db:
        for record_id, created_time in values.items():
            await db.execute(update(model).where(model.id == record_id).values(created_time=created_time))
        await db.commit()


async def _delete_app_users(ids: list[int]) -> None:
    async with async_db_session() as db:
        await db.execute(delete(AppUserModel).where(AppUserModel.id.in_(ids)))
        await db.commit()


async def _delete_products(ids: list[int]) -> None:
    async with async_db_session() as db:
        await db.execute(delete(ProductModel).where(ProductModel.id.in_(ids)))
        await db.commit()


async def _delete_order_fixture(user_id: int, product_id: int, order_ids: list[int]) -> None:
    async with async_db_session() as db:
        await db.execute(delete(ProductOrderItemModel).where(ProductOrderItemModel.order_id.in_(order_ids)))
        await db.execute(delete(ProductOrderModel).where(ProductOrderModel.id.in_(order_ids)))
        await db.execute(delete(ProductModel).where(ProductModel.id == product_id))
        await db.execute(delete(AppUserModel).where(AppUserModel.id == user_id))
        await db.commit()


async def _create_login_logs(prefix: str, timestamps: list[datetime]) -> list[int]:
    async with async_db_session() as db:
        rows = [
            LoginLogModel(
                username=f"{prefix}_{index}",
                status=1,
                msg="ordering contract",
                created_time=created_time,
            )
            for index, created_time in enumerate(timestamps, start=1)
        ]
        db.add_all(rows)
        await db.flush()
        ids = [row.id for row in rows]
        await db.commit()
        return ids


async def _delete_login_logs(ids: list[int]) -> None:
    async with async_db_session() as db:
        await db.execute(delete(LoginLogModel).where(LoginLogModel.id.in_(ids)))
        await db.commit()


def _register_app_user(test_client: TestClient, prefix: str, index: int) -> dict:
    response = test_client.post(
        "/app/auth/register",
        json={
            "username": f"{prefix}_{index}",
            "password": "Ordering123!",
            "nickname": f"Ordering user {index}",
        },
    )
    assert response.status_code == 200, response.text
    return _response_data(response)


def _create_product(
    test_client: TestClient,
    auth_headers: dict[str, str],
    *,
    prefix: str,
    index: int,
    sort: int,
    status: int = 1,
) -> dict:
    response = test_client.post(
        "/product/product/create",
        headers=auth_headers,
        json={
            "name": f"{prefix} product {index}",
            "code": f"{prefix}-{index}",
            "price": "10.00",
            "stock": 100,
            "status": status,
            "sort": sort,
        },
    )
    assert response.status_code == 200, response.text
    return _response_data(response)


def test_pagination_omission_is_service_owned_and_explicit_sort_is_preserved() -> None:
    assert PaginationQueryParam().order_by is None
    assert PaginationQueryParam(order_by='[{"id":"asc"}]').order_by == [{"id": "asc"}]
    assert PaginationQueryParam(order_by='[{"created_time":"desc"},{"id":"desc"}]').order_by == [
        {"created_time": "desc"},
        {"id": "desc"},
    ]


def test_configured_and_file_list_defaults_are_stable() -> None:
    assert DictDataService._default_order() == [
        {"dict_sort": "asc"},
        {"created_time": "desc"},
        {"id": "desc"},
    ]

    older = datetime(2025, 1, 1, 8, 0, tzinfo=UTC)
    newer = older + timedelta(days=1)
    objects = [
        StorageObject(name="old.txt", key="old.txt", modified_time=older),
        StorageObject(name="new.txt", key="new.txt", modified_time=newer),
        StorageObject(name="folder", key="folder", is_dir=True, modified_time=older),
    ]
    assert [item.key for item in StorageFileService._sort_objects(objects)] == [
        "folder",
        "new.txt",
        "old.txt",
    ]

    resources = [
        ResourceItemSchema(
            name=item.name,
            file_url=f"/{item.key}",
            relative_path=item.key,
            is_file=not item.is_dir,
            is_dir=item.is_dir,
            modified_time=item.modified_time,
        )
        for item in objects
    ]
    assert [item.relative_path for item in ResourceService._sort_results(resources)] == [
        "folder",
        "new.txt",
        "old.txt",
    ]


def test_app_user_recency_tie_pagination_and_explicit_override(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    prefix = f"ordering_user_{uuid4().hex[:10]}"
    users: list[dict] = []
    try:
        users = [_register_app_user(test_client, prefix, index) for index in range(1, 4)]
        older = datetime(2025, 1, 1, 8, 0, tzinfo=UTC)
        newer = older + timedelta(days=1)
        asyncio.run(
            _set_created_times(
                AppUserModel,
                {
                    users[0]["id"]: older,
                    users[1]["id"]: newer,
                    users[2]["id"]: newer,
                },
            )
        )

        first_page = _response_data(
            test_client.get(
                "/system/app_user/list",
                headers=auth_headers,
                params={"keyword": prefix, "page_no": 1, "page_size": 2},
            )
        )
        second_page = _response_data(
            test_client.get(
                "/system/app_user/list",
                headers=auth_headers,
                params={"keyword": prefix, "page_no": 2, "page_size": 2},
            )
        )
        assert [item["id"] for item in first_page["items"]] == [users[2]["id"], users[1]["id"]]
        assert [item["id"] for item in second_page["items"]] == [users[0]["id"]]
        assert first_page["has_next"] is True
        assert second_page["has_next"] is False

        ascending = _response_data(
            test_client.get(
                "/system/app_user/list",
                headers=auth_headers,
                params={
                    "keyword": prefix,
                    "page_no": 1,
                    "page_size": 10,
                    "order_by": json.dumps([{"id": "asc"}]),
                },
            )
        )
        assert [item["id"] for item in ascending["items"]] == [user["id"] for user in users]
    finally:
        if users:
            asyncio.run(_delete_app_users([user["id"] for user in users]))


def test_product_manual_sort_then_recency_and_id_with_explicit_override(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    prefix = f"ordering_product_{uuid4().hex[:8]}"
    products: list[dict] = []
    try:
        products = [
            _create_product(test_client, auth_headers, prefix=prefix, index=1, sort=20),
            _create_product(test_client, auth_headers, prefix=prefix, index=2, sort=10),
            _create_product(test_client, auth_headers, prefix=prefix, index=3, sort=10),
        ]
        older = datetime(2025, 2, 1, 8, 0, tzinfo=UTC)
        newer = older + timedelta(days=1)
        asyncio.run(
            _set_created_times(
                ProductModel,
                {
                    products[0]["id"]: newer + timedelta(days=1),
                    products[1]["id"]: newer,
                    products[2]["id"]: newer,
                },
            )
        )

        default_page = _response_data(
            test_client.get(
                "/product/product/list",
                headers=auth_headers,
                params={"name": prefix, "page_no": 1, "page_size": 10},
            )
        )
        assert [item["id"] for item in default_page["items"]] == [
            products[2]["id"],
            products[1]["id"],
            products[0]["id"],
        ]

        ascending = _response_data(
            test_client.get(
                "/product/product/list",
                headers=auth_headers,
                params={
                    "name": prefix,
                    "page_no": 1,
                    "page_size": 10,
                    "order_by": json.dumps([{"id": "asc"}]),
                },
            )
        )
        assert [item["id"] for item in ascending["items"]] == [product["id"] for product in products]
    finally:
        if products:
            asyncio.run(_delete_products([product["id"] for product in products]))


def test_product_order_default_is_newest_first_and_deterministic(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    prefix = f"ordering_order_{uuid4().hex[:8]}"
    user = _register_app_user(test_client, prefix, 1)
    product = _create_product(test_client, auth_headers, prefix=prefix, index=1, sort=1, status=0)
    orders: list[dict] = []
    try:
        login = test_client.post(
            "/app/auth/login",
            json={"username": f"{prefix}_1", "password": "Ordering123!"},
        )
        assert login.status_code == 200, login.text
        app_headers = {"Authorization": f"Bearer {_response_data(login)['access_token']}"}

        for _ in range(3):
            response = test_client.post(
                "/app/order",
                headers=app_headers,
                json={"product_id": product["id"], "quantity": 1},
            )
            assert response.status_code == 200, response.text
            orders.append(_response_data(response))

        older = datetime(2025, 3, 1, 8, 0, tzinfo=UTC)
        newer = older + timedelta(days=1)
        asyncio.run(
            _set_created_times(
                ProductOrderModel,
                {
                    orders[0]["id"]: older,
                    orders[1]["id"]: newer,
                    orders[2]["id"]: newer,
                },
            )
        )

        page = _response_data(
            test_client.get(
                "/product/order/list",
                headers=auth_headers,
                params={"user_id": user["id"], "page_no": 1, "page_size": 10},
            )
        )
        assert [item["id"] for item in page["items"]] == [
            orders[2]["id"],
            orders[1]["id"],
            orders[0]["id"],
        ]
    finally:
        asyncio.run(_delete_order_fixture(user["id"], product["id"], [order["id"] for order in orders]))


def test_login_log_default_is_newest_first_and_deterministic(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    prefix = f"ordering_log_{uuid4().hex[:10]}"
    older = datetime(2025, 4, 1, 8, 0, tzinfo=UTC)
    newer = older + timedelta(days=1)
    ids = asyncio.run(_create_login_logs(prefix, [older, newer, newer]))
    try:
        page = _response_data(
            test_client.get(
                "/system/log/login/list",
                headers=auth_headers,
                params={"username": prefix, "page_no": 1, "page_size": 10},
            )
        )
        assert [item["id"] for item in page["items"]] == [ids[2], ids[1], ids[0]]
    finally:
        asyncio.run(_delete_login_logs(ids))


def test_menu_tree_keeps_business_order(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = test_client.get("/system/menu/tree", headers=auth_headers)
    assert response.status_code == 200, response.text

    def assert_sibling_order(nodes: list[dict]) -> None:
        orders = [node["order"] for node in nodes]
        assert orders == sorted(orders)
        for node in nodes:
            assert_sibling_order(node.get("children") or [])

    assert_sibling_order(_response_data(response))
