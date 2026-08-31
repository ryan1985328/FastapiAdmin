# FastAPI Admin Starter — AI Development Rules

## Default mode

- Default to **Fast Iteration + Targeted Validation**. Daily development is not release validation.
- Read task-specific project docs when relevant. `docs/STARTER_CAPABILITY_BASELINE.md` remains the startup and baseline reference; its broad validation commands apply when doing a baseline/release check or when explicitly requested.

## Authorization and scope

- An explicit request to implement, develop, fix, continue, or “GOGO” authorizes ordinary local work within the task: read/write scoped files, required schema/data changes in the current development database, Generator runs, directly needed dependencies, local services, focused checks, and a local commit.
- Do not repeatedly ask for approval for those ordinary operations. Confirm only clearly high-risk or out-of-scope actions, including database deletion/rebuild, bulk data deletion, production or real-production-credential changes, force push, remote push, or broad architectural rewrites.
- Complete only the current task. Do not add unrelated refactors, dependency modernization, security campaigns, cleanup, documentation campaigns, or the next phase.

## Validation

- Validate targeted first: affected tests, lint, typecheck, build, backend import/route checks, and necessary development-environment checks.
- Do not default to full backend/repository regression, broad audits, unrelated tests, or release-readiness suites. Use full regression only when explicitly requested, performing a baseline/release lock, changing shared Core with inadequate targeted coverage, or when targeted checks show clear cross-module impact; state the reason first.
- Stop when the current goal and minimum necessary validation are complete.

## Database and WIP

- The shared development database is `fastapiadmin_phase3_fresh`; iterate there instead of creating a new database for each phase. Isolated SQLite/FakeRedis test fixtures are acceptable and must not replace the real development baseline.
- Preserve unrelated WIP: do not modify, revert, clean, or commit it. Continue the scoped task when changes can remain isolated.

## Git

- Local commits are allowed for ordinary development. Do not push by default; never force-push. Stage only files belonging to the current task and preserve unrelated WIP.
