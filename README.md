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
