# AI Collaboration Log

## AI tech stack

- **Claude (Claude Sonnet 5, via claude.ai)** — used throughout: initial architecture
  planning, debugging the backend after a hand-written rewrite broke it, and building the
  entire frontend (React/Vite dashboard, CSS design system, Nginx + Docker setup).
- Claude's own code execution environment was used to actually clone the repo, run the FastAPI
  server, and reproduce every bug with a real traceback before proposing a fix — not just
  reading the code and guessing.

My background is backend/ML-heavy; the frontend, Nginx, and Docker plumbing were the deliberate
"stretch" parts of this exercise, per the assignment's own framing. The backend architecture
(SQLAlchemy models, a `routers/` + `crud/` + `services/` split instead of one flat `main.py`)
is mine — I restructured Claude's original single-file draft into something closer to how I'd
organize a real FastAPI project, then broke it in the process.

## The prompts that shipped it

1. Initial ask, with the full assignment brief pasted in: *"i have to make this project for
   this role."* → Claude produced a first working single-file backend (FastAPI + SQLite +
   APScheduler), verified it end-to-end in its own sandbox before handing it over.
2. I took that as a reference and rewrote the backend myself with a proper `app/` package
   structure (`models.py`, `schemas.py`, `crud.py`, `routers/urls.py`, `services/ping.py`,
   `scheduler.py`) — and introduced two real bugs in the process.
3. *"only the backend is done. and i changed logic alot so its broken can u take a look"* +
   repo link → Claude cloned the repo, ran it, and reproduced two separate crashes with full
   tracebacks rather than eyeballing the diff.
4. *"give me the code"* (for the fixes) + *"what else is missing"* → Claude handed back
   corrected versions of every touched file, matching my existing structure and import paths,
   plus a full gap list against the assignment brief (empty README, no root `.gitignore`, no
   `AI_LOG.md`, no Dockerfile, no frontend).
5. Pasted a fresh terminal log after applying the fixes locally, showing what looked like the
   same error still happening → Claude read the log carefully and pointed out the crash had
   actually changed (a `UNIQUE constraint failed` on a duplicate URL, not the original
   `AttributeError`) and that the fix had worked — the old traceback lines in the log were from
   scheduler ticks that ran before the fix was saved and the server reloaded.
6. *"everything is working lets do the missing stuff"* → Claude built the frontend against the
   exact API shape already in place (`/urls/`, `/urls/{id}/history`, `/urls/{id}/check-now`),
   plus the root README, this log, `.gitignore`, and the frontend Dockerfile/Nginx config —
   and ran `npm run build` to confirm it compiles before handing it over.

## Course corrections

**#1 — wrong import path.** After I restructured the backend into a package, `scheduler.py`
still had `from app.ping import check_url`, but the ping logic had moved to
`app/services/ping.py`. This crashed the app on import — `uvicorn` never got past startup.
Claude caught this by actually running `uvicorn app.main:app` in its own sandbox and reading the
`ModuleNotFoundError` traceback, rather than assuming the code was fine because it looked
structurally reasonable.

**#2 — relationship attribute vs. foreign-key column.** `crud.save_health_check` built the new
`HealthCheck` row with `models.HealthCheck(url=url_id, ...)`. `url` is the SQLAlchemy
*relationship* (expects a `URL` object); `url_id` is the actual foreign-key column. Passing a
raw integer into `url` throws `AttributeError: 'int' object has no attribute
'_sa_instance_state'` the moment SQLAlchemy tries to treat it as a related object — and it only
surfaces once the scheduler actually tries to save a check, not at import time, so it's the kind
of bug that's easy to miss without running the periodic job end-to-end. Claude let the scheduler
run for a full 60+ second cycle in its sandbox to force the bug to fire, then fixed it to
`url_id=url_id`.

**A near-miss worth noting:** after applying the fix, a fresh terminal log still *looked* like
the same failure at first glance — same file, same function, same `AttributeError` text
repeated several times. It actually wasn't: those repeats were stale scheduler ticks from before
the file was saved and Uvicorn's `--reload` picked up the change. The real new error after the
reload was a `sqlite3.IntegrityError: UNIQUE constraint failed: urls.url` — a duplicate URL
being re-added, an entirely different (and much more mundane) problem. The lesson: when a log
shows a "recurring" error, check the timestamps and what triggered each occurrence before
assuming the same fix failed twice.

## Reflection

AI significantly accelerated scaffolding and frontend development, but the project still required iterative debugging, architecture decisions, and manual refactoring. The most valuable workflow was treating AI as a pair programmer—using it to generate a starting point, then validating, restructuring, and testing the code until it matched the intended design.