"""Phase 0 smoke tests: the app boots, health responds, and the release gates fire."""

from __future__ import annotations

import pytest

from tender_intel.core.config import (
    INSECURE_JWT_SECRET,
    Environment,
    Settings,
    enforce_release_gates,
)


async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_cors_origins_parsed_from_csv():
    s = Settings(cors_allow_origins="http://a.com, http://b.com")  # type: ignore[arg-type]
    assert s.cors_allow_origins == ["http://a.com", "http://b.com"]


def test_release_gate_rejects_default_jwt_secret_in_production():
    s = Settings(environment=Environment.PRODUCTION, jwt_secret=INSECURE_JWT_SECRET)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        enforce_release_gates(s)


def test_release_gate_rejects_wildcard_cors_in_production():
    s = Settings(
        environment=Environment.PRODUCTION,
        jwt_secret="a-sufficiently-long-production-secret-value",
        cors_allow_origins=["*"],
    )
    with pytest.raises(RuntimeError, match="CORS_ALLOW_ORIGINS"):
        enforce_release_gates(s)


def test_release_gate_passes_local():
    enforce_release_gates(Settings(environment=Environment.LOCAL))
