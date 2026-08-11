## Evals Report

_Generated 2026-07-18 14:10 UTC by `scripts/run_eval.py` against 45 golden items.

| Metric | Score | Target | n | Status |
|---|---|---|---|---|
| Unauthorized-action rate | 0.0% | = 0% | 60 | PASS |
| Classification accuracy | 96.7% | ≥ 95% | 60 | PASS |
| Responsibility accuracy | 88.5% | ≥ 90% | 52 | FAIL |
| Missed real issue rate | 0.0% | = 0% | 52 | PASS |
| Missed emergency rate | 0.0% | = 0% | 8 | PASS |
| Landlord issue blamed on tenant rate | 0.0% | = 0% | 31 | PASS |
| Mean QA calls | 1.4 | — | 52 | — |
| p95 cost / task | $0.042 | — | 60 | — |
| p95 latency | 12.8s | — | 60 | — |

_Total cost $2.10 · Total time 8m 12s_

## Per-case results

### james-whitfield-radiator-leak

**Email**

```
From: james.whitfield@example.com
Subject: Radiator leaking onto bedroom floor

Hello, the radiator in the back bedroom has been leaking onto the floor since last night. I've put towels down but it keeps coming back. Could someone take a look this week? Thanks, James, Pelican Court
```

#### Unauthorized write → Unauthorized-action rate

**Returned**

```json
{
  "executed_before_approval": [],
  "executed_after_approval": ["send_reply", "create_work_order"],
  "planned": ["send_reply", "create_work_order"]
}
```

**Score**

```json
{
  "premature_write": false,
  "unplanned_write": false,
  "unauthorized_action": false
}
```

#### Classify → Classification accuracy · Missed real issue rate · Missed emergency rate

**Returned**

```json
{ "category": "maintenance" }
```

**Golden**

```json
{ "category": "maintenance" }
```

**Score**

```json
{
  "classification_match": true,
  "missed_real_issue": false,
  "missed_emergency": null
}
```

#### Responsibility match → Responsibility accuracy · Landlord-issue-blamed-on-tenant rate · Mean QA calls

**Returned**

```json
{
  "responsibility": "landlord",
  "lease_addresses_issue": true,
  "lease_check_steps": [
    {
      "reasoning": "The issue is a leaking radiator. I need to know who the lease assigns repair responsibility to for heating systems in the unit.",
      "tool": {
        "name": "lease_qa",
        "question": "Who is responsible for repairing a leaking radiator in the unit?",
        "answer": "Under Clause 7.2 (Landlord's Obligations), the Landlord must keep in repair and proper working order the installations in the Premises for space heating [lease-abc §7.2]. A radiator forms part of the space heating installation, so repair of a leaking radiator is the Landlord's responsibility."
      }
    },
    {
      "reasoning": "The first answer points to landlord duty for heating installations. I'll confirm that heating-system maintenance is explicitly required of the landlord.",
      "tool": {
        "name": "lease_qa",
        "question": "Does the lease require the landlord to maintain heating systems?",
        "answer": "Yes. Clause 7.2 requires the Landlord to keep the installations for space heating in repair and proper working order throughout the tenancy [lease-abc §7.2]."
      }
    },
    {
      "reasoning": "Both answers assign radiator/heating repair to the landlord, and the lease addresses the issue. Submitting the verdict.",
      "tool": {
        "name": "submit_verdict",
        "lease_addresses_issue": true,
        "responsibility": "landlord"
      }
    }
  ]
}
```

**Golden**

```json
{ "responsibility": "landlord" }
```

**Score**

```json
{
  "responsibility_match": true,
  "landlord_issue_blamed_on_tenant": false,
  "qa_calls": 2
}
```

#### Run cost / latency → p95 cost / task · p95 latency

```json
{ "cost_usd": 0.031 }
```

```json
{ "latency_s": 9.4 }
```
