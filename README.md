# SmartGit 🤖

Translate plain English into Git commands, powered by a locally fine-tuned LLM. No cloud calls, no API keys — just a local model, running on your own machine via [Ollama](https://ollama.com), turning intent into safe, reviewable Git actions.

```
$ python main.py "save my work and push to github"

Proposed Commands:
  > git add .
  > git commit -m "update files"
  > git push

Do you want to run these commands? [y/N]:
```

## How it works

1. **You describe what you want** in plain English.
2. The current `git status` of your repo is captured and injected into the model's context.
3. A local LLM (fine-tuned via QLoRA on a small Qwen2.5-Coder-1.5B) translates your intent into a structured JSON sequence of Git commands, validated against a strict schema.
4. Every proposed command is checked against a **safety guardrail** that blocks destructive operations (force pushes, hard resets, etc.) before you're ever asked to confirm.
5. Nothing runs without your explicit `y/N` confirmation.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | CLI entry point — orchestrates the propose → confirm → execute flow |
| `engine.py` | `GitAgent` class — talks to Ollama, builds context-aware prompts |
| `prompt.py` | System prompt + Pydantic schema (`CommandSequence`) the model must output |
| `generate_data.py` | Generates synthetic training data (English → JSON pairs) |
| `train.py` | QLoRA fine-tuning script (Unsloth), trains a LoRA adapter on the base model |
| `export_gguf.py` | Merges the LoRA adapter into the base model and exports to GGUF for Ollama |
| `smartgit.spec` | PyInstaller spec for building a standalone `.exe` |

## Setup

**Requirements:** Python 3.10–3.11, [Ollama](https://ollama.com) installed and running, an NVIDIA GPU for fine-tuning (inference alone can run CPU-only via Ollama).

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install ollama typer rich pydantic

ollama pull qwen2.5-coder:1.5b
python main.py "commit my changes and push"
```

## Fine-tuning your own model (optional)

The repo ships with a full QLoRA fine-tuning pipeline if you want to specialize the model further on your own command patterns.

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install unsloth transformers==4.56.2 torchao==0.9.0
pip install "triton-windows<3.3"   # Windows only

python generate_data.py     # generates git_dataset.jsonl
python train.py             # fine-tunes, saves to lora_model/
python export_gguf.py       # merges + exports to GGUF

ollama create smartgit-qwen -f Modelfile
```

Then point `GitAgent`'s default `model_name` in `engine.py` at your new Ollama tag.

See [SETUP.md](./SETUP.md) for exact verified package versions and troubleshooting notes for common Windows/CUDA/Triton issues.

## Safety

`main.py` checks every proposed command against a blocklist before execution (`reset --hard`, `push --force`, `-f`, `clean -fd`) and always requires explicit confirmation. This is a first line of defense, not a guarantee — review proposed commands before confirming, especially on unfamiliar phrasing.

## Roadmap

See [IMPROVEMENTS.md](./IMPROVEMENTS.md) for planned improvements, including expanded training data coverage (`pull`, `status`, `branch`), stronger safety-check structure, and better error-state UX.

## License

MIT
