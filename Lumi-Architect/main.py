"""
Lumi: Architect - Main Orchestrator
====================================
The neural nexus that connects the Brain (AI) to the Forge (PowerShell).

Usage:
    python main.py              # Interactive mode
    python main.py --demo       # Demo mode with mock LLM response
    python main.py --help       # Show help

Author: Lumi: Architect
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Rich imports for beautiful CLI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich.style import Style
    from rich import box
    from rich.markdown import Markdown
except ImportError:
    print("Error: 'rich' library not installed.")
    print("Run: pip install rich")
    sys.exit(1)

# Project imports
from brain.prompt_engine import PromptEngine, PromptEngineResult

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
FORGE_SCRIPT = SCRIPT_DIR / "forge" / "executor.ps1"
HEALTH_CHECK_SCRIPT = SCRIPT_DIR / "forge" / "health_check.ps1"
OUTPUT_DIR = SCRIPT_DIR / "output"
MANIFEST_FILENAME = "manifest_{timestamp}.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Console with force_terminal for proper styling
console = Console(force_terminal=True, color_system="truecolor")

# =============================================================================
# CYBERPUNK THEME & BANNER
# =============================================================================

BANNER = r"""
[bold magenta]
    ██╗     ██╗   ██╗███╗   ███╗██╗
    ██║     ██║   ██║████╗ ████║██║
    ██║     ██║   ██║██╔████╔██║██║
    ██║     ██║   ██║██║╚██╔╝██║██║
    ███████╗╚██████╔╝██║ ╚═╝ ██║██║
    ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝
[/bold magenta]
[bold cyan]    A R C H I T E C T[/bold cyan]
[dim]    AI-Powered Infrastructure Forge for Windows[/dim]
"""

STYLES = {
    "primary": Style(color="magenta", bold=True),
    "secondary": Style(color="cyan"),
    "success": Style(color="green", bold=True),
    "warning": Style(color="yellow"),
    "error": Style(color="red", bold=True),
    "muted": Style(color="bright_black"),
}

# =============================================================================
# MOCK LLM RESPONSE (for demo mode)
# =============================================================================

DEMO_RESPONSES = {
    "default": {
        "thinking": """Step A - Stack Analysis: Analyzing user request for development environment.
Step B - Dependency Tree: Identifying core runtimes, tools, and IDE requirements.
Step C - Compatibility Check: Ensuring all components work together on Windows.
Step D - Windows Considerations: Checking PATH requirements and admin needs.""",
        "manifest": {
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
            "post_install_commands": [
                {
                    "command": "npm install -g typescript",
                    "description": "Install TypeScript globally",
                    "requires_restart": False,
                    "is_critical": False
                }
            ],
            "ai_reasoning": "Standard development environment with Git, Node.js, Python, and VS Code."
        }
    }
}


# =============================================================================
# UI COMPONENTS
# =============================================================================

def show_banner():
    """Display the Lumi: Architect banner."""
    console.print(BANNER)
    console.print()


def show_error(message: str, details: str = None):
    """Display a styled error message."""
    error_panel = Panel(
        f"[bold red]ERROR[/bold red]\n\n{message}" + (f"\n\n[dim]{details}[/dim]" if details else ""),
        border_style="red",
        title="[red]System Failure[/red]",
        title_align="left"
    )
    console.print(error_panel)


def show_success(message: str):
    """Display a styled success message."""
    success_panel = Panel(
        f"[bold green]SUCCESS[/bold green]\n\n{message}",
        border_style="green",
        title="[green]Operation Complete[/green]",
        title_align="left"
    )
    console.print(success_panel)


def show_thinking(thinking: str):
    """Display the AI's reasoning process."""
    thinking_panel = Panel(
        Markdown(thinking),
        border_style="cyan",
        title="[cyan]AI Reasoning Process[/cyan]",
        title_align="left"
    )
    console.print(thinking_panel)


def show_forge_plan(manifest: dict):
    """Display the forge plan as a styled table."""
    console.print()
    
    # Environment info
    env = manifest.get("target_environment", {})
    env_panel = Panel(
        f"[bold]{env.get('name', 'Unknown')}[/bold]\n"
        f"[dim]{env.get('description', 'No description')}[/dim]\n\n"
        f"[cyan]Languages:[/cyan] {', '.join(env.get('inferred_languages', []))}\n"
        f"[cyan]Frameworks:[/cyan] {', '.join(env.get('inferred_frameworks', []))}",
        border_style="magenta",
        title="[magenta]Target Environment[/magenta]",
        title_align="left"
    )
    console.print(env_panel)
    console.print()
    
    # Packages table
    table = Table(
        title="[bold magenta]FORGE PLAN[/bold magenta]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
        show_lines=True
    )
    
    table.add_column("#", style="dim", width=3)
    table.add_column("Package", style="bold white")
    table.add_column("Manager", style="yellow")
    table.add_column("Priority", style="cyan", justify="center")
    table.add_column("Category", style="magenta")
    table.add_column("Critical", justify="center")
    
    packages = manifest.get("packages", [])
    packages_sorted = sorted(packages, key=lambda x: x.get("priority_level", 99))
    
    for idx, pkg in enumerate(packages_sorted, 1):
        critical_icon = "[green]✓[/green]" if pkg.get("is_critical") else "[dim]○[/dim]"
        table.add_row(
            str(idx),
            pkg.get("display_name", pkg.get("package_id", "Unknown")),
            pkg.get("package_manager", "winget"),
            str(pkg.get("priority_level", "?")),
            pkg.get("category", "unknown"),
            critical_icon
        )
    
    console.print(table)
    console.print()
    
    # Post-install commands
    post_commands = manifest.get("post_install_commands", [])
    if post_commands:
        post_table = Table(
            title="[bold yellow]POST-INSTALL COMMANDS[/bold yellow]",
            box=box.SIMPLE,
            border_style="yellow"
        )
        post_table.add_column("Command", style="cyan")
        post_table.add_column("Description", style="white")
        
        for cmd in post_commands:
            post_table.add_row(cmd.get("command", ""), cmd.get("description", ""))
        
        console.print(post_table)
        console.print()
    
    # AI Reasoning
    reasoning = manifest.get("ai_reasoning", "")
    if reasoning:
        console.print(Panel(
            f"[italic]{reasoning}[/italic]",
            border_style="dim",
            title="[dim]AI Reasoning Summary[/dim]",
            title_align="left"
        ))
        console.print()


# =============================================================================
# CORE ORCHESTRATION
# =============================================================================

def get_user_request() -> str:
    """Prompt the user for their environment description."""
    console.print(Panel(
        "[bold]Describe the development environment you want to forge.[/bold]\n\n"
        "[dim]Examples:[/dim]\n"
        "  • Entorno para desarrollo fullstack con Node.js y React\n"
        "  • Python para Data Science con Jupyter y ML libraries\n"
        "  • Desarrollo de aplicaciones C# con .NET 8 y SQL Server\n"
        "  • Rust development with VS Code",
        border_style="magenta",
        title="[magenta]Environment Request[/magenta]",
        title_align="left"
    ))
    console.print()
    
    user_input = Prompt.ask(
        "[bold cyan]>>[/bold cyan] [bold]Your request[/bold]",
        console=console
    )
    
    return user_input.strip()


def simulate_llm_call(user_request: str, demo_mode: bool = False) -> PromptEngineResult:
    """
    Simulate or make actual LLM call.
    
    In demo mode, returns a mock response.
    In production, this would call the actual LLM API.
    """
    engine = PromptEngine()
    
    if demo_mode:
        # Use mock response
        mock = DEMO_RESPONSES["default"]
        
        # Customize based on keywords in request
        manifest = mock["manifest"].copy()
        manifest["target_environment"]["description"] = f"Environment for: {user_request}"
        
        result = PromptEngineResult(
            success=True,
            manifest=manifest,
            thinking=mock["thinking"]
        )
        return result
    else:
        # Production: Would call actual LLM API here
        # For now, return demo response with a notice
        console.print("[yellow]Note: LLM API not configured. Using demo response.[/yellow]")
        return simulate_llm_call(user_request, demo_mode=True)


def process_request(user_request: str, demo_mode: bool = False) -> PromptEngineResult:
    """Process the user request through the Brain module with loading animation."""
    
    with Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[magenta]Neural processing...[/magenta]"),
        TextColumn("[dim]{task.description}[/dim]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Analyzing request", total=None)
        
        # Simulate processing stages
        import time
        
        progress.update(task, description="Parsing natural language...")
        time.sleep(0.5)
        
        progress.update(task, description="Inferring dependencies...")
        time.sleep(0.5)
        
        progress.update(task, description="Resolving compatibility...")
        time.sleep(0.5)
        
        progress.update(task, description="Generating manifest...")
        time.sleep(0.5)
        
        # Actually process the request
        result = simulate_llm_call(user_request, demo_mode)
        
        progress.update(task, description="Complete!")
        time.sleep(0.3)
    
    return result


def save_manifest(manifest: dict) -> Path:
    """Save the manifest to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"manifest_{timestamp}.json"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return filepath


def execute_forge(manifest_path: Path) -> bool:
    """Execute the PowerShell Forge script."""
    
    console.print()
    console.print(Panel(
        "[bold]Initiating Forge Execution[/bold]\n\n"
        f"[dim]Manifest:[/dim] {manifest_path}\n"
        f"[dim]Executor:[/dim] {FORGE_SCRIPT}",
        border_style="yellow",
        title="[yellow]Forge Activation[/yellow]",
        title_align="left"
    ))
    console.print()
    
    # Build the PowerShell command
    ps_command = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(FORGE_SCRIPT),
        "-ManifestPath", str(manifest_path)
    ]
    
    console.print("[cyan]Launching PowerShell executor...[/cyan]")
    console.print("[dim]" + " ".join(ps_command) + "[/dim]")
    console.print()
    
    try:
        # Run the forge script
        result = subprocess.run(
            ps_command,
            cwd=str(SCRIPT_DIR),
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        return result.returncode == 0
        
    except FileNotFoundError:
        show_error(
            "PowerShell not found in PATH.",
            "Ensure PowerShell is installed and accessible."
        )
        return False
    except Exception as e:
        show_error(
            f"Failed to execute Forge: {e}",
            "Check that the executor.ps1 file exists and is valid."
        )
        return False


def execute_health_check(manifest_path: Path) -> bool:
    """Execute the PowerShell Health Check script."""
    
    console.print()
    console.print(Panel(
        "[bold]Running Post-Forge Health Check[/bold]\n\n"
        "Verifying all installed tools are accessible...",
        border_style="cyan",
        title="[cyan]System Verification[/cyan]",
        title_align="left"
    ))
    console.print()
    
    ps_command = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(HEALTH_CHECK_SCRIPT),
        "-ManifestPath", str(manifest_path),
        "-Detailed"
    ]
    
    try:
        result = subprocess.run(
            ps_command,
            cwd=str(SCRIPT_DIR),
            capture_output=False,
            text=True
        )
        
        return result.returncode == 0
        
    except Exception as e:
        console.print(f"[yellow]Health check could not run: {e}[/yellow]")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main orchestrator entry point."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Lumi: Architect - AI-Powered Infrastructure Forge"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run in demo mode with mock LLM responses"
    )
    parser.add_argument(
        "--request", "-r",
        type=str,
        help="Provide request directly instead of interactive prompt"
    )
    args = parser.parse_args()
    
    # Clear screen and show banner
    console.clear()
    show_banner()
    
    if args.demo:
        console.print(Panel(
            "[yellow]DEMO MODE ACTIVE[/yellow]\n"
            "[dim]Using mock LLM responses for demonstration.[/dim]",
            border_style="yellow"
        ))
        console.print()
    
    # Main loop
    while True:
        try:
            # Get user request
            if args.request:
                user_request = args.request
                console.print(f"[bold cyan]Request:[/bold cyan] {user_request}")
                args.request = None  # Only use once
            else:
                user_request = get_user_request()
            
            if not user_request:
                console.print("[yellow]No request provided. Please try again.[/yellow]")
                continue
            
            if user_request.lower() in ("exit", "quit", "q"):
                console.print("[dim]Exiting Lumi: Architect...[/dim]")
                break
            
            # Process through Brain
            console.print()
            result = process_request(user_request, demo_mode=args.demo)
            
            if not result.success:
                show_error(
                    "Failed to generate architecture manifest.",
                    result.error or "Unknown error occurred."
                )
                
                retry = Confirm.ask("[yellow]Would you like to try again?[/yellow]")
                if retry:
                    continue
                else:
                    break
            
            # Show AI thinking (if available)
            if result.thinking:
                show_thinking(result.thinking)
            
            # Show the forge plan
            show_forge_plan(result.manifest)
            
            # Confirmation prompt
            console.print(Panel(
                "[bold yellow]CONFIRMATION REQUIRED[/bold yellow]\n\n"
                "The Forge will install the packages listed above.\n"
                "This may require Administrator privileges.",
                border_style="yellow"
            ))
            
            proceed = Confirm.ask(
                "[bold magenta]>> Do you want to initiate the Forge?[/bold magenta]",
                console=console
            )
            
            if proceed:
                # Save manifest
                manifest_path = save_manifest(result.manifest)
                console.print(f"[dim]Manifest saved to: {manifest_path}[/dim]")
                
                # Execute forge
                success = execute_forge(manifest_path)
                
                if success:
                    # Run health check after successful forge
                    health_ok = execute_health_check(manifest_path)
                    
                    if health_ok:
                        show_success(
                            "Forge execution completed!\n\n"
                            "All installed tools passed health verification.\n"
                            "Your development environment is ready to use!"
                        )
                    else:
                        show_success(
                            "Forge execution completed!\n\n"
                            "Some tools may need a terminal restart to be accessible.\n"
                            "Run health_check.ps1 again after restarting your terminal."
                        )
                else:
                    show_error(
                        "Forge execution encountered errors.",
                        "Check the output above for details."
                    )
                    
                    # Offer to run health check anyway
                    run_health = Confirm.ask(
                        "[yellow]Run health check to see current system state?[/yellow]"
                    )
                    if run_health:
                        execute_health_check(manifest_path)
            else:
                console.print("[dim]Forge cancelled by user.[/dim]")
            
            # Ask if they want to forge another environment
            console.print()
            another = Confirm.ask("[cyan]Would you like to forge another environment?[/cyan]")
            if not another:
                break
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted by user. Exiting...[/dim]")
            break
        except Exception as e:
            show_error(f"Unexpected error: {e}")
            console.print("[dim]Please report this issue.[/dim]")
            break
    
    console.print()
    console.print("[bold magenta]Thank you for using Lumi: Architect![/bold magenta]")
    console.print("[dim]May your development environment be ever optimized.[/dim]")
    console.print()


if __name__ == "__main__":
    main()
