import ollama
from prompt import SYSTEM_PROMPT, CommandSequence

def generate_git_commands(user_intent: str) -> CommandSequence:
    # Pass the pydantic schema to the format parameter to enforce JSON output
    response = ollama.chat(
        model='qwen2.5-coder:1.5b',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_intent}
        ],
        format=CommandSequence.model_json_schema(),
        options={'temperature': 0} 
    )
    
    # Parse the JSON string back into our Pydantic object
    return CommandSequence.model_validate_json(response.message.content)

if __name__ == "__main__":
    print("Testing local Ollama connection...")
    try:
        result = generate_git_commands("save my work as 'fixed the login bug'")
        print("\nSuccess! The model returned:")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure Ollama is running in the background!")