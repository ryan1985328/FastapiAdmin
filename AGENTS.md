# FastAPI Admin Starter — AI Development Rules

## Default mode

- Default to **Fast Iteration + Targeted Validation**. Daily development is not release validation.
- The repository is in the **Starter Skeleton / Capability Productization Development Stage**. The normal loop is `Capability → Implementation → Apply to Current Dev Environment → Targeted Runtime Verification → Complete`; this is not a Production, Pre-production, Shared Test, or Migration Compatibility stage.
- Priorities are **Stability First, Reuse First, Subtract First, Targeted First, Current Dev Environment First**. Use Migration When Needed and apply Release Rigor At Release Time.
- Read task-specific project docs when relevant. `docs/STARTER_CAPABILITY_BASELINE.md` remains the startup and baseline reference; its broad validation commands apply when doing a baseline/release check or when explicitly requested.

## Authorization and scope

- An explicit request to implement, develop, fix, continue, or “GOGO” authorizes ordinary local work within the task: read/write scoped files, required schema/data changes in the current development database, Generator runs, required menu/permission/dictionary/seed/Generator metadata, directly needed dependencies, local services, focused checks, and a local commit.
- Do not repeatedly ask for approval for those ordinary operations, including inspecting or updating the current dev environment, applying existing scoped schema changes, applying required runtime metadata, restarting a local service, or running targeted checks. Confirm only clearly high-risk or out-of-scope actions, including database deletion/rebuild, bulk data deletion, production or real-production-credential changes, force push, remote push, or broad architectural rewrites.
- Complete only the current task. Do not add unrelated refactors, dependency modernization, security campaigns, cleanup, documentation campaigns, or the next phase.

## Validation

- Validate targeted first: affected tests, lint, typecheck, build, backend import/route checks, and necessary development-environment checks.
- Do not default to full backend/repository regression, broad audits, unrelated tests, or release-readiness suites. Use full regression only when explicitly requested, performing a baseline/release lock, changing shared Core with inadequate targeted coverage, or when targeted checks show clear cross-module impact; state the reason first.
- Stop when the current goal and minimum necessary validation are complete.

## Starter Development Database & Completion Policy

- The shared development database is `fastapiadmin_phase3_fresh`; it is the real Starter development runtime baseline. Iterate there instead of creating a fresh, temporary, validation, or per-phase database for ordinary module, table, field, Generator, or feature work. Isolated SQLite/FakeRedis fixtures may support tests but must not replace this baseline.
- The default Starter workflow is: update Model/Schema → update the current dev database → apply required runtime metadata → run targeted runtime verification → complete. Do not mechanically require a new migration, temporary database, upgrade/downgrade test, SQLite migration smoke, or migration idempotency test for every schema change.
- Alembic migrations remain available when there is an actual need: the user requests migration work; a baseline/release is being locked; a shared-test, pre-production, production, or controlled deployment needs reproducible upgrades; or important data preservation, multiple environments, or backward compatibility must be proven. Do not generate migrations merely for ceremony.
- Existing development migrations are preserved as-is during ordinary work: do not delete, squash, rewrite, or renumber them. Reassess migration history, a clean initial schema baseline, or a formal upgrade starting point later at Starter Baseline Lock.
- A feature is complete in an available dev environment only when code is complete, the current dev database is updated, required runtime metadata is applied, and targeted runtime verification passes. Runtime metadata includes applicable menus, permissions, dictionaries, seed data, Generator metadata, and runtime configuration; source files or unit tests alone do not prove the live development loop is complete.
- If the current dev environment is unavailable, do not create a substitute database or environment just to claim completion. Complete safe code/static/unit validation when possible and report `CODE: COMPLETE`, `DEV ENVIRONMENT: NOT APPLIED`, and `RUNTIME VERIFICATION: PENDING`. If the environment can be started within scope, start it and continue without reconfirmation.
- Preserve unrelated WIP: do not modify, revert, clean, or commit it. Continue the scoped task when changes can remain isolated.

## Git

- Local commits are allowed for ordinary development. Do not push by default; never force-push. Stage only files belonging to the current task and preserve unrelated WIP.
