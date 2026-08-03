# LeaseOps frontend

- no shared client cache — `cache: "no-store"` everywhere plus `force-dynamic`, so every
  page entry refetches
- dumb frontend: pages load, components render
- mocks confined to `lib/api.ts`

## The stream ↔ reload gap

`GET /runs/{email_id}` and `POST /runs/stream` do not agree on shape yet (api-todo.md
Checkpoint 2). Rather than let components branch on which source they got, both paths fold
into one `RunState` in `lib/run-state.ts`:

- reload → `fromRunDetail(data)`
- live → `applyStreamEvent(state, event)`, event by event

Three real discrepancies are handled there and documented in-file:

- **No run row on reload.** The endpoint returns email + steps + stats but no `RunStatus`,
  so gate state is derived from the email status instead.
- **`submit_verdict` is never emitted or persisted** — only its result lands on the step
  output. The design shows it as a tool row, so it is reconstructed from the real verdict
  fields on _both_ paths. `reasoning` stays null rather than invented.

The streamed run and the reloaded run render an identical timeline.

## Mocks

Both live in `lib/api.ts` and are marked `MOCK:`.

- `getBuildInfo()` — eval/version footer, explicitly later backend work.
- `senderDisplayName()` — the backend `sender` is a bare address; the design shows a name.

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000` — see `.env.example`.
`./dev.sh` needs no changes.
