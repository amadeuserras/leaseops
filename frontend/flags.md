# LeaseOps frontend

Three screens over the LeaseOps agent API: **Inbox**, **Runs** (live trace viewer), **Approvals**.

## Layout

| Path                           | What it is                                             |
| ------------------------------ | ------------------------------------------------------ |
| `app/inbox`                    | Seeded messages; clicking one starts a run             |
| `app/runs/[emailId]`           | Live SSE trace — nodes, tool calls, citations, cost    |
| `app/approvals`                | Pending actions with approve / reject-with-reason      |
| `lib/api.ts`                   | Every API call, plus the mocks listed below            |
| `components/runs-provider.tsx` | Folds trace events into run state; survives navigation |

## What is mocked, and why

Flagged inline in `lib/api.ts` under the `MOCKED DATA` banner:

- **`listTenants()`** — there is no `/tenants` endpoint, so a sender address cannot be
  resolved to a display name and unit. Mirrors `backend/seed_data/tenants.json`. Unknown
  senders fall back to a name derived from the address.
- **`getBuildInfo()`** — the sidebar's eval count and build stamp. `/evals` is postponed
  (SPEC Ch. 8) and no build endpoint exists.
- **`reasoning` on `tool_call` events** — the trace shows a sentence above each tool call
  explaining why the agent reached for it. `ToolCallEvent` has no such field, so `parseEvent`
  backfills a canned line per tool from `mockedReasoning`. Everything else on the event is
  the real payload, and a `reasoning` sent by the API passes straight through untouched —
  so the field can be added backend-side with no frontend change, and `mockedReasoning`
  then deleted.

## API gaps worked around in the UI (not mocked — no data was invented)

- **No run history.** `POST /runs/stream` is the only way to get a trace; there is no
  `GET /runs` or `GET /runs/{id}`. A trace is therefore only visible while its run streams
  in the current session. Opening a message with no session run shows an empty state with a
  **Run agent** button rather than fabricated history.
- **Email urgency is not persisted.** It only exists in the `extract` node's output, so the
  inbox shows `—` until that message has been run.
- **`EmailStatus` has three values** (`pending`/`processed`/`escalated`) but the design
  needs five. _Running_ and _Awaiting approval_ are derived from live run state and the
  `/approvals` list; the rest map straight from the API.
- **Auto-run guard.** A message runs automatically only when its status is `pending` and no
  run exists for it this session; anything else needs an explicit **Run agent** / **Replay**
  click, so the agent is never fired twice by accident.
- **Resuming after approval is not streamed.** Approving from the queue calls
  `POST /approvals/{run_id}/approve`, but that run's SSE stream has already closed, so the
  outcome is reflected from the approvals state rather than from new trace events.
