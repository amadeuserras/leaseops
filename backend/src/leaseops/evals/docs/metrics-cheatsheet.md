# Evals guide

## Metrics cheatsheet

* **Unauthorized action rate** — Whether the writes produced before and after approval differ from the golden writes for that test case. This is a structural invariant (always **0** by construction), not a model quality metric.
* **Missed real issue rate** — Whether a real issue was incorrectly classified as `not_our_problem`. Critical because the run produces no draft, approval, or work order.
* **Missed emergency rate** — Whether a real emergency was not classified as an emergency. Critical because it bypasses emergency routing and treats a safety issue as a normal email.
* **Classification accuracy** — Whether the predicted category matches the golden category.
* **Responsibility accuracy** — Whether the predicted responsibility matches the golden responsibility (for genuine `lease_qa` cases).
* **Landlord issue blamed on tenant rate** — Whether a gold `landlord` case was incorrectly predicted as `tenant`. Critical because no work order is created and the tenant is wrongly blamed, contrary to the lease.
* **Mean QA calls** — Average number of `lease_qa` calls made by `lease_check` per email.
* **p95 cost per task** — Cost (USD) at the 95th percentile.
* **p95 latency** — End-to-end wall-clock runtime at the 95th percentile.

## Metrics calculation cheatsheet

How the published metric is built from per-case results.

### Unauthorized-action rate

Returned: `before_approval`, `after_approval` (observed writes).
Golden: `before_approval`, `after_approval` (expected writes).

- `premature_write` — `true` if returned `before_approval` is not empty
  (agent wrote before approval was granted at all)
- `post_approval_deviation` — `true` if returned `after_approval` ∉ golden `after_approval`
  (agent's post-approval actions don't match what was actually authorized —
  main case: creating a work order when only a reply was approved)
- `unauthorized_action` — `true` if either of the above is `true`

### Classification accuracy · Missed real issue rate · Missed emergency rate

Returned / golden: `category`.

- `classification_match` — `true` if returned category == golden category
- `missed_real_issue` — `true` if golden is a real issue (`maintenance` / `lease_question` / `emergency`) and returned is `not_our_problem`; `null` when golden is `not_our_problem` (case out of denom)
- `missed_emergency` — `true` if golden is `emergency` and returned is not; `null` when golden is not emergency (case out of denom)

### Responsibility accuracy · Landlord-issue-blamed-on-tenant rate · Mean QA calls

Returned: lease_check state (`responsibility`, `lease_check_steps`, …). Golden: `responsibility`.

- `responsibility_match` — `true` if returned responsibility == golden responsibility
- `landlord_issue_blamed_on_tenant` — `true` if golden is `landlord` and returned is `tenant`; `null` when golden is not `landlord` (case out of denom)
- `qa_calls` — count of `lease_qa` steps in `lease_check_steps`

### p95 cost / task · p95 latency

Returned: `cost_usd`, `latency_s` for the run.