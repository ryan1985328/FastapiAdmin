---
layout: doc
title: 项目概述
description: FastAPI Admin Starter 项目概述,基于 FastAPI + Vue3 + UniApp 的可扩展后台基础工程。
outline: "deep"
---

<div style="text-align: center;">
  <div align="center">
     <img src="/logo.svg" width="150" height="150" alt="logo" />
  </div>
  <h1>FastAPI Admin Starter</h1>
  <h3>可扩展的 FastAPI 后台基础工程</h3>
</div>

## 📘项目介绍

**FastAPI Admin Starter** 是一套基于 FastAPI、Vue 3 和 TypeScript 的通用后台基础工程。它采用前后端分离架构，保留系统管理、权限、日志、任务、存储、代码生成和多端壳等可复用能力。

> **设计边界**: 保持现有异步 SQLAlchemy、Auth/RBAC、Redis、插件注册、Generator、Storage 和 Scheduler 架构，业务模块在其上按现有结构扩展。

## 📦 工程结构概览

项目采用 **Monorepo** 架构，所有子工程在同一仓库中协同开发：

```sh
FastapiAdmin/
├─ backend/               # 后端工程 (FastAPI + Python)
├─ frontend/              # 前端工程
│   ├── web/              # Web 前端 (Vue3 + Element Plus)
│   ├── app/              # 移动端 (UniApp)
│   └── docs/             # 文档网站 (VitePress)
├─ docker/                # Docker 部署配置
│   ├── backend/          # 后端 Dockerfile
│   ├── nginx/            # Nginx 配置和静态文件
│   ├── mysql/            # MySQL 数据目录
│   └── redis/            # Redis 数据目录
├─ deploy.sh              # 一键部署脚本
├─ deploy.bat             # Windows 启动脚本
├─ LICENSE                # 开源协议
└─ README.md              # 项目文档
```

> 三个前端子工程均在 `frontend/` 目录下，分别是 `web`（Web 前端）、`app`（移动端）、`docs`（文档网站）。详细目录结构见 [前端开发](./frontend)、[后端开发](./backend)、[移动端开发](./miniprogram) 和 [部署指南](./deployment)。

## ✨核心亮点

| 特性 | 描述 |
| ---- | ---- |
| 🔭 快速开发 | 一套完全开源的现代化快速开发平台，旨在帮助开发者高效搭建高质量的企业级中后台系统。 |
| 🌐 全栈整合 | 前后端分离，融合 Python (FastAPI) + Vue3 多端开发，支持 Web 端和移动端。 |
| 🧱 模块化设计 | 系统功能高度解耦，插件化架构，支持自动路由发现和注册，便于扩展和维护。 |
| ⚡️ 高性能异步 | 使用 FastAPI 异步框架 + Redis 缓存优化接口响应速度。 |
| 🔒 安全认证 | 支持 JWT OAuth2 认证机制，保障系统安全。 |
| 📊 权限管理 | RBAC 模型实现菜单、按钮、数据级别的细粒度权限控制。 |
| 🚀 快速部署 | 支持 Docker/Docker Compose/Nginx 一键部署。 |
| 📄 开发友好 | 提供完善的中文文档 + 中文化界面 + 可视化工具链，降低学习成本。 |
| 🧩 快速接入 | 基于 Vue3、Vite5、Pinia、ElementPlus 等主流前端技术栈，开箱即用。 |
| 📱 移动端支持 | 保留 UniApp App/H5 shell，支持未来按需扩展多端应用。 |
| 🎨 主题定制 | 支持深色/浅色主题切换，提供个性化界面体验。 |
| 🌍 国际化支持 | 内置国际化框架，支持多语言切换。 |
| 📈 数据可视化 | 集成图表库，提供丰富的数据可视化能力。 |
| 🛠️ 代码生成 | 内置代码生成工具，提升开发效率。 |

## 🛠️技术栈概览

| 类型     | 技术选型            | 描述 |
|----------|---------------------|---------------------|
| 后端框架 | FastAPI / Uvicorn / Pydantic 2.0 / Alembic | 现代、高性能的异步框架，强制类型约束，数据迁移。 |
| ORM      | SQLAlchemy 2.0      | 强大的 ORM 库。 |
| 定时任务 | APScheduler         | 轻松实现定时任务。 |
| 权限认证 | PyJWT               | 实现 JWT 认证。 |
| 前端框架 | Vue3 / Vite5 / Pinia / TypeScript | 快速开发 Vue3 应用。 |
| 前端工具 | ESLint / Prettier / Stylelint | 代码质量和风格工具。 |
| 移动端框架 | UniApp / Vue3 / TypeScript | 跨平台移动应用开发。 |
| UI 库    | ElementPlus (Web) / Wot Design Uni (移动端) | 企业级 UI 组件库。 |
| CSS 框架 | UnoCSS / SCSS       | 原子化 CSS 和预处理器。 |
| 数据库   | MySQL / PostgreSQL / SQLite | 关系型数据库支持。 |
| 缓存     | Redis               | 强大的缓存数据库。 |
| 文档     | Swagger / Redoc     | 自动生成 API 文档。 |
| 部署     | Docker / Nginx / Docker Compose | 快速部署项目。 |
| 监控     | 内置服务器监控 / 缓存监控 | 系统运行状态监控。 |
| 国际化   | i18n                | 多语言支持。 |
| 数据可视化 | ECharts             | 图表库。 |

## 📌内置模块

| 模块名 | 子模块名 | 描述 |
|--------|----------|------|
| 仪表盘 | 工作台、分析页 | 系统概览和数据分析 |
| 系统管理 | 用户、角色、菜单、部门、岗位、字典、配置、公告 | 核心系统管理功能 |
| 监控管理 | 在线用户、服务器监控、缓存监控 | 系统运行状态监控 |
| 任务管理 | 定时任务 | 异步任务调度管理 |
| 日志管理 | 操作日志 | 用户行为审计 |
| 开发工具 | 代码生成、表单构建、接口文档 | 提升开发效率的工具 |
| 文件管理 | 文件存储 | 统一文件管理 |

> 移动端模块详见 [移动端开发](./miniprogram)。

## 📐 分包理念：按业务域 vs 按技术层

讨论的是**源码目录如何划分**（文件夹怎么分包），与是否做 MVC / Controller–Service–CRUD **逻辑分层**是不同的概念。

| 方式 | 组织方式 | 典型目录（示例） |
|------|----------|-----------------|
| **按技术层次分包** | 同一类技术文件归在一起 | 顶层 `models/`、`schemas/`、`services/`、`controllers/` … |
| **按业务特性分包** | 同一业务域的文件归在一起 | `app/api/v1/module_*/` 下并列 `controller.py`、`service.py`、`crud.py`、`model.py`、`schema.py` |

**本项目（后端）采用：按业务特性分包（竖切）。**

**设计考量**：
- **解耦的单位是业务边界**：以系统管理、监控等为模块，子域内再分文件。多人协作时各自目录独立，减少冲突。
- **面向未来的拆分**：若要将某一模块独立成子工程，一整个目录搬走即可。按层分包则需要跨多个顶层目录抽取。
- **分层仍在**：Controller → Service → CRUD → Model 的**逻辑分层没有消失**，只是**叠在业务包内部**，而不是拿「全项目唯一的分层目录」作为第一维划分。
