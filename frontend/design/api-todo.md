# API todo (v7) — remaining

Inbox: done.

---

## Checkpoint 1 — Reloadable Runs screen

Plain English: after a run finishes (or pauses), open the email and see the full agent timeline again — same steps, tool calls, and cost footer — without needing a live stream.

**Plain English for Checkpoint 1** — after a run finishes, reopen the email and see the same timeline again.

1. **`GET /runs/{email_id}` — run + email + steps**  
   One API call that returns everything the Runs screen needs: the original email, the run record, and every step.

2. **Typed step `output` per node**  
   Each step’s result has a known shape for that node (classify, extract, lease_check, etc.) — not a vague “blob of JSON.”

3. **Persist `lease_check` tool calls**  
   Save the lease Q&A expanders (why it asked, what it asked, answers, citations, verdict) so they show up again on reload — not only while watching live.

4. **Persist per-step `model`, `input_tokens`, `output_tokens`, `cost_usd`** ✅  
   Remember which model ran each step and how many tokens / how much money it cost, broken out clearly.

5. **Step statuses incl. approval `paused` / `skipped` / `completed`**  
   Each step knows if it finished, is waiting on you, or was skipped — especially the approval gate.

6. **Run aggregates: `tokens`, `cost`, `elapsed`, `step_count`**  
   The footer totals (tokens, $, time, number of steps) come from the API for the whole run, not pieced together by the UI.

## Checkpoint 2 — Live Runs = reload shape

Plain English: watching a run live should look identical to reloading it later — same event shapes, tool expanders filling in as they happen, and a clear jump to Approvals when the gate pauses.

- [ ] Align `POST /runs/stream` SSE with Checkpoint 1 step/tool shape
- [ ] Stream `tool_call` / `tool_result` into the timeline while `lease_check` runs
- [ ] Approval gate payload includes `run_id` + `email_id` (deep-link to Approvals)

## Checkpoint 3 — Approvals polish

Plain English: the approvals list and approve/reject path mostly work; this pass is checking the card matches the design and settling reject vs mark-complete.

Already have: `GET /approvals`, `POST .../approve`, `POST .../reject`, execute-on-approve.

- [ ] Confirm card fields vs v7 (`appliance_or_system` as issue type, `citation`, `actions`)
- [ ] Decide: reject reason body or drop reject from UI
- [ ] Skip server-side filters (client-side fine)

## Later / optional

- [ ] Denormalize extract fields onto email (stop joining step JSON for inbox)
- [ ] Auth / “approved by” on completed gate
- [ ] Eval / version footer APIs
