# FastAPI Admin Starter 文档工程

FastAPI Admin Starter 的文档工程，基于 [VitePress](https://vitepress.dev/) 构建。

> **与仓库根文档的关系**：项目总览、本地启动、开发账号、Docker 部署等请以 [根目录 README.md](../../README.md) 为准；**本文档**侧重 `frontend/docs/` 文档工程的开发与维护。

## 项目结构

```sh
frontend/docs/
├── .vitepress/              # VitePress 配置
│   ├── cache/               # 缓存目录
│   ├── theme/               # 主题配置
│   │   ├── index.ts         # 主题入口
│   │   └── style.css        # 主题样式
│   └── config.mts           # 主配置文件
├── src/                     # 文档源文件
│   ├── guide/               # 指南
│   │   ├── overview.md      # 项目概述
│   │   ├── start.md         # 快速开始
│   │   ├── why.md           # Starter 概述
│   │   ├── frontend.md      # 前端开发
│   │   ├── backend.md       # 后端开发
│   │   ├── miniprogram.md   # 移动端开发
│   │   ├── guidelines.md    # 开发规范
│   │   ├── examples.md      # 示例
│   │   ├── custom-development.md  # 自定义开发
│   │   ├── deployment.md    # 部署指南
│   │   └── api-docs.md      # API 文档说明
│   ├── about/               # 关于
│   │   ├── about.md         # 关于我们
│   │   └── contributing.md  # 贡献指南
│   ├── en/                  # 英文文档（结构同中文）
│   ├── public/              # 公共资源
│   └── index.md             # 根首页
├── package.json             # 项目依赖文件
├── pnpm-lock.yaml           # pnpm 锁定文件
└── tsconfig.json            # TypeScript 配置
```

## 快速开始

```bash
cd frontend/docs
pnpm install
pnpm run dev          # 运行文档工程（默认 http://127.0.0.1:5174）
pnpm run build        # 构建文档工程
```

构建产物在 `dist/` 下，可部署到 Nginx 等静态服务器。

## 文档编写规范

- 文档使用 Markdown 编写，放在 `src/guide/` 或 `src/about/` 对应目录下
- 英文文档放在 `src/en/` 下，结构与中文一致
- 图片等静态资源放在 `src/public/` 下
- 修改导航/侧边栏需编辑 `.vitepress/config.mts`

## 来源与许可

文档内容服务于 FastAPI Admin Starter；项目基于 [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin)，并保留必要的技术归属和 MIT License。
