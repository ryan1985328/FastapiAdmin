"""Product reference module API and Storage integration tests."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

PRODUCT_PATH = "/product/product"


def response_data(response):
    body = response.json()
    assert body.get("success") is True, body
    return body.get("data")


def walk_menu(nodes):
    for node in nodes:
        yield node
        yield from walk_menu(node.get("children") or [])


def test_product_menu_and_openapi(test_client: TestClient, auth_headers: dict[str, str]) -> None:
    openapi = test_client.get("/openapi.json")
    assert openapi.status_code == 200
    assert f"{PRODUCT_PATH}/list" in openapi.json()["paths"]
    assert f"{PRODUCT_PATH}/status/batch" in openapi.json()["paths"]

    menu_response = test_client.get("/system/menu/tree", headers=auth_headers)
    assert menu_response.status_code == 200, menu_response.text
    menus = response_data(menu_response)
    product_nodes = list(walk_menu(menus))
    product_menu = next(node for node in product_nodes if node.get("route_name") == "Product")
    assert product_menu["component_path"] == "module_product/product/index"
    product_permissions = {
        node.get("permission")
        for node in product_menu.get("children") or []
        if node.get("permission")
    }
    assert "module_product:product:create" in product_permissions
    assert "module_product:product:patch" in product_permissions


def test_product_crud_and_storage_reference(
    test_client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def skip_operation_log(_log_data: dict) -> None:
        return None

    monkeypatch.setattr("app.core.router_class._write_operation_log_async", skip_operation_log)
    code = f"phase4-{uuid4().hex[:12]}"
    product_id = None
    source_id = None
    uploaded_path = None

    invalid = test_client.post(
        f"{PRODUCT_PATH}/create",
        headers=auth_headers,
        json={"code": code},
    )
    assert invalid.status_code == 422

    source_response = test_client.post(
        "/storage/source/create",
        headers=auth_headers,
        json={
            "name": f"phase4-local-{uuid4().hex[:8]}",
            "protocol": "local",
            "host": str(tmp_path),
            "port": 0,
            "is_default": True,
            "status": 0,
        },
    )
    assert source_response.status_code == 200, source_response.text
    source_id = response_data(source_response)["id"]

    try:
        upload_response = test_client.post(
            "/storage/file/upload",
            headers=auth_headers,
            files={"file": ("product.png", b"phase4-product-image", "image/png")},
            data={"source_id": str(source_id)},
        )
        assert upload_response.status_code == 200, upload_response.text
        upload = response_data(upload_response)
        uploaded_path = upload["file_path"]
        assert uploaded_path
        assert (tmp_path / uploaded_path).is_file()

        create_response = test_client.post(
            f"{PRODUCT_PATH}/create",
            headers=auth_headers,
            json={
                "name": "Phase 4 Reference Product",
                "code": code,
                "description": "Generator-backed reference record",
                "image_url": uploaded_path,
                "price": "12.50",
                "stock": 8,
                "status": 0,
                "sort": 10,
                "remark": "test-only",
            },
        )
        assert create_response.status_code == 200, create_response.text
        created = response_data(create_response)
        product_id = created["id"]
        assert created["code"] == code
        assert created["price"] in {"12.50", 12.5}
        assert created["image_url"] == uploaded_path

        duplicate_response = test_client.post(
            f"{PRODUCT_PATH}/create",
            headers=auth_headers,
            json={"name": "Duplicate", "code": code},
        )
        assert duplicate_response.status_code == 500
        assert duplicate_response.json()["success"] is False

        list_response = test_client.get(
            f"{PRODUCT_PATH}/list",
            headers=auth_headers,
            params={"page_no": 1, "page_size": 10, "name": "Reference", "code": code},
        )
        assert list_response.status_code == 200, list_response.text
        page = response_data(list_response)
        assert page["total"] == 1
        assert page["items"][0]["id"] == product_id

        detail_response = test_client.get(f"{PRODUCT_PATH}/detail/{product_id}", headers=auth_headers)
        assert detail_response.status_code == 200, detail_response.text
        assert response_data(detail_response)["stock"] == 8

        update_response = test_client.put(
            f"{PRODUCT_PATH}/update/{product_id}",
            headers=auth_headers,
            json={"name": "Updated Reference Product", "price": "18.75", "stock": 13},
        )
        assert update_response.status_code == 200, update_response.text
        updated = response_data(update_response)
        assert updated["name"] == "Updated Reference Product"
        assert updated["price"] in {"18.75", 18.75}
        assert updated["code"] == code

        status_response = test_client.patch(
            f"{PRODUCT_PATH}/status/batch",
            headers=auth_headers,
            json={"ids": [product_id], "status": 1},
        )
        assert status_response.status_code == 200, status_response.text
        assert response_data(test_client.get(f"{PRODUCT_PATH}/detail/{product_id}", headers=auth_headers))["status"] == 1

        delete_response = test_client.request(
            "DELETE",
            f"{PRODUCT_PATH}/delete",
            headers=auth_headers,
            json=[product_id],
        )
        assert delete_response.status_code == 200, delete_response.text
        product_id = None
        deleted_detail = test_client.get(f"{PRODUCT_PATH}/detail/{product_id or created['id']}", headers=auth_headers)
        assert deleted_detail.status_code == 500
        assert deleted_detail.json()["success"] is False
    finally:
        if product_id is not None:
            test_client.request(
                "DELETE",
                f"{PRODUCT_PATH}/delete",
                headers=auth_headers,
                json=[product_id],
            )
        if uploaded_path:
            test_client.request(
                "DELETE",
                "/storage/file/delete",
                headers=auth_headers,
                json={"source_id": source_id, "remote_path": uploaded_path},
            )
        if source_id is not None:
            test_client.request(
                "DELETE",
                "/storage/source/delete",
                headers=auth_headers,
                json=[source_id],
            )


def test_product_rich_description_is_sanitized_on_create_and_update(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    code = f"rich-{uuid4().hex[:12]}"
    product_id = None
    create_description = (
        '<h2>商品亮点</h2><p><strong>安全正文</strong> 与 <em>排版</em></p>'
        '<ul><li>第一项</li><li>第二项</li></ul>'
        '<p><a href="https://example.com" onclick="alert(1)">了解更多</a></p>'
        '<img src="https://example.com/product.png" onerror="alert(1)">'
        '<script>alert("xss")</script>'
    )

    try:
        created_response = test_client.post(
            f"{PRODUCT_PATH}/create",
            headers=auth_headers,
            json={
                "name": "Rich Product",
                "code": code,
                "description": create_description,
                "price": "19.90",
                "stock": 2,
                "status": 0,
            },
        )
        assert created_response.status_code == 200, created_response.text
        created = response_data(created_response)
        product_id = created["id"]
        sanitized = created["description"]
        assert "<h2>商品亮点</h2>" in sanitized
        assert "<strong>安全正文</strong>" in sanitized
        assert "<ul>" in sanitized and "<li>第一项</li>" in sanitized
        assert "<img src=\"https://example.com/product.png\">" in sanitized
        assert "<script" not in sanitized
        assert "onclick" not in sanitized
        assert "onerror" not in sanitized

        update_description = '<h3>更新后的详情</h3><p style="color: red" onmouseover="evil()">更新正文</p><script>evil()</script>'
        updated_response = test_client.put(
            f"{PRODUCT_PATH}/update/{product_id}",
            headers=auth_headers,
            json={"description": update_description},
        )
        assert updated_response.status_code == 200, updated_response.text
        updated = response_data(updated_response)
        assert "<h3>更新后的详情</h3>" in updated["description"]
        assert "更新正文" in updated["description"]
        assert "onmouseover" not in updated["description"]
        assert "<script" not in updated["description"]

        app_detail = test_client.get(f"/app/product/{product_id}")
        assert app_detail.status_code == 200, app_detail.text
        app_description = response_data(app_detail)["description"]
        assert "<h3>更新后的详情</h3>" in app_description
        assert "<script" not in app_description
        assert "onmouseover" not in app_description
    finally:
        if product_id is not None:
            test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product_id])
