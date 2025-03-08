"""
Command-line interface for FastAPI-MCP.
"""

import os
import sys
import json
import shutil
import importlib.util
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from fastapi_mcp.discovery import discover_fastapi_app
from fastapi_mcp.generator import generate_mcp_server
from fastapi_mcp.utils import find_fastapi_app, load_module_from_path

app = typer.Typer(
    name="fastapi-mcp",
    help="A magical tool for generating MCP servers from FastAPI applications.",
    add_completion=False,
)

console = Console()

@app.command()
def generate(
    source_path: str = typer.Argument(
        ...,
        help="Path to a FastAPI application file or module. Use 'module.py:app_var' if the app variable is not named 'app'.",
    ),
    output_dir: Optional[str] = typer.Option(
        "mcp_server",
        "--output", "-o",
        help="Directory where the MCP server will be generated.",
    ),
    app_var: Optional[str] = typer.Option(
        None,
        "--app-var",
        help="Name of the FastAPI application variable. If not provided, it will be extracted from the source path.",
    ),
    base_url: Optional[str] = typer.Option(
        "http://localhost:8000",
        "--base-url", "-b",
        help="Base URL of the FastAPI server to call. Defaults to http://localhost:8000.",
    ),
):
    """
    Generate an MCP server from a FastAPI application.
    """
    console.print(Panel.fit("🚀 FastAPI-MCP Generator", title="FastAPI-MCP"))
    
    # Process the source path to determine the module and app variable
    if ":" in source_path:
        module_path, var_name = source_path.split(":", 1)
    else:
        module_path = source_path
        var_name = app_var or "app"
    
    # Resolve the module path
    module_path = Path(module_path).resolve()
    if not module_path.exists():
        console.print(f"[bold red]Error:[/bold red] File {module_path} does not exist.")
        sys.exit(1)
    
    # Load the module
    console.print(f"🔍 Loading module from {module_path}...")
    module = load_module_from_path(module_path)
    
    # Find the FastAPI app in the module
    console.print(f"🔍 Finding FastAPI app '{var_name}' in module...")
    app_instance = find_fastapi_app(module, var_name)
    if not app_instance:
        console.print(f"[bold red]Error:[/bold red] Could not find FastAPI app '{var_name}' in module {module_path.name}.")
        sys.exit(1)
    
    # Discover the endpoints in the app
    console.print("🔍 Discovering endpoints...")
    endpoints = discover_fastapi_app(app_instance)
    
    if not endpoints:
        console.print("[bold yellow]Warning:[/bold yellow] No endpoints found in the FastAPI app.")
    else:
        console.print(f"✅ Found {len(endpoints)} endpoints.")
    
    # Create the output directory
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate the MCP server
    console.print(f"⚙️ Generating MCP server in {output_path}...")
    server_path = generate_mcp_server(app_instance, endpoints, output_path, base_url)
    
    # Generate requirements.txt
    requirements_path = output_path / "requirements.txt"
    with open(requirements_path, "w") as f:
        f.write("mcp>=1.3.0\n")
        f.write("requests>=2.25.0\n")
        f.write("pydantic>=2.0.0\n")
    
    # Generate README.md
    from fastapi_mcp.generator import generate_readme
    readme_path = output_path / "README.md"
    with open(readme_path, "w") as f:
        f.write(generate_readme(app_instance, endpoints))
    
    console.print(f"✅ MCP server generated in {output_path}.")
    console.print(f"\nServer code: {server_path}")
    console.print(f"Requirements: {requirements_path}")
    console.print(f"README: {readme_path}")
    
    console.print("\n🚀 What's next?")
    console.print("  - Run [bold]fastapi-mcp preview[/bold] to see the generated server code")
    console.print("  - Run [bold]fastapi-mcp run[/bold] to run the server")
    console.print("  - Run [bold]fastapi-mcp install[/bold] to install the server for Claude")


@app.command()
def preview(
    dir: str = typer.Option(
        "mcp_server",
        "--dir", "-d",
        help="Directory where the MCP server was generated.",
    ),
):
    """
    Preview the generated MCP server.
    """
    console.print(Panel.fit("👀 FastAPI-MCP Preview", title="FastAPI-MCP"))
    
    dir_path = Path(dir).resolve()
    server_path = dir_path / "server.py"
    
    if not server_path.exists():
        console.print(f"[bold red]Error:[/] No MCP server found at '{server_path}'.")
        console.print("Generate a server first with 'fastapi-mcp generate'.")
        raise typer.Exit(code=1)
    
    console.print(f"Previewing MCP server at: [bold blue]{server_path}[/]\n")
    
    # Load and display the server code
    with open(server_path, "r") as f:
        server_code = f.read()
    
    syntax = Syntax(server_code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="server.py", border_style="blue"))
    
    # Display available tools
    try:
        module_spec = importlib.util.spec_from_file_location("mcp_server", server_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        
        mcp_server = getattr(module, "server", None)
        if mcp_server is None:
            console.print("[bold yellow]Warning:[/] Could not find MCP server object in generated code.")
            return
        
        console.print("\n📝 Available MCP Tools:")
        
        # Handle different MCP SDK versions
        if hasattr(mcp_server, "tools"):
            for tool_name, tool in mcp_server.tools.items():
                console.print(f"  - [bold green]{tool_name}[/]")
                if hasattr(tool, "__doc__") and tool.__doc__:
                    console.print(f"    {tool.__doc__.strip()}")
        elif hasattr(mcp_server, "_tools"):
            for tool_name, tool in getattr(mcp_server, "_tools", {}).items():
                console.print(f"  - [bold green]{tool_name}[/]")
                if hasattr(tool, "__doc__") and tool.__doc__:
                    console.print(f"    {tool.__doc__.strip()}")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to load generated server: {str(e)}")


@app.command()
def run(
    dir: str = typer.Option(
        "mcp_server",
        "--dir", "-d",
        help="Directory where the MCP server was generated.",
    ),
):
    """
    Run the generated MCP server.
    """
    console.print(Panel.fit("▶️ FastAPI-MCP Runner", title="FastAPI-MCP"))
    
    dir_path = Path(dir).resolve()
    server_path = dir_path / "server.py"
    
    if not server_path.exists():
        console.print(f"[bold red]Error:[/] No MCP server found at '{server_path}'.")
        console.print("Generate a server first with 'fastapi-mcp generate'.")
        raise typer.Exit(code=1)
    
    console.print(f"Running MCP server at: [bold blue]{server_path}[/]\n")
    
    # Add the directory to sys.path so the server can be imported
    sys.path.insert(0, str(dir_path.parent))
    
    # Run the server
    try:
        # Execute the server script
        with open(server_path, "r") as f:
            server_code = f.read()
        
        # Execute in the current process
        globals_dict = {
            "__file__": str(server_path),
            "__name__": "__main__",
        }
        exec(server_code, globals_dict)
    
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Server stopped by user.[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to run the server: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def install(
    dir: str = typer.Option(
        "mcp_server",
        "--dir", "-d",
        help="Directory where the MCP server was generated.",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Name for the server in the Claude configuration. Defaults to the directory name.",
    ),
):
    """
    Install the generated MCP server for use with Claude or other MCP clients.
    """
    console.print(Panel.fit("📦 FastAPI-MCP Installer", title="FastAPI-MCP"))
    
    dir_path = Path(dir).resolve()
    server_path = dir_path / "server.py"
    
    if not server_path.exists():
        console.print(f"[bold red]Error:[/] No MCP server found at '{server_path}'.")
        console.print("Generate a server first with 'fastapi-mcp generate'.")
        raise typer.Exit(code=1)
    
    # Determine server name
    if name is None:
        name = dir_path.name
    
    # Find Claude config directory
    home_dir = Path.home()
    config_dirs = [
        home_dir / ".config" / "claude",  # Linux/macOS
        home_dir / "Library" / "Application Support" / "Claude",  # macOS alternate
        home_dir / "AppData" / "Roaming" / "Claude",  # Windows
    ]
    
    config_dir = None
    for d in config_dirs:
        if d.exists():
            config_dir = d
            break
    
    if config_dir is None:
        console.print("[bold yellow]Warning:[/] Could not find Claude configuration directory.")
        console.print("Manual installation required. Copy the server to the desired location and add it to your Claude configuration.")
        return
    
    # Find or create the servers directory
    servers_dir = config_dir / "servers"
    servers_dir.mkdir(exist_ok=True)
    
    # Create installation directory
    install_dir = servers_dir / name
    install_dir.mkdir(exist_ok=True)
    
    # Copy the server files
    console.print(f"Installing MCP server to: [bold blue]{install_dir}[/]")
    
    # Copy server.py
    shutil.copy2(server_path, install_dir / "server.py")
    
    # Copy requirements.txt if it exists
    requirements_path = dir_path / "requirements.txt"
    if requirements_path.exists():
        shutil.copy2(requirements_path, install_dir / "requirements.txt")
    
    # Create or update the config file
    config_file = config_dir / "config.json"
    config = {}
    
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            console.print("[bold yellow]Warning:[/] Could not parse existing config file. Creating a new one.")
    
    # Update config
    if "servers" not in config:
        config["servers"] = []
    
    # Check if the server is already in the config
    server_found = False
    for server in config["servers"]:
        if server.get("name") == name:
            server_found = True
            server.update({
                "name": name,
                "command": f"python3 {install_dir / 'server.py'}",
                "enabled": True,
            })
            break
    
    # Add the server if not found
    if not server_found:
        config["servers"].append({
            "name": name,
            "command": f"python3 {install_dir / 'server.py'}",
            "enabled": True,
        })
    
    # Write the config file
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    console.print(f"\n✅ MCP server '{name}' installed successfully.")
    console.print("\nStart the Claude application to use the server.")
    console.print("\nAlternatively, you can run the server manually with:")
    console.print(f"[bold]cd {install_dir} && python server.py[/]")


if __name__ == "__main__":
    app() 