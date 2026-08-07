from pydantic import BaseModel
from typing import List

# 1. Define the exact JSON structure we want back from the LLM
class GitCommand(BaseModel):
    command: str
    args: List[str]

class CommandSequence(BaseModel):
    commands: List[GitCommand]

# 2. Write the strict instructions for the AI
SYSTEM_PROMPT = """
You are an expert Git command generator. 
The user will provide a natural language description of what they want to do in Git.
Your job is to translate this into a sequence of valid Git commands.

CRITICAL RULES:
- Never output markdown, code blocks, or conversational explanations.
- Only output a valid JSON object matching the requested schema.
- If the user asks to "save" or "track", use `git add .` and `git commit -m "message"`.
- If the user asks to "upload", use `git push`.
- If the user asks to "download" or "update", use `git pull`.
"""