# 参与贡献

欢迎通过代码、文档、缺陷报告和功能建议改进 FastAPI Admin Starter。

## 开始之前

1. 先搜索仓库现有 Issues，避免重复提交。
2. 较大改动先说明目标、影响范围和验证方式。
3. 保持现有异步 SQLAlchemy、Auth/RBAC、Redis、Generator、Storage 和 Scheduler 结构；避免无关重构。

## 本地开发

```bash
# 基础设施
cd docker && docker compose --env-file .env up -d mysql redis

# 后端
cd ../backend && uv sync && uv run main.py run --env=dev

# Web Admin
cd ../frontend/web && pnpm install && pnpm dev
```

## Pull Request

1. 从当前分支创建一个聚焦的工作分支。
2. 使用约定式提交信息，说明必要的行为变化。
3. 运行相关检查：`uv run pytest`、`uv run ruff check`、`pnpm test`、`pnpm type-check` 和 `pnpm build`。
4. 在 PR 描述中记录数据库、Redis、前端和测试验证结果。

## 来源与许可

本项目基于 [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin)。提交贡献即表示你同意将代码以项目的 [MIT License](./LICENSE) 发布。
