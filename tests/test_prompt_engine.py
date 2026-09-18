"""
Unit tests for Lumi: Architect Prompt Engine and JSON Schema Validation.
"""

import pytest
import sys
from pathlib import Path

# Add Lumi-Architect to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Lumi-Architect"))

from brain.prompt_engine import (
    PromptEngine,
    extract_json_from_response,
    validate_manifest,
    build_user_prompt,
)


@pytest.fixture
def valid_manifest():
    return {
        "manifest_version": "1.0.0",
        "target_environment": {
            "name": "fullstack-node-react",
            "description": "Fullstack Node.js and React environment",
            "inferred_languages": ["JavaScript", "TypeScript"],
            "inferred_frameworks": ["React", "Express"],
        },
        "packages": [
            {
                "package_id": "Git.Git",
                "display_name": "Git",
                "package_manager": "winget",
                "version_requirement": "latest",
                "version_check_command": "git --version",
                "installation_flags": ["--silent"],
                "priority_level": 10,
                "is_critical": True,
                "depends_on": [],
                "category": "tool",
            },
            {
                "package_id": "OpenJS.NodeJS.LTS",
                "display_name": "Node.js LTS",
                "package_manager": "winget",
                "version_requirement": "latest",
                "version_check_command": "node --version",
                "installation_flags": ["--silent"],
                "priority_level": 20,
                "is_critical": True,
                "depends_on": [],
                "category": "runtime",
            },
        ],
        "environment_variables": [],
        "post_install_commands": [],
        "ai_reasoning": "Standard fullstack environment with Git and Node.js.",
    }


def test_validate_manifest_success(valid_manifest):
    """Ensure a properly formed manifest passes JSON Schema validation."""
    is_valid, error = validate_manifest(valid_manifest)
    assert is_valid is True
    assert error is None


def test_validate_manifest_missing_version_check_command(valid_manifest):
    """Ensure omitting version_check_command fails schema validation."""
    del valid_manifest["packages"][0]["version_check_command"]
    is_valid, error = validate_manifest(valid_manifest)
    assert is_valid is False
    assert "version_check_command" in error


def test_validate_manifest_invalid_package_manager(valid_manifest):
    """Ensure unsupported package manager values (e.g., brew on Windows) fail."""
    valid_manifest["packages"][0]["package_manager"] = "brew"
    is_valid, error = validate_manifest(valid_manifest)
    assert is_valid is False
    assert "brew" in error


def test_extract_json_from_response_with_thinking():
    """Test extracting both thinking and manifest blocks from an LLM response."""
    sample_response = """
```thinking
Step A - Stack Analysis: Python data science stack.
Step B - Dependencies: Python 3.11, Git.
```

```json
{
  "manifest_version": "1.0.0",
  "target_environment": {
    "name": "python-ds",
    "description": "Data Science with Python",
    "inferred_languages": ["Python"],
    "inferred_frameworks": ["Pandas"]
  },
  "packages": [
    {
      "package_id": "Python.Python.3.11",
      "display_name": "Python 3.11",
      "package_manager": "winget",
      "version_requirement": "3.11",
      "version_check_command": "python --version",
      "installation_flags": ["--silent"],
      "priority_level": 15,
      "is_critical": true,
      "depends_on": [],
      "category": "runtime"
    }
  ],
  "environment_variables": [],
  "post_install_commands": [],
  "ai_reasoning": "Python for data analysis"
}
```
"""
    result = extract_json_from_response(sample_response, validate_schema=True)
    assert result.success is True
    assert "Stack Analysis" in result.thinking
    assert result.manifest["target_environment"]["name"] == "python-ds"
    assert len(result.manifest["packages"]) == 1


def test_build_user_prompt_with_context():
    """Test prompt builder appends existing system context if present."""
    prompt = build_user_prompt(
        user_request="Configure Rust dev",
        system_context={"installed_software": ["Git 2.40.0"], "os_version": "Windows 11"},
    )
    assert "## User Request" in prompt
    assert "Configure Rust dev" in prompt
    assert "Git 2.40.0" in prompt
    assert "Windows 11" in prompt
