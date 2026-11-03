import typer
import subprocess
from rich.console import Console
from engine import GitAgent

app = typer.Typer()
console = Console()

# Guardrails: (subcommand, flag) pairs that must never run together.
# Checked on parsed tokens, so URLs/messages like "my-first-app" can't cause false blocks.
DANGEROUS = [
    ("reset", "--hard"),
    ("push", "--force"), ("push", "-f"), ("push", "--force-with-lease"),
    ("clean", "-f"), ("clean", "-fd"), ("clean", "-fdx"),
    ("branch", "-D"),
    ("checkout", "--"),
]

def is_safe(cmd) -> bool:
    """Only allow git, and block destructive subcommand+flag combinations."""
    if cmd.command != "git":
        return False
    for sub, flag in DANGEROUS:
        if sub in cmd.args and flag in cmd.args:
            return False
    return True

@app.command()
def main(intent: str):
    """
    Translate English into Git commands and execute them.
    """
    agent = GitAgent()

    with console.status("[bold cyan]AI is reading your repo and writing commands...", spinner="dots"):
        try:
            sequence = agent.generate_commands(intent)
        except Exception as e:
            console.print(f"[bold red]AI System Error: {e}[/bold red]")
            raise typer.Abort()

    if not sequence.commands:
        console.print("[yellow]The model didn't suggest any commands for that request.[/yellow]")
        raise typer.Abort()

    console.print("\n[bold yellow]Proposed Commands:[/bold yellow]")

    for cmd in sequence.commands:
        shown = f"{cmd.command} {' '.join(cmd.args)}"
        if not is_safe(cmd):
            console.print(f"  > [bold red]BLOCKED:[/bold red] {shown} (Dangerous command detected)")
            console.print("[red]Aborting operation to protect repository.[/red]")
            raise typer.Abort()
        console.print(f"  > {shown}", markup=False)

    if not typer.confirm("\nDo you want to run these commands?"):
        console.print("[red]Aborted.[/red]")
        raise typer.Abort()

    for cmd in sequence.commands:
        shown = f"{cmd.command} {' '.join(cmd.args)}"
        console.print(f"Running: {shown} ...", style="dim", markup=False)

        # List form, no shell: arguments (URLs, messages) are passed through untouched.
        result = subprocess.run([cmd.command, *cmd.args], capture_output=True, text=True)
        output = (result.stdout + result.stderr).strip()

        if result.returncode == 0:
            console.print("Success!", style="green")
            if output:
                console.print(output, style="dim", markup=False)
        elif "nothing to commit" in output or "up to date" in output.lower():
            console.print(output, style="yellow", markup=False)   # normal state, not an error
        else:
            console.print("Git Error:", style="bold red")
            console.print(output, markup=False)
            break

if __name__ == "__main__":
    app()