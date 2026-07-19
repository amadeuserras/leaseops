from __future__ import annotations

import pytest
from pydantic import ValidationError

from leaseops.models.schemas import HealthResponse, LeaseOpsModel


def test_health_response_defaults() -> None:
    assert HealthResponse().status == "ok"
    assert HealthResponse().service == "leaseops"


def test_leaseops_model_forbids_extra_fields() -> None:
    class Probe(LeaseOpsModel):
        name: str

    with pytest.raises(ValidationError):
        Probe(name="ok", unexpected="nope")  # type: ignore[call-arg]
