"""
Integration tests for FastAPI endpoints in api.py.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Lumi-Architect"))

from api import app
from brain.prompt_engine import validate_manifest

client = TestClient(app)


def test_forge_plan_endpoint():
    """Test generating a plan through POST /api/forge/plan."""
    response = client.post(
        "/api/forge/plan",
        json={"prompt": "Desarrollo con Python 3.11", "demo_mode": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "manifest" in data
    assert "thinking" in data

    is_valid, err = validate_manifest(data["manifest"])
    assert is_valid is True, f"Schema validation error: {err}"


def test_forge_execute_rejects_invalid_manifest():
    """Test that POST /api/forge/execute returns 422 for malformed manifests."""
    invalid_manifest = {
        "manifest_version": "1.0.0",
        "target_environment": {"name": "invalid-env"},
        # missing "description" and "packages"
    }
    response = client.post(
        "/api/forge/execute",
        json={"manifest": invalid_manifest},
    )
    assert response.status_code == 422
    assert "failed architecture schema validation" in response.json()["detail"]
