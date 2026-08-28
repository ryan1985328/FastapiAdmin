# FastAPI Admin Starter — Capability Baseline

这份文档记录当前 Starter 的可运行基线和最短扩展路径，目标是 Clone → Configure → Run → Develop。它不改变现有 FastAPI Admin 的认证、权限、异步 SQLAlchemy、Redis、Generator、Storage 或 Scheduler 结构。

## 1. 本地启动

要求：Python 3.12+、uv、Node.js 20+、pnpm、Docker Desktop（含 Compose v2）。

```bash
cd docker
cp .env.example .env
# 编辑 .env，设置 MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD、REDIS_PASSWORD
docker compose --env-file .env up -d mysql redis
docker compose ps
```

当前受版本控制的 compose 使用 `mysql:8.4` 和 `redis:7-alpine`，数据分别落在 `docker/mysql/data/` 与 `docker/redis/data/`。日常开发不要使用 `docker compose down -v`。

```bash
cd backend
cp env/.env.example env/.env.dev
# 编辑 env/.env.dev，使 DATABASE_* 与 docker/.env 的 MySQL 用户/密码/数据库一致
# 同样填写 REDIS_HOST、REDIS_PORT、REDIS_PASSWORD、REDIS_DB_NAME
uv sync --locked
uv run --locked main.py run --env=dev
```

`main.py run --env=dev` 会在加载 Settings 前设置环境名，因此 clean clone 不需要预先导出 `ENVIRONMENT`。`backend/env/.env.dev` 被 `.gitignore` 忽略，不要提交。

Web Admin：

```bash
cd frontend/web
pnpm install --frozen-lockfile
pnpm dev
```

App/H5：

```bash
cd frontend/app
pnpm install --frozen-lockfile
VITE_API_BASE_URL=http://127.0.0.1:8001 VITE_APP_WS_ENDPOINT= pnpm dev:h5
```

当前 `frontend/app/.env.development` 保留 upstream 服务地址。上面的 shell 变量仅临时把 H5 请求指向本地 backend；本阶段不修改、删除或重构 `frontend/app`。

常用地址：

- Web 登录：`http://127.0.0.1:5180/web#/login`
- Swagger：`http://127.0.0.1:8001/api/v1/docs`
- ReDoc：`http://127.0.0.1:8001/api/v1/redoc`
- Readiness：`http://127.0.0.1:8001/common/health/ready`

本地 seed 默认账号为 `admin / 123456`，只用于开发，不得用于生产。

## 2. Seed 用户边界

当前 `sys_user`、表结构和 Auth/RBAC 保持原样；本阶段不清理 seed 用户。

| 用户 | 当前用途 | 依赖 |
| --- | --- | --- |
| `super` | `SUPER_ADMIN` 超级管理员；`is_superuser=true`，用于最高权限基线 | `sys_user`、`sys_user_roles`、`sys_role`、系统菜单/权限 |
| `admin` | `ADMIN` 管理员；当前 seed 仍为 `is_superuser=true`，用于默认登录和后台 smoke | `sys_user`、`sys_user_roles`、`sys_role`、系统菜单/权限 |
| `user` | `USER` 普通用户；`is_superuser=false`，按角色菜单和数据范围限制 | `sys_user`、`sys_user_roles`、`sys_role_menus`，默认数据范围为本人 |

三者的 seed 定义位于 `backend/sql/data/sys_user.json`、`sys_role.json` 和 `sys_user_roles.json`。是否保留或调整 Demo seed 用户留待后续 Review。

## 3. 数据库生命周期

- 首次 backend startup 调用 `app/scripts/initialize.py`。
- `create_tables()` 使用 `MappedBase.metadata.create_all` 创建当前 ORM 表。
- seed 从 `backend/sql/data/{table}.json` 读取；已有数据的表会跳过，不做覆盖或回滚。
- 当前目标数据库是 MySQL 8.4；Redis 同时用于缓存、会话和 APScheduler 默认 jobstore。
- Alembic 配置在 `backend/alembic.ini` 和 `backend/app/alembic/env.py`；当前 `backend/app/alembic/versions/` 没有实际 revision，仅有 `__init__.py`。
- `uv run --locked main.py upgrade --env=dev` 可以运行，但没有 revision head；第一次初始化仍由 `create_all + seed` 完成。

未来模型变更流程：修改并测试 ORM → `revision --env=dev` 生成 revision → 人工审核 SQL/数据影响 → 在目标环境执行 `upgrade --env=dev`。当前没有自动迁移体系改造，也不应把 `create_all` 当作生产迁移方案。

## 4. Backend 模块开发路径

可参考现有公告模块：

`backend/app/api/v1/module_system/notice/` 包含 `model.py`、`schema.py`、`crud.py`、`service.py`、`controller.py`；`backend/app/api/v1/module_system/__init__.py` 将 `NoticeRouter` 挂入 `/system`。Controller 中同时声明 endpoint permission，例如 `module_system:notice:query`，对应菜单/按钮权限在 `backend/sql/data/sys_menu.json`。

通用新模块步骤：

1. 沿用 Model → Schema → CRUD → Service → Controller 的分层。
2. 系统模块在对应 `module_system`/`module_monitor` router 中注册；插件模块放在 `backend/app/plugin/module_xxx/**/controller.py`。
3. 插件 controller 顶层声明 `APIRouter`，动态发现器会把 `module_xxx` 映射到 `/xxx`，不需要改核心注册器。
4. 在菜单 seed 中建立目录、页面和按钮，保持 `component_path`、route path、permission 字符串一致。
5. 为 Service/Controller 和权限边界补 backend tests。

## 5. Web Admin 扩展路径

现有 Web 页面使用后端菜单动态生成路由：`frontend/web/src/router/MenuProcessor.ts` 读取菜单，`route-loader.ts` 通过 `import.meta.glob('/src/views/**/*.vue')` 解析 `component_path`。

以 Notice 为例：

- API client：`frontend/web/src/api/module_system/notice.ts`
- 页面：`frontend/web/src/views/module_system/notice/index.vue`
- 菜单/按钮/权限：`backend/sql/data/sys_menu.json`
- 公共表单、搜索栏、表格和抽屉优先复用现有 `Fa*` 组件。

因此新增 Admin 功能通常是 backend endpoint + Web API client + view + seed menu/permission + locale/test，而不是重写 router 或 shell。

## 6. Generator

Generator 保留为开发效率能力。

- Backend：`backend/app/api/v1/module_generator/gencode/`
- Templates：`backend/templates/python/`、`backend/templates/vue/`、`backend/templates/ts/`
- Web：`frontend/web/src/views/module_generator/gencode/`
- API：`/api/v1/generator/gencode/*`

工作流是数据库表 → 导入表结构 → 编辑 module/package/menu 配置 → 预览 → 下载 ZIP 或输出到指定路径。生成结果默认包含 backend plugin 的 model/schema/crud/service/controller，以及 Web API/view。生成到仓库前先审阅结果；临时实验不要写入源码。

## 7. Storage

Storage 入口为 `/api/v1/storage`，管理层位于 `backend/app/api/v1/module_storage/`。

当前 provider：Local、FTP、FTPS、SFTP、S3、OSS、OBS、COS。Storage source 的密码由现有加密层保存，不在响应中返回明文。

常用路径：

- Source：`POST /storage/source/create`、`POST /storage/source/test/{id}`
- File：`POST /storage/file/upload`、`GET /storage/file/list`、`POST /storage/file/download`、`DELETE /storage/file/delete`
- Provider factory：`backend/app/api/v1/module_storage/core/factory.py`

业务模块应保存返回的 `file_path`/对象 key 或业务引用，并按 source_id 读取；不要把 provider SDK 直接写进业务 controller。

## 8. Scheduler / Cron Job

Scheduler 由 `backend/app/core/ap_scheduler.py` 管理，启动时注册系统操作日志清理任务。

- Jobstore：Redis `default`、SQLAlchemy `sqlalchemy`、内存 `memory`
- 节点定义：`task_node`，API 前缀 `/api/v1/task/cronjob/node`
- 执行日志：`task_job`，API 前缀 `/api/v1/task/cronjob/job`
- Web 管理页：`frontend/web/src/views/module_task/cronjob/`

新任务沿用 Node 的 `func` 代码块约定，定义 `handler(*args, **kwargs)`，先用 `now` 或短期 date trigger 验证，再配置 cron/interval。应使用无副作用的维护、同步、缓存刷新或统计任务；任务失败由现有事件监听写入执行日志。

## 9. App/H5 边界

`frontend/app` 保留为未来 C 端用户基础工程。本阶段只确认：

- 请求基址由 `VITE_API_BASE_URL + VITE_APP_BASE_API` 组成，实现在 `src/http/adapters/alova.ts`。
- 路由守卫在 `src/router/index.ts`，用户状态在 `src/store/userStore.ts`。
- H5 使用 UniApp/Vite，`base` 为 `/app`。
- 不删除 OA 页面、不调整 App shell、不改 `sys_user`，也不把 App 当作 Admin 扩展路径。

## 10. Baseline 验证命令

```bash
(cd backend && uv sync --locked && uv run --locked pytest)
(cd frontend/web && pnpm install --frozen-lockfile && pnpm test && pnpm type-check && pnpm build)
(cd frontend/app && pnpm install --frozen-lockfile && pnpm type-check && pnpm build:h5)
```

另外检查 Docker：

```bash
cd docker && docker compose --env-file .env ps
curl -f http://127.0.0.1:8001/common/health/ready
curl -f http://127.0.0.1:8001/api/v1/openapi.json
```

当前基线的生产注意事项只有两项：默认账号仅限本地；Alembic 尚无提交 revision，生产结构变更必须先建立并审核 migration lineage。
