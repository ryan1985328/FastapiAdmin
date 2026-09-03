---
layout: doc
title: 关于我们
editLink: true
lastUpdated: true
---

## 项目简介

FastAPI Admin Starter 是一个基于 FastAPI、Vue 3 和 TypeScript 的通用后台基础工程。它提供可以直接运行的系统管理能力，并保留 Generator、Storage、Scheduler、Redis、插件和 Web/App 壳，方便在现有基础上添加业务模块。

## 保留能力

- Authentication / Session、User、Role、Menu、Department、Position
- Dictionary、Parameters、Login Log、Operation Log、Notice / Announcement
- Redis、Online Session、Health / Readiness、API Docs、Generic CRUD 和权限控制
- App 认证基础（注册、密码登录、短信登录、密码重置）
- Dashboard、Scheduler / Cron Job、Generator、Storage Source/File、SMS Foundation 与插件基础设施
- MySQL、异步 SQLAlchemy、Web Admin shell 与 App/H5 shell

## 技术栈

Backend 使用 Python、FastAPI、SQLAlchemy 2.0 async、Pydantic、Alembic 和 Redis；Web Admin 使用 Vue 3、TypeScript、Vite、Element Plus 与 Pinia；本地基础设施使用 MySQL、Redis 与 Docker Compose。

## 开始使用

请先阅读 [快速开始](/guide/start)，完成本地依赖、数据库、Redis、Backend 和 Web Admin 的启动。默认 `admin / 123456` 仅用于本地开发初始化，不应带入生产环境。

## 上游来源与许可

本 Starter 基于 [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin)。必要的技术归属、历史包名和上游结构保留，以便后续同步和审阅；项目使用 MIT License，法律文本见仓库根目录的 `LICENSE`。
