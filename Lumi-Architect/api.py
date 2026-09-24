import os
import sys
import json
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from brain.prompt_engine import PromptEngine, PromptEngineResult, validate_manifest
from brain.llm_client import LLMClient

logger = logging.getLogger("lumi.api")
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

@app.websocket("/ws/forge")
async def websocket_forge(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming of Forge execution and verification logs.
    Protocol:
      Client -> Server: {"manifest": {...}, "dry_run": false}
      Server -> Client: {"type": "status", "stage": "FORGING"|"VERIFYING"|"COMPLETED"|"FAILED", "message": "..."}
      Server -> Client: {"type": "log", "line": "..."}
      Server -> Client: {"type": "complete", "success": bool, "all_healthy": bool}
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        manifest = data.get("manifest")
        dry_run = data.get("dry_run", False)

        if not manifest:
            await websocket.send_json({"type": "error", "message": "Missing manifest in request payload."})
            await websocket.close(code=1008)
            return

        is_valid, err_msg = validate_manifest(manifest)
        if not is_valid:
            await websocket.send_json({
                "type": "error",
                "message": f"Manifest failed architecture schema validation: {err_msg}"
            })
            await websocket.close(code=1008)
            return

        manifest_path = save_manifest(manifest)
        await websocket.send_json({
            "type": "status",
            "stage": "FORGING",
            "message": f"Starting Forge execution for '{manifest.get('target_environment', {}).get('name', 'environment')}'..."
        })

        ps_command = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", str(FORGE_SCRIPT),
            "-ManifestPath", str(manifest_path)
        ]
        if dry_run:
            ps_command.append("-DryRun")

        # Spawn asynchronous PowerShell subprocess for streaming
        process = await asyncio.create_subprocess_exec(
            *ps_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(SCRIPT_DIR)
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if text:
                await websocket.send_json({"type": "log", "line": text})

        await process.wait()
        forge_success = (process.returncode == 0)

        # Run post-install health verification if forge succeeded
        all_healthy = False
        if forge_success:
            await websocket.send_json({
                "type": "status",
                "stage": "VERIFYING",
                "message": "Forge completed. Running post-installation health checks..."
            })
            hc_command = [
                "powershell",
                "-ExecutionPolicy", "Bypass",
                "-File", str(HEALTH_CHECK_SCRIPT),
                "-ManifestPath", str(manifest_path),
                "-Detailed"
            ]
            hc_process = await asyncio.create_subprocess_exec(
                *hc_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(SCRIPT_DIR)
            )
            while True:
                line = await hc_process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\r\n")
                if text:
                    await websocket.send_json({"type": "log", "line": text})
            await hc_process.wait()
            all_healthy = (hc_process.returncode == 0)

        await websocket.send_json({
            "type": "complete",
            "stage": "COMPLETED" if (forge_success and all_healthy) else ("WARNING" if forge_success else "FAILED"),
            "success": forge_success,
            "all_healthy": all_healthy,
            "exit_code": process.returncode
        })

    except WebSocketDisconnect:
        logger.info("Forge WebSocket client disconnected.")
    except Exception as exc:
        logger.error(f"Error during WebSocket forge execution: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=1011)
        except Exception:
            pass

@app.post("/api/forge/execute")
async def execute_forge(request: ExecuteRequest):
    """Execute the forge script with the provided manifest (non-blocking async)."""
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
        process = await asyncio.create_subprocess_exec(
            *ps_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(SCRIPT_DIR)
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {"success": True, "output": stdout.decode("utf-8", errors="replace")}
        else:
            return {"success": False, "error": stderr.decode("utf-8", errors="replace")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
