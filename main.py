import typer
import subprocess
from rich.console import Console
from engine import GitAgent

app = typer.Typer()
console = Console()

# UPGRADE 3: Guardrails for Destructive Commands
DANGEROUS_COMMANDS = ["reset --hard", "push --force", "-f", "clean -fd"]

def is_safe(cmd_string: str) -> bool:
    """Check if the AI suggested something that could delete code."""
    for danger in DANGEROUS_COMMANDS:
        if danger in cmd_string:
            return False
    return True

@app.command()
def main(intent: str):
    """
    Translate English into Git commands and execute them.
    """
    # Instantiate our new OOP class
    agent = GitAgent()
    
    # UPGRADE 4: Rich Terminal Animations
    with console.status("[bold cyan]AI is reading your repo and writing commands...", spinner="dots"):
        try:
            sequence = agent.generate_commands(intent)
        except Exception as e:
            console.print(f"[bold red]AI System Error: {e}[/bold red]")
            raise typer.Abort()
            
    console.print("\n[bold yellow]Proposed Commands:[/bold yellow]")
    
    # Check Safety and Print
    for cmd in sequence.commands:
        full_cmd = f"{cmd.command} {' '.join(cmd.args)}"
        
        if not is_safe(full_cmd):
            console.print(f"  > [bold red]BLOCKED:[/bold red] {full_cmd} (Dangerous command detected)")
            console.print("[red]Aborting operation to protect repository.[/red]")
            raise typer.Abort()
            
        console.print(f"  > {full_cmd}")
        
    # Ask for confirmation
    confirm = typer.confirm("\nDo you want to run these commands?")
    if not confirm:
        console.print("[red]Aborted.[/red]")
        raise typer.Abort()
        
    # Execute safely in Windows shell
    for cmd in sequence.commands:
        windows_safe_command = f"{cmd.command} {' '.join(cmd.args)}"
        console.print(f"[dim]Running: {windows_safe_command}...[/dim]")
        
        result = subprocess.run(windows_safe_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print(f"[green]Success![/green]")
        else:
            console.print(f"[bold red]Git Error:[/bold red]\n{result.stderr}")
            break 

if __name__ == "__main__":
    app()