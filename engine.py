import subprocess
import ollama
from prompt import SYSTEM_PROMPT, CommandSequence

class GitAgent:
    # UPGRADE 5: Model Swapping is now as easy as changing this one string
    def __init__(self, model_name: str = "qwen2.5-coder:1.5b"):
        self.model = model_name
        
    def get_git_status(self) -> str:
        """Silently check what files changed to give the AI eyes."""
        try:
            result = subprocess.run("git status --short", shell=True, capture_output=True, text=True)
            return result.stdout.strip() if result.stdout else "No changes detected."
        except Exception:
            return "Could not retrieve git status."

    def generate_commands(self, user_intent: str) -> CommandSequence:
        # UPGRADE 1: Context Injection
        status = self.get_git_status()
        contextual_prompt = f"{SYSTEM_PROMPT}\n\nCURRENT REPOSITORY STATUS (Git Status):\n{status}"
        
        # UPGRADE 2: Encapsulated OOP Logic
        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': contextual_prompt},
                {'role': 'user', 'content': user_intent}
            ],
            format=CommandSequence.model_json_schema(),
            options={'temperature': 0} 
        )
        
        return CommandSequence.model_validate_json(response.message.content)