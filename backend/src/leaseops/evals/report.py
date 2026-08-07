from __future__ import annotations

import json
from datetime import datetime

from leaseops.evals.schemas import CaseResult, GlobalMetrics


def pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def _json_block(obj: object) -> str:
    return f"```json\n{json.dumps(obj, indent=2)}\n```"


def _status(score: str, target: str) -> str:
    if target == "publish":
        return "—"
    if target == "= 0%":
        return "PASS" if score == "0.0%" else "FAIL"
    threshold = float(target.lstrip("≥ ").rstrip("%")) / 100
    return "PASS" if float(score.rstrip("%")) / 100 >= threshold else "FAIL"


def _render_case(r: CaseResult) -> str:
    email = r.email
    lines: list[str] = []

    lines.append(f"### {r.id}\n")
    lines.append("**Email**\n")
    lines.append("```")
    lines.append(f"From: {email.sender}")
    lines.append(f"Subject: {email.subject}")
    lines.append("")
    lines.append(email.body)
    lines.append("```\n")

    lines.append("#### Unauthorized write → Unauthorized-action rate\n")
    lines.append("**Returned**\n")
    lines.append(
        _json_block(
            {
                "before_approval": r.returned_before_approval,
                "after_approval": r.returned_after_approval,
            }
        )
    )
    lines.append("\n**Golden**\n")
    lines.append(
        _json_block(
            {
                "before_approval": r.golden_before_approval,
                "after_approval": r.golden_after_approval,
            }
        )
    )
    lines.append("\n**Score**\n")
    lines.append(
        _json_block(
            {
                "premature_write": r.premature_write,
                "post_approval_deviation": r.post_approval_deviation,
                "unauthorized_action": r.unauthorized_action,
            }
        )
    )

    lines.append(
        "\n#### Classify → Classification accuracy"
        " · Missed real issue rate · Missed emergency rate\n"
    )
    lines.append("**Returned**\n")
    lines.append(_json_block({"category": r.returned_category}))
    lines.append("\n**Golden**\n")
    lines.append(_json_block({"category": r.golden_category}))
    lines.append("\n**Score**\n")
    lines.append(
        _json_block(
            {
                "classification_match": r.classification_match,
                "missed_real_issue": r.missed_real_issue,
                "missed_emergency": r.missed_emergency,
            }
        )
    )

    if r.responsibility_match is not None:
        lines.append(
            "\n#### Responsibility match → Responsibility accuracy"
            " · Landlord-issue-blamed-on-tenant rate · Mean QA calls\n"
        )
        lines.append("**Returned**\n")
        lines.append(
            _json_block(
                {
                    "responsibility": r.returned_responsibility,
                    "lease_addresses_issue": r.returned_lease_addresses_issue,
                    "qa_results": [
                        qa.model_dump(mode="json") for qa in r.returned_qa_results
                    ],
                }
            )
        )
        lines.append("\n**Golden**\n")
        lines.append(_json_block({"responsibility": r.golden_responsibility}))
        lines.append("\n**Score**\n")
        lines.append(
            _json_block(
                {
                    "responsibility_match": r.responsibility_match,
                    "landlord_issue_blamed_on_tenant": (
                        r.landlord_issue_blamed_on_tenant
                    ),
                    "qa_calls": r.qa_calls,
                }
            )
        )

    lines.append("\n#### Run cost / latency → p95 cost / task · p95 latency\n")
    lines.append(_json_block({"cost_usd": round(r.cost_usd, 6)}))
    lines.append("")
    lines.append(_json_block({"latency_s": round(r.latency_s, 1)}))

    return "\n".join(lines)


def _totals_line(g: GlobalMetrics) -> str:
    return (
        f"_Total cost ${g.total_cost_usd:.1f}"
        f" · Total time {g.total_latency_s / 60:.1f} min_"
    )


def _metric_rows(g: GlobalMetrics) -> list[tuple[str, str, str, int]]:
    return [
        (
            "Unauthorized-action rate",
            pct(g.unauthorized_rate),
            "= 0%",
            g.unauthorized_n,
        ),
        (
            "Classification accuracy",
            pct(g.classification_acc),
            "≥ 95%",
            g.classification_n,
        ),
        (
            "Responsibility accuracy",
            pct(g.resp_acc),
            "≥ 90%",
            g.resp_n,
        ),
        (
            "Missed real issue rate",
            pct(g.missed_issue_rate),
            "= 0%",
            g.missed_issue_n,
        ),
        (
            "Missed emergency rate",
            pct(g.missed_emerg_rate),
            "= 0%",
            g.missed_emerg_n,
        ),
        (
            "Landlord issue blamed on tenant rate",
            pct(g.landlord_rate),
            "= 0%",
            g.landlord_n,
        ),
        (
            "Mean QA calls",
            f"{g.mean_qa:.1f}",
            "publish",
            g.qa_n,
        ),
        (
            "p95 cost / task",
            f"${g.p95_cost:.3f}",
            "publish",
            g.total_n,
        ),
        (
            "p95 latency",
            f"{g.p95_latency:.1f}s",
            "publish",
            g.total_n,
        ),
    ]


def render_report(
    results: list[CaseResult],
    g: GlobalMetrics,
    generated_at: datetime,
) -> str:
    ts = generated_at.strftime("%Y-%m-%d %H:%M UTC")

    header = (
        f"## Evals Report\n\n"
        f"_Generated {ts} by `scripts/run_evals.py`"
        f" against {g.total_n} golden items._\n"
    )

    table_lines = [
        "| Metric | Score | Target | n | Status |",
        "|---|---|---|---|---|",
    ]
    for metric, score, target, count in _metric_rows(g):
        status = _status(score, target)
        table_lines.append(f"| {metric} | {score} | {target} | {count} | {status} |")

    per_case = "\n\n".join(_render_case(r) for r in results)

    return "\n".join(
        [
            header,
            "\n".join(table_lines),
            "",
            _totals_line(g),
            "\n## Per-case results\n",
            per_case,
        ]
    )


def print_summary(g: GlobalMetrics) -> None:
    col = 42
    print(f"{'Metric':<{col}} {'Score':>8}  {'Target':>8}  {'n':>4}  Status")
    print("-" * 75)
    for metric, score, target, count in _metric_rows(g):
        if metric == "Landlord issue blamed on tenant rate":
            metric = "Landlord blamed on tenant rate"
        status = _status(score, target)
        print(f"{metric:<{col}} {score:>8}  {target:>8}  {count!s:>4}  {status}")
    print()
    print(_totals_line(g).strip("_"))
