---
layout: doc
title: About Us
editLink: true
lastUpdated: true
---

## Overview

FastAPI Admin Starter is a general-purpose admin foundation built with FastAPI, Vue 3, and TypeScript. It provides runnable system-management capabilities while retaining the Generator, Storage, Scheduler, Redis, plugin infrastructure, and Web/App shells for future business modules.

## Included capabilities

- Authentication / Session, User, Role, Menu, Department, and Position
- Dictionary, Parameters, Login Log, Operation Log, Notice / Announcement
- Redis, Online Session, Health / Readiness, API Docs, Generic CRUD, and permissions
- App authentication foundation (registration, password login, SMS login, password reset)
- Dashboard, Scheduler / Cron Job, Generator, Storage Source/File, SMS Foundation, and plugin infrastructure
- MySQL, async SQLAlchemy, Web Admin shell, and App/H5 shell

## Technology

The backend uses Python, FastAPI, SQLAlchemy 2.0 async, Pydantic, Alembic, and Redis. The Web Admin uses Vue 3, TypeScript, Vite, Element Plus, and Pinia. Local infrastructure uses MySQL, Redis, and Docker Compose.

## Getting started

Read the [Quick Start](/en/guide/start) to configure local dependencies, database, Redis, backend, and Web Admin. The default `admin / 123456` credential is for local development initialization only and must not be used in production.

## Upstream and license

This Starter is based on [FastapiAdmin upstream](https://github.com/fastapiadmin/FastapiAdmin). Necessary technical attribution, historical package names, and upstream structure remain for review and future synchronization. The project uses the MIT License; the legal text is in the repository-root `LICENSE` file.
