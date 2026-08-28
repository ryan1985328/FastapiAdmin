# FastAPI Admin Starter

FastAPI Admin Starter is an extensible admin foundation based on [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin). It keeps the upstream async backend, permission system, admin shell, mobile shell, and developer tooling for a simple Clone → Configure → Run → Develop workflow.

## Stack

- Backend: Python 3.12+, FastAPI 0.138.2, async SQLAlchemy 2.0, Pydantic, Alembic, APScheduler
- Web Admin: Vue 3, TypeScript, Vite, Element Plus, Pinia, Tailwind CSS
- App/H5: UniApp, Vue 3, TypeScript, Wot Design Uni
- Infrastructure: MySQL 8.0+ (MySQL 8.4 for the local baseline), Redis 7, Docker Compose

## Included capabilities

- Authentication / Session, User, Role, Menu, Department, Position
- Dictionary, Parameters, Login Log, Operation Log, Notice / Announcement
- Redis, Online Session, Health / Readiness, API Docs, Generic CRUD, permissions
- Dashboard (Workplace, Analysis, Screen)
- Scheduler / Cron Job, Generator, Storage (Local, FTP/SFTP, S3, OSS, OBS, COS)
- Plugin infrastructure, Web Admin shell, App/H5 shell

## Local setup

### 1. Start MySQL and Redis

```bash
cd docker
cp .env.example .env
# Set MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, and REDIS_PASSWORD for your machine
docker compose --env-file .env up -d mysql redis
```

### 2. Start the backend

```bash
cd backend
uv sync
uv run main.py run --env=dev
```

The first start creates the database schema and core seed data. For model changes, use Alembic:

```bash
uv run main.py revision --env=dev
uv run main.py upgrade --env=dev
```

### 3. Start the Web Admin

```bash
cd frontend/web
pnpm install
pnpm dev
```

Default local URL: <http://127.0.0.1:5180/web#/login>. API docs: <http://127.0.0.1:8001/api/v1/docs>.

### 4. Start App/H5

```bash
cd frontend/app
pnpm install
pnpm dev:h5
```

Use the URL printed by Vite/UniApp. The App development environment uses `frontend/app/.env.development` to connect to the local backend.

## Local default account

`admin / 123456` is provided only for local development initialization. Change it before using a deployed environment; never use the default credential in production.

## Extending the Starter

- Use Generator to create standard CRUD from database tables, then extend the business module.
- Follow the existing module layout for Controller, Service, CRUD, Model, Schema, and menu permissions.
- Use Storage for files and external storage sources; use Scheduler for maintenance and synchronization jobs.
- Keep the existing async SQLAlchemy, Auth/RBAC, Redis, and plugin registration mechanisms.

## Tests

```bash
cd backend && uv run pytest
cd frontend/web && pnpm test && pnpm type-check && pnpm build
cd frontend/app && pnpm type-check && pnpm build:h5
```

## Source and license

This distribution is based on [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin) and retains the required upstream technical attribution and MIT License. See [LICENSE](./LICENSE); third-party dependencies remain subject to their own licenses.
