"""
Unit tests for the LLMClient fallback and schema compliance.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Lumi-Architect"))

from brain.llm_client import LLMClient
from brain.prompt_engine import extract_json_from_response, validate_manifest


def test_llm_client_fallback_generates_valid_schema():
    """Verify that the offline fallback produces schema-compliant manifests."""
    client = LLMClient()
    response = client.generate("system prompt", "Setup Python and Jupyter for Machine Learning")

    result = extract_json_from_response(response, validate_schema=True)
    assert result.success is True
    assert result.manifest is not None

    is_valid, err = validate_manifest(result.manifest)
    assert is_valid is True
    assert err is None
    assert any("Python" in p["display_name"] for p in result.manifest["packages"])


def test_llm_client_fallback_for_node():
    """Verify offline fallback correctly detects Node.js stacks."""
    client = LLMClient()
    response = client.generate("system prompt", "Fullstack React application with Node")

    result = extract_json_from_response(response, validate_schema=True)
    assert result.success is True
    assert any("Node" in p["display_name"] for p in result.manifest["packages"])
