"""Focused final Product media and public Mall contract tests."""

from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit

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


def _create_local_source(test_client, auth_headers, tmp_path: Path) -> int:
    response = test_client.post(
        "/storage/source/create",
        headers=auth_headers,
        json={
            "name": f"mall-final-local-{uuid4().hex[:10]}",
            "protocol": "local",
            "host": str(tmp_path),
            "port": 0,
            "is_default": True,
            "status": 0,
        },
    )
    assert response.status_code == 200, response.text
    return response_data(response)["id"]


def _upload(test_client, auth_headers, source_id: int, filename: str, content: bytes) -> dict:
    response = test_client.post(
        "/storage/file/upload",
        headers=auth_headers,
        files={"file": (filename, content, "image/png")},
        data={"source_id": str(source_id)},
    )
    assert response.status_code == 200, response.text
    result = response_data(response)
    assert result["file_path"]
    assert result["file_url"].startswith("http://testserver/")
    assert result["source_id"] == source_id
    return result


def _create_product(test_client, auth_headers, *, images: list[dict] | None = None, image_url: str | None = None) -> dict:
    payload = {
        "name": "Mini Mall Final Product",
        "code": f"mall-final-{uuid4().hex[:14]}",
        "description": "Final product media contract",
        "price": "49.90",
        "stock": 12,
        "status": 0,
        "sort": 1,
    }
    if images is not None:
        payload["images"] = images
    if image_url is not None:
        payload["image_url"] = image_url
    response = test_client.post(f"{PRODUCT_PATH}/create", headers=auth_headers, json=payload)
    assert response.status_code == 200, response.text
    return response_data(response)


def _public_get(test_client, url: str):
    parsed = urlsplit(url)
    return test_client.get(parsed.path + (f"?{parsed.query}" if parsed.query else ""))


def test_product_images_order_primary_ownership_and_public_read(
    test_client,
    auth_headers,
    tmp_path: Path,
):
    source_id = _create_local_source(test_client, auth_headers, tmp_path)
    product_id = None
    uploads: list[dict] = []
    try:
        for index in range(3):
            uploads.append(_upload(test_client, auth_headers, source_id, f"mall-{index}.png", f"image-{index}".encode()))

        unauthenticated_upload = test_client.post(
            "/storage/file/upload",
            files={"file": ("blocked.png", b"blocked", "image/png")},
            data={"source_id": str(source_id)},
        )
        assert unauthenticated_upload.status_code in {401, 403}

        image_payload = [
            {"storage_key": upload["file_path"], "source_id": source_id, "sort": index}
            for index, upload in enumerate(uploads)
        ]
        product = _create_product(test_client, auth_headers, images=image_payload)
        product_id = product["id"]
        assert [image["storage_key"] for image in product["images"]] == [upload["file_path"] for upload in uploads]
        assert product["cover_url"] == product["images"][0]["url"]
        assert product["images"][0]["url"].startswith("http://testserver/")

        public_image = _public_get(test_client, product["images"][0]["url"])
        assert public_image.status_code == 200, public_image.text
        assert public_image.content == b"image-0"
        assert public_image.headers["content-type"].startswith("image/png")

        app_detail = test_client.get(f"/app/product/{product_id}")
        assert app_detail.status_code == 200, app_detail.text
        app_product = response_data(app_detail)
        assert [image["url"] for image in app_product["images"]] == [image["url"] for image in product["images"]]
        assert app_product["cover_url"] == app_product["images"][0]["url"]
        assert "storage_key" not in app_product["images"][0]

        reordered = list(reversed(product["images"]))
        update = test_client.put(
            f"{PRODUCT_PATH}/update/{product_id}",
            headers=auth_headers,
            json={
                "images": [
                    {
                        "id": image["id"],
                        "storage_key": image["storage_key"],
                        "source_id": image["source_id"],
                        "sort": index,
                    }
                    for index, image in enumerate(reordered)
                ]
            },
        )
        assert update.status_code == 200, update.text
        updated = response_data(update)
        assert [image["storage_key"] for image in updated["images"]] == [image["storage_key"] for image in reordered]
        assert updated["cover_url"] == updated["images"][0]["url"]

        too_many = test_client.post(
            f"{PRODUCT_PATH}/create",
            headers=auth_headers,
            json={
                "name": "Too many images",
                "code": f"mall-too-many-{uuid4().hex[:12]}",
                "price": "1.00",
                "stock": 1,
                "images": [
                    {"storage_key": f"too-many-{index}.png", "source_id": source_id, "sort": index}
                    for index in range(10)
                ],
            },
        )
        assert too_many.status_code == 422, too_many.text

        traversal = test_client.post(
            f"{PRODUCT_PATH}/create",
            headers=auth_headers,
            json={
                "name": "Unsafe image key",
                "code": f"mall-unsafe-{uuid4().hex[:12]}",
                "price": "1.00",
                "stock": 1,
                "images": [{"storage_key": "%252e%252e/secret.png", "source_id": source_id}],
            },
        )
        assert traversal.status_code == 422, traversal.text

        missing = test_client.get(f"/storage/file/public/not-found.png?source_id={source_id}")
        assert missing.status_code == 404
        encoded_traversal = test_client.get("/storage/file/public/%252e%252e/secret.png")
        assert encoded_traversal.status_code == 404
        absolute_path = test_client.get("/storage/file/public//etc/passwd")
        assert absolute_path.status_code == 404

        foreign_product = _create_product(test_client, auth_headers)
        foreign_product_id = foreign_product["id"]
        try:
            foreign_update = test_client.put(
                f"{PRODUCT_PATH}/update/{foreign_product_id}",
                headers=auth_headers,
                json={
                    "images": [
                        {
                            "id": updated["images"][0]["id"],
                            "storage_key": updated["images"][0]["storage_key"],
                            "source_id": source_id,
                        }
                    ]
                },
            )
            assert foreign_update.status_code == 409, foreign_update.text
            original = test_client.get(f"{PRODUCT_PATH}/detail/{product_id}", headers=auth_headers)
            assert response_data(original)["images"][0]["id"] == updated["images"][0]["id"]
        finally:
            test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[foreign_product_id])

        detached = test_client.put(
            f"{PRODUCT_PATH}/update/{product_id}",
            headers=auth_headers,
            json={"images": []},
        )
        assert detached.status_code == 200, detached.text
        assert response_data(detached)["images"] == []
        assert (tmp_path / uploads[0]["file_path"]).is_file()
        assert _public_get(test_client, uploads[0]["file_url"]).status_code == 200
    finally:
        if product_id is not None:
            test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product_id])
        for upload in uploads:
            test_client.request(
                "DELETE",
                "/storage/file/delete",
                headers=auth_headers,
                json={"source_id": source_id, "remote_path": upload["file_path"]},
            )
        test_client.request("DELETE", "/storage/source/delete", headers=auth_headers, json=[source_id])


def test_local_rich_content_uses_public_url_and_sanitizes_html(test_client, auth_headers, tmp_path: Path):
    source_id = _create_local_source(test_client, auth_headers, tmp_path)
    product_id = None
    upload = None
    try:
        upload = _upload(test_client, auth_headers, source_id, "rich-content.png", b"rich-content-image")
        description = f'<p>安全详情</p><img src="{upload["file_url"]}" onerror="evil()"><script>evil()</script>'
        product = _create_product(test_client, auth_headers)
        product_id = product["id"]
        update = test_client.put(
            f"{PRODUCT_PATH}/update/{product_id}",
            headers=auth_headers,
            json={"description": description},
        )
        assert update.status_code == 200, update.text
        saved = response_data(update)["description"]
        assert upload["file_url"] in saved
        assert "<img" in saved
        assert "onerror" not in saved
        assert "<script" not in saved
        assert _public_get(test_client, upload["file_url"]).status_code == 200

        app_detail = test_client.get(f"/app/product/{product_id}")
        assert app_detail.status_code == 200, app_detail.text
        app_description = response_data(app_detail)["description"]
        assert upload["file_url"] in app_description
        assert "<script" not in app_description
    finally:
        if product_id is not None:
            test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product_id])
        if upload is not None:
            test_client.request(
                "DELETE",
                "/storage/file/delete",
                headers=auth_headers,
                json={"source_id": source_id, "remote_path": upload["file_path"]},
            )
        test_client.request("DELETE", "/storage/source/delete", headers=auth_headers, json=[source_id])


def test_legacy_image_url_fallback_is_kept_in_public_dto(test_client, auth_headers):
    product = _create_product(test_client, auth_headers, image_url="https://cdn.example.test/legacy-cover.png")
    product_id = product["id"]
    try:
        detail = test_client.get(f"/app/product/{product_id}")
        assert detail.status_code == 200, detail.text
        data = response_data(detail)
        assert data["cover_url"] == "https://cdn.example.test/legacy-cover.png"
        assert data["images"] == [{"url": "https://cdn.example.test/legacy-cover.png", "sort": 0}]
    finally:
        test_client.request("DELETE", f"{PRODUCT_PATH}/delete", headers=auth_headers, json=[product_id])
