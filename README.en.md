# FastAPI Admin Starter

FastAPI Admin Starter is an extensible admin foundation based on [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin). It keeps the upstream async backend, permission system, admin shell, mobile shell, and developer tooling for a simple Clone → Configure → Run → Develop workflow.

## Stack

- Backend: Python 3.12+, FastAPI 0.138.2, async SQLAlchemy 2.0, Pydantic, Alembic, APScheduler
- Web Admin: Vue 3, TypeScript, Vite, Element Plus, Pinia, Tailwind CSS
- App/H5: UniApp, Vue 3, TypeScript, Wot Design Uni
- Infrastructure: MySQL 8.4, Redis 7, Docker Compose

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

The compose file uses MySQL 8.4 and Redis 7 with local persistent directories. Do not use `docker compose down -v` for normal development.

### 2. Start the backend

```bash
cd backend
cp env/.env.example env/.env.dev
# Edit env/.env.dev with local database and Redis credentials
uv sync --locked
uv run --locked main.py run --env=dev
```

The first start creates ORM tables with `create_all` and loads core seed data from `backend/sql/data/`. Tables with existing data are not reseeded. For model changes, use Alembic:

```bash
uv run --locked main.py revision --env=dev
uv run --locked main.py upgrade --env=dev
```

The upstream baseline currently has no committed Alembic revisions. `upgrade` is runnable but does not replace the initial `create_all`; review generated revisions before deployment.

### 3. Start the Web Admin

```bash
cd frontend/web
pnpm install --frozen-lockfile
pnpm dev
```

Default local URL: <http://127.0.0.1:5180/web#/login>. API docs: <http://127.0.0.1:8001/api/v1/docs>. Readiness: <http://127.0.0.1:8001/common/health/ready>.

### 4. Start App/H5

```bash
cd frontend/app
pnpm install --frozen-lockfile
VITE_API_BASE_URL=http://127.0.0.1:8001 VITE_APP_WS_ENDPOINT= \
pnpm dev:h5
```

Use the URL printed by Vite/UniApp. The tracked `frontend/app/.env.development` retains the upstream service address; the shell variables above temporarily point local H5 at the local backend without changing App source or committing local configuration.

## Local default account

`admin / 123456` is provided only for local development initialization. Change it before using a deployed environment; never use the default credential in production.

## Extending the Starter

- Use Generator to create standard CRUD from database tables, then extend the business module.
- Follow the existing module layout for Controller, Service, CRUD, Model, Schema, and menu permissions.
- Use Storage for files and external storage sources; use Scheduler for maintenance and synchronization jobs.
- Keep the existing async SQLAlchemy, Auth/RBAC, Redis, and plugin registration mechanisms.

See [Starter Capability Baseline](docs/STARTER_CAPABILITY_BASELINE.md) for the concrete module, Generator, Storage, Scheduler, and frontend extension paths.


## Tests

```bash
(cd backend && uv run --locked pytest)
(cd frontend/web && pnpm test && pnpm type-check && pnpm build)
(cd frontend/app && pnpm type-check && pnpm build:h5)
```

## Source and license

This distribution is based on [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin) and retains the required upstream technical attribution and MIT License. See [LICENSE](./LICENSE); third-party dependencies remain subject to their own licenses.
