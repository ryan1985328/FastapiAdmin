# Reference Product Module

This module is a small, generic business-module example for the Starter. It demonstrates the existing Generator/plugin/CRUD/Admin Web path without changing the Core architecture.

## Layout

- Backend plugin: `backend/app/plugin/module_product/product/`
- Admin Web API: `frontend/web/src/api/module_product/product.ts`
- Admin Web page: `frontend/web/src/views/module_product/product/index.vue`
- Menu seed: `backend/sql/data/sys_menu.json`
- API prefix: `/product/product`

The module is intentionally Web-admin only. `frontend/app` has no Product route, API, store, or menu entry.

## Generator record

The existing Generator was validated first with Product fields and rendered the following skeletons:

- `model.py`
- `schema.py`
- `crud.py`
- `service.py`
- `controller.py`
- Web API/types
- Web CRUD view

Manual patches add practical Product constraints, unique-code checking, default `sort/id` ordering, import required-field validation, and the image upload slot. The module keeps the generated controller/service/CRUD layering and existing permissions, pagination, audit fields, import/export, and status endpoint.

## Data contract

Product contains only reference fields: `name`, unique `code`, `description`, `image_url`, Decimal `price`, non-negative `stock`, 0/1 `status`, non-negative `sort`, and `remark`. `status=0` means enabled and `status=1` means disabled. Common IDs, UUID, soft-delete, timestamps, and audit relations come from the existing base mixins.

There is no Product demo seed. A fresh initialization creates the table and menu/permission records; developers can add records through the page or API.

## API and Storage

The page uses the existing generic CRUD conventions:

- `GET /product/product/list`
- `GET /product/product/detail/{id}`
- `POST /product/product/create`
- `PUT /product/product/update/{id}`
- `DELETE /product/product/delete`
- `PATCH /product/product/status/batch`

The list endpoint supports name/code `like` filters, status filtering, pagination, and the standard audit filters. Product images are uploaded through `/storage/file/upload`; the returned `file_url` or `file_path` is stored in `image_url`. No second file-storage subsystem is introduced.

## Extending the example

For a new business module, use the existing Generator to inspect the table and render the same layer set, then apply only domain-specific validation and UI slots. Add the module's Web menu and permissions to the seed data, keep shared Core/Storage/Scheduler code unchanged, and add focused API tests before broader regression validation.
