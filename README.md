# Pulse — Uptime Monitor

A small full-stack app that pings a list of URLs on a schedule and shows whether each one is
up or down, with response time and history.

**Stack:** FastAPI + SQLAlchemy + SQLite + APScheduler (backend) · React + Vite, served via Nginx
(frontend) · Docker Compose (orchestration).

## 1-line setup

```bash
docker compose up --build
```

- **Backend** — `http://localhost:8000` (interactive API docs at `/docs`)
- **Frontend** — `http://localhost:3000` (dashboard)

The SQLite file (`backend/uptime.db`) lives on a bind mount to your host filesystem, so your
monitored URLs and check history survive container restarts.

## How it works

- **Backend** (`/backend`): a FastAPI service backed by SQLite via SQLAlchemy. On startup, and
  then every 60 seconds, an APScheduler job pings every registered URL and writes one row per
  check (status code, response time in ms, up/down flag, timestamp) to a `health_checks` table.
  Adding a URL also triggers an immediate check, so the dashboard doesn't sit at "unknown" for a
  full minute.
- **Frontend** (`/frontend`): a single-page React app that polls `GET /urls/` every 8 seconds and
  renders a status board — a pulsing dot for UP/DOWN/PENDING, HTTP status code, response time,
  and "last checked" relative time. You can add a URL, force an immediate re-check, or stop
  monitoring one, all from the UI.
- Nginx in the frontend container serves the built static assets and reverse-proxies `/urls` and
  `/api` to the backend container, so the browser only ever talks to one origin.

## API reference (also browsable at `/docs`)

| Method | Path                     | Description                                             |
|--------|--------------------------|----------------------------------------------------------|
| GET    | `/urls/`                 | List monitored URLs with their latest check              |
| POST   | `/urls/`                 | Register a new URL (`{"url": "..."}`) — runs an immediate check; 409 if already registered |
| DELETE | `/urls/{id}`             | Stop monitoring a URL                                    |
| GET    | `/urls/{id}/history`     | Last 50 checks for a URL                                 |
| POST   | `/urls/{id}/check-now`   | Force an immediate re-check                              |
| GET    | `/api/health`            | Liveness check                                           |

## Testing steps — verify UP and DOWN detection

1. Start the stack: `docker compose up --build`
2. Open `http://localhost:3000`
3. Add a **healthy** URL: type `https://example.com` and click **Add URL**. Within a couple of
   seconds it should show a green **UP** pill, an HTTP status code (200), and a response time.
4. Add a **broken** URL: type `https://this-domain-does-not-exist-abcxyz123.com` and click
   **Add URL**. It should show a red **DOWN** pill with no status code — the request never got a
   response (DNS/connection failure), which is different from a reachable server returning an
   error code.
5. Click the **↻** button on either row to force an immediate re-check without waiting for the
   next scheduled cycle.
6. Or hit the API directly:
   ```bash
   curl http://localhost:8000/urls/
   curl http://localhost:8000/urls/1/history
   ```

## Deployment sketch (light)

For a real deployment I'd keep the two-container shape but move state out of the container and
put a managed load balancer in front:

- **Backend** → a small container service (e.g. AWS ECS Fargate). Swap SQLite for a managed
  Postgres instance (e.g. RDS) once there's more than one backend replica — SQLite doesn't
  handle concurrent writers across hosts well.
- **Frontend** → static build output pushed to S3 + served through CloudFront, rather than
  running Nginx in a container in production.
- **Scheduler** → in-process APScheduler is fine at this MVP scale (a few dozen URLs, checked
  every minute). At real scale, I'd pull the periodic check into its own worker (an ECS
  scheduled task or a Lambda on an EventBridge cron) so it's not competing with the API process
  for resources.

A hypothetical Terraform sketch (illustrative, not production-hardened):

```hcl
resource "aws_ecs_cluster" "pulse" {
  name = "pulse-uptime-monitor"
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "pulse-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  container_definitions = jsonencode([{
    name  = "backend"
    image = "<ecr-repo>/pulse-backend:latest"
    portMappings = [{ containerPort = 8000 }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql://..." }
    ]
  }])
}

resource "aws_db_instance" "pulse" {
  engine            = "postgres"
  instance_class    = "db.t4g.micro"
  allocated_storage = 20
}

resource "aws_s3_bucket" "frontend" {
  bucket = "pulse-frontend-static"
}

resource "aws_cloudfront_distribution" "frontend" {
  # origin = aws_s3_bucket.frontend, default_root_object = "index.html"
}

resource "aws_lb" "backend" {
  name               = "pulse-backend-alb"
  load_balancer_type = "application"
}
```

## AI collaboration

See `AI_LOG.md` for the tools used, the prompts that shipped it, and the course corrections
(there were two real ones, both caught by actually running the code rather than assuming it
worked).
