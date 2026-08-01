# LeaseOps

An AI agent that runs a property manager's maintenance inbox — reads tenant emails, checks the lease (via LeaseClear over MCP), drafts the reply, creates the work order, and escalates to a human when it isn't sure.

## Local setup

LeaseClear must sit next to this repo (`../leaseclear`).

```bash
# Clone both next to each other
git clone https://github.com/amadeuserras/leaseclear.git
git clone https://github.com/amadeuserras/leaseops.git
cd leaseops

# From backend
cp .env.example .env   # fill API keys
uv sync

# From frontend
npm install

# From root
./dev.sh
```

- LeaseOps API: http://localhost:8000
- LeaseClear API: http://localhost:8001
- Frontend: http://localhost:3000

## MCP Inspector

From `backend/`, run the MCP server with the Inspector (opens in the browser):

```bash
uv run mcp dev src/leaseops/mcp/server.py
```

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
│       ├── mcp/                  # MCP server + tool implementations
│       ├── api/                  # FastAPI, SSE trace streaming
│       ├── db/                   # SQLAlchemy 2.0 async
│       ├── models/               # Pydantic boundary schemas
│       └── evals/                # golden set, trajectory harness
├── frontend/                     # Next.js + TS + Tailwind
├── METRICS.md
├── SPEC.md
└── README.md
```
