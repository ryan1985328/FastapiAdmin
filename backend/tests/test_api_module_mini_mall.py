"""Focused Mini Mall V1 vertical-slice contract tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest

PRODUCT_PATH = "/product/product"


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body["data"]


@pytest.fixture(autouse=True)
def skip_audit_writes(monkeypatch: pytest.MonkeyPatch):
    async def skip_operation_log(_log_data: dict) -> None:
        return None

    monkeypatch.setattr("app.core.router_class._write_operation_log_async", skip_operation_log)
    monkeypatch.setattr("app.api.v1.module_system.auth.service._write_login_log", skip_operation_log)


def register_and_login(test_client, label: str) -> tuple[int, dict[str, str]]:
    username = f"mall_{label}_{uuid4().hex[:10]}"
    password = "MallUser123!"
    registered = test_client.post(
        "/app/auth/register",
        json={"username": username, "password": password, "nickname": f"Mall {label}"},
    )
    assert registered.status_code == 200, registered.text
    user_id = response_data(registered)["id"]
    login = test_client.post("/app/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    token = response_data(login)["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def create_product(test_client, auth_headers, *, name: str, price: str, stock: int, status: int | None = None, image_url: str | None = None):
    payload = {
        "name": name,
        "code": f"mall-{uuid4().hex[:14]}",
        "price": price,
        "stock": stock,
        "description": "plain product description\nsecond line",
        "sort": 1,
    }
    if status is not None:
        payload["status"] = status
    if image_url is not None:
        payload["image_url"] = image_url
    created = test_client.post(f"{PRODUCT_PATH}/create", headers=auth_headers, json=payload)
    assert created.status_code == 200, created.text
    return response_data(created)


def test_public_product_projection_and_default_off_sale(test_client, auth_headers):
    product = create_product(
        test_client,
        auth_headers,
        name="Mall Public Product",
        price="12.50",
        stock=3,
        image_url="https://cdn.example.test/mall.png",
    )
    assert product["status"] == 1

    hidden = test_client.get("/app/product/list", params={"page_no": 1, "page_size": 50})
    assert hidden.status_code == 200, hidden.text
    assert all(item["id"] != product["id"] for item in response_data(hidden)["items"])

    on_sale = test_client.patch(
        f"{PRODUCT_PATH}/status/batch",
        headers=auth_headers,
        json={"ids": [product["id"]], "status": 0},
    )
    assert on_sale.status_code == 200, on_sale.text

    listed = test_client.get("/app/product/list", params={"page_no": 1, "page_size": 50})
    assert listed.status_code == 200, listed.text
    item = next(row for row in response_data(listed)["items"] if row["id"] == product["id"])
    assert item["cover_url"] == "https://cdn.example.test/mall.png"
    assert item["price"] in {"12.50", 12.5}
    assert "code" not in item
    assert "remark" not in item
    assert "status" not in item

    detail = test_client.get(f"/app/product/{product['id']}")
    assert detail.status_code == 200, detail.text
    detail_data = response_data(detail)
    assert detail_data["description"].startswith("plain product description")
    assert "code" not in detail_data
    assert "is_deleted" not in detail_data

    deleted = test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product["id"]])
    assert deleted.status_code == 200, deleted.text


def test_local_storage_cover_is_browser_readable(test_client, auth_headers, tmp_path: Path):
    source = test_client.post(
        "/storage/source/create",
        headers=auth_headers,
        json={
            "name": f"mall-local-{uuid4().hex[:8]}",
            "protocol": "local",
            "host": str(tmp_path),
            "port": 0,
            "is_default": True,
            "status": 0,
        },
    )
    assert source.status_code == 200, source.text
    source_id = response_data(source)["id"]
    product_id = None
    uploaded_path = None
    try:
        uploaded = test_client.post(
            "/storage/file/upload",
            headers=auth_headers,
            files={"file": ("mall.png", b"mall-cover", "image/png")},
            data={"source_id": str(source_id)},
        )
        assert uploaded.status_code == 200, uploaded.text
        uploaded_path = response_data(uploaded)["file_path"]
        product = create_product(
            test_client,
            auth_headers,
            name="Mall Local Cover",
            price="1.00",
            stock=1,
            status=0,
            image_url=uploaded_path,
        )
        product_id = product["id"]
        detail = test_client.get(f"/app/product/{product_id}")
        assert detail.status_code == 200, detail.text
        assert response_data(detail)["cover_url"].endswith(f"/app/product/{product_id}/cover")
        assert "/api/v1/api/v1/" not in response_data(detail)["cover_url"]
        cover = test_client.get(f"/app/product/{product_id}/cover")
        assert cover.status_code == 200, cover.text
        assert cover.content == b"mall-cover"
        assert "module_storage" not in str(cover.url)
    finally:
        if product_id is not None:
            test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product_id])
        if uploaded_path:
            test_client.request(
                "DELETE",
                "/storage/file/delete",
                headers=auth_headers,
                json={"source_id": source_id, "remote_path": uploaded_path},
            )
        test_client.request("DELETE", "/storage/source/delete", headers=auth_headers, json=[source_id])


def test_order_server_snapshot_ownership_payment_idempotency_and_cancel(test_client, auth_headers):
    product = create_product(
        test_client,
        auth_headers,
        name="Mall Order Product",
        price="10.00",
        stock=2,
        status=0,
        image_url="https://cdn.example.test/order.png",
    )
    first_user_id, first_headers = register_and_login(test_client, "first")
    _second_user_id, second_headers = register_and_login(test_client, "second")

    rejected_client_fields = test_client.post(
        "/app/order",
        headers=first_headers,
        json={"product_id": product["id"], "quantity": 1, "user_id": 999, "total_amount": "0.01", "status": "PAID"},
    )
    assert rejected_client_fields.status_code == 422, rejected_client_fields.text

    created = test_client.post(
        "/app/order",
        headers=first_headers,
        json={"product_id": product["id"], "quantity": 2},
    )
    assert created.status_code == 200, created.text
    order = response_data(created)
    assert order["status"] == "PENDING_PAYMENT"
    assert order["total_amount"] in {"20.00", 20.0}
    assert order["items"][0]["product_name"] == "Mall Order Product"

    updated_product = test_client.put(
        f"{PRODUCT_PATH}/update/{product['id']}",
        headers=auth_headers,
        json={"name": "Mall Renamed", "price": "99.00"},
    )
    assert updated_product.status_code == 200, updated_product.text
    order_detail = test_client.get(f"/app/order/{order['id']}", headers=first_headers)
    assert order_detail.status_code == 200, order_detail.text
    snapshot = response_data(order_detail)
    assert snapshot["items"][0]["product_name"] == "Mall Order Product"
    assert snapshot["items"][0]["unit_price"] in {"10.00", 10.0}
    assert snapshot["total_amount"] in {"20.00", 20.0}

    cross_user = test_client.get(f"/app/order/{order['id']}", headers=second_headers)
    assert cross_user.status_code == 404, cross_user.text
    cross_pay = test_client.post(f"/app/order/{order['id']}/pay", headers=second_headers, json={})
    assert cross_pay.status_code == 404, cross_pay.text

    paid = test_client.post(f"/app/order/{order['id']}/pay", headers=first_headers, json={})
    assert paid.status_code == 200, paid.text
    assert response_data(paid)["status"] == "PAID"
    repeat_paid = test_client.post(f"/app/order/{order['id']}/pay", headers=first_headers, json={})
    assert repeat_paid.status_code == 200, repeat_paid.text
    assert response_data(repeat_paid)["status"] == "PAID"

    product_after_pay = test_client.get(f"{PRODUCT_PATH}/detail/{product['id']}", headers=auth_headers)
    assert response_data(product_after_pay)["stock"] == 0
    paid_cancel = test_client.post(f"/app/order/{order['id']}/cancel", headers=first_headers, json={})
    assert paid_cancel.status_code == 409, paid_cancel.text

    pending = test_client.post(
        "/app/order",
        headers=first_headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert pending.status_code == 200, pending.text
    pending_id = response_data(pending)["id"]
    cancelled = test_client.post(f"/app/order/{pending_id}/cancel", headers=first_headers, json={})
    assert cancelled.status_code == 200, cancelled.text
    assert response_data(cancelled)["status"] == "CANCELLED"
    repeated_cancel = test_client.post(f"/app/order/{pending_id}/cancel", headers=first_headers, json={})
    assert repeated_cancel.status_code == 200, repeated_cancel.text

    admin_orders = test_client.get(
        "/product/order/list",
        headers=auth_headers,
        params={"page_no": 1, "page_size": 20, "keyword": order["order_no"]},
    )
    assert admin_orders.status_code == 200, admin_orders.text
    assert response_data(admin_orders)["items"][0]["order_no"] == order["order_no"]
    admin_detail = test_client.get(f"/product/order/detail/{order['id']}", headers=auth_headers)
    assert admin_detail.status_code == 200, admin_detail.text
    assert response_data(admin_detail)["items"][0]["product_name"] == "Mall Order Product"

    blocked_delete = test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product["id"]])
    assert blocked_delete.status_code == 409, blocked_delete.text


def test_order_rejects_off_sale_and_payment_failure_keeps_stock(test_client, auth_headers):
    user_id, user_headers = register_and_login(test_client, "failure")
    del user_id
    product = create_product(
        test_client,
        auth_headers,
        name="Mall Atomic Failure Product",
        price="7.25",
        stock=1,
        status=0,
    )
    pending = test_client.post(
        "/app/order",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 2},
    )
    assert pending.status_code == 200, pending.text
    order_id = response_data(pending)["id"]

    insufficient = test_client.post(f"/app/order/{order_id}/pay", headers=user_headers, json={})
    assert insufficient.status_code == 409, insufficient.text
    product_after_failure = test_client.get(f"{PRODUCT_PATH}/detail/{product['id']}", headers=auth_headers)
    assert product_after_failure.status_code == 200, product_after_failure.text
    assert response_data(product_after_failure)["stock"] == 1
    pending_detail = test_client.get(f"/app/order/{order_id}", headers=user_headers)
    assert response_data(pending_detail)["status"] == "PENDING_PAYMENT"

    off_sale = create_product(
        test_client,
        auth_headers,
        name="Mall Off Sale Product",
        price="3.00",
        stock=5,
        status=1,
    )
    rejected = test_client.post(
        "/app/order",
        headers=user_headers,
        json={"product_id": off_sale["id"], "quantity": 1},
    )
    assert rejected.status_code == 409, rejected.text


def test_concurrent_payment_consumes_stock_once(test_client, auth_headers):
    _user_id, user_headers = register_and_login(test_client, "concurrent")
    product = create_product(
        test_client,
        auth_headers,
        name="Mall Concurrent Payment Product",
        price="2.50",
        stock=1,
        status=0,
    )
    created = test_client.post(
        "/app/order",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert created.status_code == 200, created.text
    order_id = response_data(created)["id"]

    def pay_once():
        return test_client.post(f"/app/order/{order_id}/pay", headers=user_headers, json={})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: pay_once(), range(2)))

    assert all(response.status_code in {200, 409} for response in responses), [response.text for response in responses]
    successful_payments = [response for response in responses if response.status_code == 200]
    assert successful_payments
    assert all(response_data(response)["status"] == "PAID" for response in successful_payments)
    product_after_payment = test_client.get(f"{PRODUCT_PATH}/detail/{product['id']}", headers=auth_headers)
    assert response_data(product_after_payment)["stock"] == 0


def test_cancelled_order_allows_product_soft_delete(test_client, auth_headers):
    _user_id, user_headers = register_and_login(test_client, "delete")
    product = create_product(
        test_client,
        auth_headers,
        name="Mall Cancelled Reference Product",
        price="4.00",
        stock=1,
        status=0,
    )
    created = test_client.post(
        "/app/order",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    assert created.status_code == 200, created.text
    order_id = response_data(created)["id"]
    cancelled = test_client.post(f"/app/order/{order_id}/cancel", headers=user_headers, json={})
    assert cancelled.status_code == 200, cancelled.text
    assert response_data(cancelled)["status"] == "CANCELLED"

    deleted = test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product["id"]])
    assert deleted.status_code == 200, deleted.text
    order_detail = test_client.get(f"/app/order/{order_id}", headers=user_headers)
    assert order_detail.status_code == 200, order_detail.text
    assert response_data(order_detail)["items"][0]["product_id"] == product["id"]
