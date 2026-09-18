"""
Lumi: Architect - Prompt Engine
================================
This module contains the System Prompt and logic for transforming
natural language user requests into structured Architecture Manifests.

The prompt uses Chain-of-Thought (CoT) reasoning to ensure the AI
explicitly reasons about dependencies before generating the JSON output.
"""

import json
import re
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

import jsonschema
from jsonschema import Draft7Validator, ValidationError

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "architecture_manifest.schema.json"


def get_manifest_schema() -> dict:
    """Loads and caches the Architecture Manifest JSON Schema."""
    if not hasattr(get_manifest_schema, "_cached_schema"):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            get_manifest_schema._cached_schema = json.load(f)
    return get_manifest_schema._cached_schema


def validate_manifest(manifest: dict) -> Tuple[bool, Optional[str]]:
    """
    Validates an Architecture Manifest against the formal JSON Schema.
    
    Args:
        manifest: Dictionary containing the parsed manifest.
        
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    schema = get_manifest_schema()
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    
    if not errors:
        return True, None
    
    error_messages = []
    for err in errors:
        path = " -> ".join([str(p) for p in err.path]) if err.path else "root"
        error_messages.append(f"[{path}] {err.message}")
    
    return False, "; ".join(error_messages)


# =============================================================================
# SYSTEM PROMPT - The "Soul" of Lumi: Architect
# =============================================================================
# This prompt enforces:
# 1. Chain-of-Thought reasoning for dependency inference
# 2. Strict JSON output conforming to the Architecture Manifest schema
# 3. Idempotency awareness (include version_check_command for discovery)
# 4. Security constraints (only winget/choco commands)

SYSTEM_PROMPT = """You are Lumi: Architect, an expert AI Systems Architect specialized in Windows development environment configuration. Your task is to transform natural language requests into precise, executable infrastructure manifests.

## YOUR CORE DIRECTIVES

### 1. CHAIN-OF-THOUGHT REASONING (MANDATORY)
Before generating ANY JSON output, you MUST reason through the following steps internally:

**Step A - Stack Analysis:** What programming languages, frameworks, and tools does the user's request imply?

**Step B - Dependency Tree:** What are the foundational dependencies? Think in layers:
  - Layer 0: Build Tools (C++ Build Tools for native compilation, etc.)
  - Layer 1: Runtimes (Python, Node.js, .NET SDK, JDK, etc.)
  - Layer 2: Package Managers (pip, npm, cargo, etc.) - Usually bundled with runtimes
  - Layer 3: Databases/Services (MongoDB, PostgreSQL, Redis, etc.)
  - Layer 4: IDEs/Editors (VS Code, Visual Studio, etc.)
  - Layer 5: Extensions & Plugins (VS Code extensions, IDE plugins)
  - Layer 6: Global CLI Tools (typescript, create-react-app, jupyter, etc.)

**Step C - Compatibility Check:** Are there version conflicts? (e.g., Python 2 vs 3, Node 16 vs 20)

**Step D - Windows-Specific Considerations:** 
  - Does this require adding to PATH?
  - Does this need admin privileges?
  - Are there Windows-specific installers vs Unix-only tools?

### 2. OUTPUT FORMAT
Your response MUST follow this exact structure:

```thinking
[Your internal reasoning from Steps A-D goes here. Be thorough.]
```

```json
{
  "manifest_version": "1.0.0",
  "target_environment": { ... },
  "packages": [ ... ],
  "environment_variables": [ ... ],
  "post_install_commands": [ ... ],
  "ai_reasoning": "Summary of key decisions for audit log"
}
```

### 3. PACKAGE DEFINITION RULES

For each package, you MUST specify:

```json
{
  "package_id": "Exact.Winget.Or.Choco.ID",
  "display_name": "Human-Friendly Name",
  "package_manager": "winget",  // or "choco"
  "version_requirement": "latest",  // or ">=X.Y", "X.x"
  "version_check_command": "command --version",  // For idempotency
  "installation_flags": ["--silent", "--accept-package-agreements"],
  "priority_level": 1,  // Lower = install first
  "is_critical": true,  // false = continue on failure
  "depends_on": [],  // List of package_ids
  "category": "runtime"  // runtime|database|ide|extension|tool|library|build-tool
}
```

### 4. COMMON PACKAGE ID REFERENCE (Winget)

Use these EXACT package IDs:
- Python: `Python.Python.3.11` or `Python.Python.3.12`
- Node.js LTS: `OpenJS.NodeJS.LTS`
- Git: `Git.Git`
- VS Code: `Microsoft.VisualStudioCode`
- .NET SDK: `Microsoft.DotNet.SDK.8`
- Visual Studio Build Tools: `Microsoft.VisualStudio.2022.BuildTools`
- MongoDB: `MongoDB.Server`
- PostgreSQL: `PostgreSQL.PostgreSQL`
- Docker Desktop: `Docker.DockerDesktop`
- Rust: `Rustlang.Rust.MSVC`
- Go: `GoLang.Go`
- Java JDK: `Microsoft.OpenJDK.21` or `Oracle.JDK.21`

### 5. INFERENCE EXAMPLES

**User says:** "Entorno para Data Science con Python"
**You infer:**
- Python 3.11+ (runtime)
- Visual Studio Build Tools (for compiling numpy, pandas, etc.)
- VS Code + Python Extension + Jupyter Extension
- pip install: jupyter, numpy, pandas, matplotlib, scikit-learn

**User says:** "Desarrollo Fullstack con C# y React"
**You infer:**
- .NET SDK 8 (runtime for C#)
- Node.js LTS (runtime for React/npm)
- Git (version control)
- VS Code + C# Dev Kit + ES7 React Snippets
- npm global: create-react-app or vite

**User says:** "Quiero programar en Rust"
**You infer:**
- Visual Studio Build Tools (MSVC linker required)
- Rust (via rustup, includes cargo)
- VS Code + rust-analyzer extension
- Git

### 6. SECURITY CONSTRAINTS

You are ONLY allowed to generate commands using:
- `winget install`
- `choco install`
- `setx` (for environment variables)
- `npm install -g` / `pip install` / `cargo install` (post-install)
- Version check commands (e.g., `python --version`)

NEVER generate:
- Registry edits (`reg add`)
- PowerShell execution policy changes
- Download commands (`curl`, `wget`, `Invoke-WebRequest`) for arbitrary URLs
- Any command that modifies system files directly

### 7. PRIORITIZATION RULES

1. Build Tools ALWAYS have priority_level: 1-10
2. Runtimes have priority_level: 11-30
3. Databases have priority_level: 31-40
4. IDEs have priority_level: 41-50
5. Extensions have priority_level: 51-70
6. Global CLI tools (post_install_commands) run last

NOW, await the user's request and generate the manifest.
"""


# =============================================================================
# RESPONSE PARSER
# =============================================================================

@dataclass
class PromptEngineResult:
    """Result of processing a user request through the prompt engine."""
    success: bool
    manifest: Optional[dict] = None
    thinking: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None


def extract_json_from_response(response: str, validate_schema: bool = True) -> PromptEngineResult:
    """
    Extracts the JSON manifest and thinking block from an LLM response.
    
    The LLM is instructed to return:
    ```thinking
    [reasoning]
    ```
    ```json
    {manifest}
    ```
    
    This function parses both blocks and validates the manifest against
    architecture_manifest.schema.json.
    
    Args:
        response: Raw text response from the LLM.
        validate_schema: Whether to validate the extracted manifest against JSON Schema.
        
    Returns:
        PromptEngineResult with parsed manifest and thinking, or error details.
    """
    result = PromptEngineResult(success=False, raw_response=response)
    
    # Extract thinking block (optional but expected)
    thinking_pattern = r"```thinking\s*(.*?)\s*```"
    thinking_match = re.search(thinking_pattern, response, re.DOTALL)
    if thinking_match:
        result.thinking = thinking_match.group(1).strip()
    
    # Extract JSON block (required)
    json_pattern = r"```json\s*(.*?)\s*```"
    json_match = re.search(json_pattern, response, re.DOTALL)
    
    if not json_match:
        # Fallback: Try to find raw JSON object
        json_fallback_pattern = r"\{[\s\S]*\"manifest_version\"[\s\S]*\}"
        json_match = re.search(json_fallback_pattern, response)
        if json_match:
            json_str = json_match.group(0)
        else:
            result.error = "No JSON manifest found in LLM response."
            return result
    else:
        json_str = json_match.group(1).strip()
    
    # Parse JSON
    try:
        manifest = json.loads(json_str)
        if validate_schema:
            is_valid, validation_err = validate_manifest(manifest)
            if not is_valid:
                result.error = f"Schema validation failed: {validation_err}"
                result.manifest = manifest
                return result
        result.manifest = manifest
        result.success = True
    except json.JSONDecodeError as e:
        result.error = f"Invalid JSON in LLM response: {e}"
    
    return result


def build_user_prompt(user_request: str, system_context: Optional[dict] = None) -> str:
    """
    Constructs the user prompt to send to the LLM.
    
    Args:
        user_request: The natural language request from the user.
        system_context: Optional dict with additional context (e.g., existing software).
        
    Returns:
        Formatted user prompt string.
    """
    prompt_parts = [f"## User Request\n\n{user_request}"]
    
    if system_context:
        context_section = "\n## Current System Context\n\n"
        if "installed_software" in system_context:
            context_section += "### Already Installed (skip these):\n"
            for software in system_context["installed_software"]:
                context_section += f"- {software}\n"
        if "os_version" in system_context:
            context_section += f"\n### OS: {system_context['os_version']}\n"
        prompt_parts.append(context_section)
    
    prompt_parts.append("\nGenerate the Architecture Manifest now.")
    
    return "\n".join(prompt_parts)


# =============================================================================
# MAIN INTERFACE
# =============================================================================

class PromptEngine:
    """
    Main interface for the Lumi: Architect Prompt Engine.
    
    This class encapsulates the system prompt and provides methods for:
    1. Building prompts for LLM calls
    2. Parsing LLM responses into structured manifests
    
    Note: This class does NOT call the LLM directly. It prepares inputs
    and parses outputs. The actual LLM call is handled by the orchestrator.
    
    Reasoning: Separation of concerns. The PromptEngine is a pure function
    layer with no I/O side effects. This makes it testable and portable
    across different LLM providers (OpenAI, Anthropic, local models).
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
    
    def get_system_prompt(self) -> str:
        """Returns the system prompt for configuring the LLM."""
        return self.system_prompt
    
    def prepare_request(
        self, 
        user_input: str, 
        system_context: Optional[dict] = None
    ) -> dict:
        """
        Prepares a complete request payload for the LLM.
        
        Args:
            user_input: Natural language request from user.
            system_context: Optional context about current system state.
            
        Returns:
            Dict with 'system' and 'user' prompts ready for LLM API call.
        """
        return {
            "system": self.system_prompt,
            "user": build_user_prompt(user_input, system_context)
        }
    
    def parse_response(self, llm_response: str, validate_schema: bool = True) -> PromptEngineResult:
        """
        Parses an LLM response into a structured manifest.
        
        Args:
            llm_response: Raw text response from the LLM.
            
        Returns:
            PromptEngineResult containing the parsed manifest or error.
        """
        return extract_json_from_response(llm_response, validate_schema=validate_schema)
    
    def process(
        self, 
        user_input: str, 
        llm_response: str,
        system_context: Optional[dict] = None,
        validate_schema: bool = True
    ) -> PromptEngineResult:
        """
        Full pipeline: validate input and parse LLM response.
        
        This is a convenience method that combines preparation and parsing.
        Use when you have both the input and response available.
        
        Args:
            user_input: Original user request (for logging/audit).
            llm_response: Response from the LLM.
            system_context: Optional system context used in the request.
            validate_schema: Whether to validate the manifest against JSON Schema.
            
        Returns:
            PromptEngineResult with parsed manifest.
        """
        result = self.parse_response(llm_response, validate_schema=validate_schema)
        
        # Attach original request info for auditability
        if result.success and result.manifest:
            result.manifest["_meta"] = {
                "original_request": user_input,
                "had_system_context": system_context is not None
            }
        
        return result


# =============================================================================
# EXAMPLE USAGE (for testing)
# =============================================================================

if __name__ == "__main__":
    # Example: Simulate the flow without an actual LLM call
    engine = PromptEngine()
    
    # Step 1: User provides natural language input
    user_request = "Necesito un entorno para desarrollo web fullstack con Node.js y React"
    
    # Step 2: Prepare the prompt (this would be sent to the LLM)
    request_payload = engine.prepare_request(user_request)
    print("=" * 60)
    print("SYSTEM PROMPT (first 500 chars):")
    print("=" * 60)
    print(request_payload["system"][:500] + "...")
    print("\n" + "=" * 60)
    print("USER PROMPT:")
    print("=" * 60)
    print(request_payload["user"])
    
    # Step 3: Simulate an LLM response (in production, this comes from the API)
    mock_llm_response = '''
```thinking
Step A - Stack Analysis: User wants fullstack web with Node.js and React.
This implies: JavaScript/TypeScript runtime, React framework, likely Express for backend.

Step B - Dependency Tree:
- Layer 1: Node.js LTS (includes npm)
- Layer 1: Git (essential for any dev work)
- Layer 4: VS Code
- Layer 5: ES7 React Snippets, Prettier
- Layer 6: create-react-app or vite globally

Step C - No version conflicts. Node LTS is stable.

Step D - Windows: Node installer handles PATH. No admin needed for npm global with proper config.
```

```json
{
  "manifest_version": "1.0.0",
  "target_environment": {
    "name": "fullstack-node-react",
    "description": "Entorno de desarrollo web fullstack con Node.js y React",
    "inferred_languages": ["JavaScript", "TypeScript"],
    "inferred_frameworks": ["React", "Express"]
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
      "is_critical": true,
      "depends_on": [],
      "category": "tool"
    },
    {
      "package_id": "OpenJS.NodeJS.LTS",
      "display_name": "Node.js LTS",
      "package_manager": "winget",
      "version_requirement": "latest",
      "version_check_command": "node --version",
      "installation_flags": ["--silent"],
      "priority_level": 15,
      "is_critical": true,
      "depends_on": [],
      "category": "runtime"
    },
    {
      "package_id": "Microsoft.VisualStudioCode",
      "display_name": "Visual Studio Code",
      "package_manager": "winget",
      "version_requirement": "latest",
      "version_check_command": "code --version",
      "installation_flags": ["--silent"],
      "priority_level": 45,
      "is_critical": false,
      "depends_on": [],
      "category": "ide"
    }
  ],
  "environment_variables": [],
  "post_install_commands": [
    {
      "command": "npm install -g create-react-app",
      "description": "Install Create React App globally for scaffolding React projects",
      "requires_restart": false,
      "is_critical": false
    },
    {
      "command": "npm install -g typescript",
      "description": "Install TypeScript compiler globally",
      "requires_restart": false,
      "is_critical": false
    }
  ],
  "ai_reasoning": "Inferred Node.js + React stack. Included Git as foundational tool. VS Code as primary IDE for JavaScript development. Added global npm packages for React scaffolding and TypeScript support."
}
```
'''
    
    # Step 4: Parse the response
    result = engine.process(user_request, mock_llm_response)
    
    print("\n" + "=" * 60)
    print("PARSING RESULT:")
    print("=" * 60)
    print(f"Success: {result.success}")
    if result.thinking:
        print(f"\nAI Thinking:\n{result.thinking[:300]}...")
    if result.manifest:
        print(f"\nManifest (packages count): {len(result.manifest.get('packages', []))}")
        print(f"Packages: {[p['display_name'] for p in result.manifest.get('packages', [])]}")
    if result.error:
        print(f"Error: {result.error}")
