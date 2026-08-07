import typer
import subprocess
from rich.console import Console
from engine import generate_git_commands

app = typer.Typer()
console = Console()

@app.command()
def do(intent: str):
    """
    Translate English into Git commands and execute them.
    """
    console.print(f"[cyan]Thinking about: '{intent}'...[/cyan]")
    
    try:
        # 1. Get the commands from the local LLM
        sequence = generate_git_commands(intent)
        
        # 2. Show the user what we are about to run
        console.print("\n[bold yellow]Proposed Commands:[/bold yellow]")
        for cmd in sequence.commands:
            full_cmd = f"{cmd.command} {' '.join(cmd.args)}"
            console.print(f"  > {full_cmd}")
            
        # 3. Ask for safety confirmation
        confirm = typer.confirm("\nDo you want to run these commands?")
        if not confirm:
            console.print("[red]Aborted.[/red]")
            raise typer.Abort()
            
        # 4. Execute the commands using subprocess with Windows Shell enabled
        for cmd in sequence.commands:
            full_cmd_list = [cmd.command] + cmd.args
            
            # This is the line that fixes the Windows file execution error!
            windows_safe_command = " ".join(full_cmd_list)
            console.print(f"[dim]Running: {windows_safe_command}...[/dim]")
            
            result = subprocess.run(windows_safe_command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"[green]Success![/green]")
            else:
                console.print(f"[bold red]Git Error:[/bold red]\n{result.stderr}")
                break # Stop running the rest of the commands if one fails
                
    except Exception as e:
        console.print(f"[bold red]System Error: {e}[/bold red]")

if __name__ == "__main__":
    app()