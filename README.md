# FastAPI Admin Starter

FastAPI Admin Starter 是一个基于 [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin) 的可扩展后台基础工程。它保留成熟的异步后端、权限体系、后台壳、移动端壳和开发工具，适合 Clone → Configure → Run → Develop。

## 技术栈

- Backend：Python 3.12+、FastAPI 0.138.2、SQLAlchemy 2.0 async、Pydantic、Alembic、APScheduler
- Web Admin：Vue 3、TypeScript、Vite、Element Plus、Pinia、Tailwind CSS
- App/H5：UniApp、Vue 3、TypeScript、Wot Design Uni
- Infrastructure：MySQL 8.4、Redis 7、Docker Compose

## 包含能力

- Authentication / Session、User、Role、Menu、Department、Position
- Dictionary、Parameters、Login Log、Operation Log、Notice / Announcement
- Redis、Online Session、Health / Readiness、API Docs、Generic CRUD、权限控制
- Dashboard（Workplace）
- App authentication foundation（注册、密码登录、短信验证码登录、密码重置）
- Scheduler / Cron Job、Generator、Storage Source/File（Local、FTP/SFTP、S3、OSS、OBS、COS）
- SMS Foundation（Aliyun / Tencent 固定配置、认证场景模板、发送记录）
- Plugin infrastructure、Web Admin shell、App/H5 shell

## 本地启动

### 1. 启动 MySQL 与 Redis

```bash
cd docker
cp .env.example .env
# 按本机环境设置 MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD、REDIS_PASSWORD
docker compose --env-file .env up -d mysql redis
```

默认 compose 使用 MySQL 8.4 和 Redis 7，并挂载本地持久化目录；不要使用 `docker compose down -v` 删除开发数据。

### 2. 启动 Backend

```bash
cd backend
cp env/.env.example env/.env.dev
# 编辑 env/.env.dev，填写 DATABASE_PASSWORD、DATABASE_NAME、REDIS_PASSWORD 等本机配置
uv sync --locked
uv run --locked main.py run --env=dev
```

首次启动使用 `create_all` 创建 ORM 表，并从 `backend/sql/data/` 写入基础 seed；已有数据的表不会被 seed 覆盖。模型变更时再使用：

```bash
uv run --locked main.py revision --env=dev
uv run --locked main.py upgrade --env=dev
```

首次 `create_all + seed` 建立上游基础 schema/data，`upgrade` 再应用已提交的 Starter Alembic revisions；它不会替代首次 `create_all`。新增 revision 后必须人工审核，再用于部署迁移。

### 3. 启动 Web Admin

```bash
cd frontend/web
pnpm install --frozen-lockfile
pnpm dev
```

默认本地地址：<http://127.0.0.1:5180/web#/login>。API 文档：<http://127.0.0.1:8001/api/v1/docs>。就绪检查：<http://127.0.0.1:8001/common/health/ready>。

### 4. 启动 App/H5

```bash
cd frontend/app
pnpm install --frozen-lockfile
VITE_API_BASE_URL=http://127.0.0.1:8001 VITE_APP_WS_ENDPOINT= \
pnpm dev:h5
```

具体地址以 Vite/UniApp 启动输出为准。当前 `frontend/app/.env.development` 保留 upstream 服务地址；上面的 shell 环境变量只为本地 H5 临时覆盖 API 地址，不修改 App 源码或提交本地配置。

## 本地默认账号

`admin / 123456` 仅用于本地开发初始化。首次进入可用环境后请立即修改密码；不要将默认凭据用于生产环境。

## 生产配置边界

使用 `ENVIRONMENT=prod` 启动时，应用会拒绝已知的不安全开发回退配置：必须关闭 `DEBUG`，设置不同于仓库默认值且足够长的 `SECRET_KEY`，配置明确的非通配 `PROD_CORS_ORIGINS`、`ALLOWED_HOSTS` 和 `OAUTH_ALLOWED_HOSTS`，并在启用凭据时为 CORS 提供明确的方法和请求头。`APP_SMS_FIXED_CODE_ENABLED` 在生产环境必须关闭；空生产库也不会自动创建本地默认管理员，请先预置管理员账号。

开发环境仍可使用 `create_all + seed` 和上述本地账号；生产环境需按实际域名、密钥和账号要求提供显式配置。本文不承诺一键生产部署。

## 扩展方式

- 使用 Generator 根据数据库表生成通用 CRUD，再按业务模块扩展。
- 按现有模块结构添加 Controller、Service、CRUD、Model、Schema 和菜单权限。
- 使用 Storage 管理文件与外部存储源，使用 Scheduler 注册维护或同步任务。
- 保持现有 async SQLAlchemy、Auth/RBAC、Redis 和插件注册机制。

模块、Generator、Storage、Scheduler 和 Web/App 的实际扩展路径见
[Starter Capability Baseline](docs/STARTER_CAPABILITY_BASELINE.md)。


## 测试

```bash
(cd backend && uv run --locked pytest)
(cd frontend/web && pnpm test && pnpm type-check && pnpm build)
(cd frontend/app && pnpm type-check && pnpm build:h5)
```

## 来源与许可

本项目基于 [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin)，保留必要的上游技术归属和 MIT License。法律文本见 [LICENSE](./LICENSE)；第三方依赖仍以各自许可证为准。
