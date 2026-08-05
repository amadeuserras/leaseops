from __future__ import annotations

import math

from leaseops.evals.types import CaseResult, GlobalMetrics


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    n = len(values)
    idx = min(max(0, math.ceil(0.95 * n) - 1), n - 1)
    return sorted(values)[idx]


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values) if values else 0.0


def unauthorized_action_rate(results: list[CaseResult]) -> tuple[float, int]:
    values = [r.unauthorized_action for r in results]
    return _rate(values), len(values)


def classification_accuracy(results: list[CaseResult]) -> tuple[float, int]:
    values = [r.classification_match for r in results]
    return _rate(values), len(values)


def missed_real_issue_rate(results: list[CaseResult]) -> tuple[float, int]:
    values = [r.missed_real_issue for r in results if r.missed_real_issue is not None]
    return _rate(values), len(values)


def missed_emergency_rate(results: list[CaseResult]) -> tuple[float, int]:
    values = [r.missed_emergency for r in results if r.missed_emergency is not None]
    return _rate(values), len(values)


def responsibility_accuracy(results: list[CaseResult]) -> tuple[float, int]:
    values = [
        r.responsibility_match for r in results if r.responsibility_match is not None
    ]
    return _rate(values), len(values)


def landlord_issue_blamed_on_tenant_rate(
    results: list[CaseResult],
) -> tuple[float, int]:
    values = [
        r.landlord_issue_blamed_on_tenant
        for r in results
        if r.landlord_issue_blamed_on_tenant is not None
    ]
    return _rate(values), len(values)


def mean_qa_calls(results: list[CaseResult]) -> tuple[float, int]:
    values = [r.qa_calls for r in results if r.qa_calls is not None]
    mean = sum(values) / len(values) if values else 0.0
    return mean, len(values)


def p95_cost_per_task(results: list[CaseResult]) -> float:
    return _p95([r.cost_usd for r in results])


def p95_latency(results: list[CaseResult]) -> float:
    return _p95([r.latency_s for r in results])


def compute_globals(results: list[CaseResult]) -> GlobalMetrics:
    unauthorized_rate, unauthorized_n = unauthorized_action_rate(results)
    classification_acc, classification_n = classification_accuracy(results)
    missed_issue_rate, missed_issue_n = missed_real_issue_rate(results)
    missed_emerg_rate, missed_emerg_n = missed_emergency_rate(results)
    resp_acc, resp_n = responsibility_accuracy(results)
    landlord_rate, landlord_n = landlord_issue_blamed_on_tenant_rate(results)
    mean_qa, qa_n = mean_qa_calls(results)

    return GlobalMetrics(
        unauthorized_rate=unauthorized_rate,
        unauthorized_n=unauthorized_n,
        classification_acc=classification_acc,
        classification_n=classification_n,
        missed_issue_rate=missed_issue_rate,
        missed_issue_n=missed_issue_n,
        missed_emerg_rate=missed_emerg_rate,
        missed_emerg_n=missed_emerg_n,
        resp_acc=resp_acc,
        resp_n=resp_n,
        landlord_rate=landlord_rate,
        landlord_n=landlord_n,
        mean_qa=mean_qa,
        qa_n=qa_n,
        p95_cost=p95_cost_per_task(results),
        p95_latency=p95_latency(results),
        total_n=len(results),
    )
