import os
import sys
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from brain.prompt_engine import PromptEngine, PromptEngineResult, validate_manifest
from brain.llm_client import LLMClient

app = FastAPI(title="Lumi: Architect API", description="AI-Powered Infrastructure Forge API")
llm_client = LLMClient()

# Allow CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRIPT_DIR = Path(__file__).parent.resolve()
FORGE_SCRIPT = SCRIPT_DIR / "forge" / "executor.ps1"
HEALTH_CHECK_SCRIPT = SCRIPT_DIR / "forge" / "health_check.ps1"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Mock responses from main.py for demo mode (strictly schema-compliant)
DEMO_MANIFEST = {
    "manifest_version": "1.0.0",
    "target_environment": {
        "name": "custom-dev-environment",
        "description": "Custom development environment based on user request",
        "inferred_languages": ["JavaScript", "Python"],
        "inferred_frameworks": ["Node.js"]
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
            "category": "tool"
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
            "category": "runtime"
        },
        {
            "package_id": "Python.Python.3.11",
            "display_name": "Python 3.11",
            "package_manager": "winget",
            "version_requirement": "3.11",
            "version_check_command": "python --version",
            "installation_flags": ["--silent"],
            "priority_level": 25,
            "is_critical": True,
            "category": "runtime"
        },
        {
            "package_id": "Microsoft.VisualStudioCode",
            "display_name": "Visual Studio Code",
            "package_manager": "winget",
            "version_requirement": "latest",
            "version_check_command": "code --version",
            "installation_flags": ["--silent"],
            "priority_level": 50,
            "is_critical": False,
            "category": "ide"
        }
    ],
    "environment_variables": [],
    "post_install_commands": [],
    "ai_reasoning": "Standard development environment with Git, Node.js, Python, and VS Code."
}

class PlanRequest(BaseModel):
    prompt: str
    demo_mode: bool = True

class ExecuteRequest(BaseModel):
    manifest: Dict[str, Any]

def save_manifest(manifest: dict) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"manifest_{timestamp}.json"
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return filepath

@app.post("/api/forge/plan")
async def create_plan(request: PlanRequest):
    """Generate an infrastructure manifest based on a natural language prompt."""
    engine = PromptEngine()
    req_payload = engine.prepare_request(request.prompt)

    if request.demo_mode and not llm_client.is_configured():
        raw_response = llm_client._generate_fallback(request.prompt)
    else:
        raw_response = await llm_client.agenerate(
            system_prompt=req_payload["system"],
            user_prompt=req_payload["user"]
        )

    result = engine.parse_response(raw_response, validate_schema=True)
    if not result.success:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to generate valid architecture manifest: {result.error}"
        )

    return {
        "success": True,
        "manifest": result.manifest,
        "thinking": result.thinking or "Reasoning completed successfully.",
        "provider": llm_client.provider if llm_client.is_configured() else "offline-template"
    }

@app.post("/api/forge/execute")
async def execute_forge(request: ExecuteRequest):
    """Execute the forge script with the provided manifest."""
    is_valid, err_msg = validate_manifest(request.manifest)
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail=f"Manifest failed architecture schema validation: {err_msg}"
        )
    
    manifest_path = save_manifest(request.manifest)
    
    ps_command = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(FORGE_SCRIPT),
        "-ManifestPath", str(manifest_path)
    ]
    
    try:
        # Run asynchronously and return immediately in a real app, 
        # but for simplicity we will wait and return the result.
        result = subprocess.run(
            ps_command,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
