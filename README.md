# LeaseOps

An AI agent that runs a property manager's maintenance inbox — reads tenant emails, checks the lease (via LeaseClear over MCP), drafts the reply, creates the work order, and escalates to a human when it isn't sure.

## Local setup

```bash
# Backend
cd backend
cp .env.example .env
uv sync

# Start
cd ..
./dev.sh
```

Frontend: http://localhost:3000  
API: http://localhost:8000

## Tests

```bash
docker compose up -d
cd backend
uv sync
uv run pytest
```

## Database migrations (Alembic)

Postgres must be running (`docker compose up -d` or `./dev.sh`). From `backend/`:

1. Edit the SQLAlchemy model in `src/leaseops/db/models.py` (new table = new class; also import it in `alembic/env.py`).
2. Generate a migration: `uv run alembic revision --autogenerate -m "short description"`
3. Review the file under `alembic/versions/` (autogenerate is a draft — fix it if needed).
4. Apply: `uv run alembic upgrade head`
5. Check: `uv run python scripts/preview.py`

Useful: `uv run alembic current` · `uv run alembic history` · `uv run alembic downgrade -1`

## Repo layout

```
leaseops/
├── backend/
│   ├── pyproject.toml            # uv
│   ├── alembic/                  # SQLAlchemy migrations
│   └── src/leaseops/
│       ├── agent/                # LangGraph graph, nodes, state
│       ├── policy/               # decide rules, whitelist, caps
│       ├── mcp/                  # MCP server + tool implementations
│       ├── api/                  # FastAPI, SSE trace streaming
│       ├── db/                   # SQLAlchemy 2.0 async
│       ├── models/               # Pydantic boundary schemas
│       └── evals/                # golden set, trajectory harness
├── frontend/                     # Next.js (Ch. 9)
├── METRICS.md
├── SPEC.md
└── README.md
```
