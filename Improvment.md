# SmartGit — Improvement Roadmap

Context: SmartGit is a CLI tool that translates natural-language intent
into Git commands using a local LLM (via Ollama), with a QLoRA fine-tuning
pipeline (Unsloth) to specialize a small Qwen2.5-Coder-1.5B model on a
synthetic dataset. The base pipeline is verified working end-to-end on
Windows + RTX 4050: data generation → fine-tuning → GGUF export → Ollama
deployment → CLI execution → real git push to GitHub.

This document lists concrete next improvements, grouped by area.

---

## 1. Training data quality (highest impact)

**Problem:** `generate_data.py` currently generates 2,000 examples that
are lexically diverse ("save my work and upload to github", "commit
everything and sync online", etc.) but *all map to the exact same
three-command output* (`git add .` → `git commit -m "update files"` →
`git push`). The model has only ever seen one target, so:
- It's very reliable at that one pattern.
- It has **no exposure** to `pull`, `status`, `branch`, `log`, `diff`,
  `checkout`, `merge`, or any command *SYSTEM_PROMPT* claims to support.
- The single hardcoded commit message ("update files") means the model
  never learns to produce a *meaningful* commit message from context.

**Improvements:**
- Add data for each other supported intent (pull/download → `git pull`;
  branch creation; status checks; viewing diffs; undoing changes safely) —
  each with **varied, appropriate JSON outputs**, not one fixed answer.
- Vary the commit message itself in training examples based on
  plausible context (e.g. "fix the login bug and push" → commit message
  referencing "fix login bug"), so the model learns to *generate*
  messages rather than always emit "update files".
- Add negative/edge-case examples: ambiguous intents, multi-step intents
  ("check status then commit"), and intents that should map to *no*
  commands (e.g. "what does git rebase do?" — a question, not an action).
- Consider generating data with an LLM (e.g. have a stronger model
  produce diverse (intent, command-sequence) pairs) rather than
  templated string concatenation, for more natural phrasing coverage.
- Track a held-out validation set so future fine-tunes can be compared
  objectively instead of eyeballing loss curves.

## 2. Safety / guardrails

**Problem:** `main.py`'s `is_safe()` check is a naive substring match
against a hardcoded list (`"reset --hard"`, `"push --force"`, `"-f"`,
`"clean -fd"`). This is easy to bypass unintentionally or intentionally:
- `"-f"` as a substring check will also block legitimate flags that
  happen to contain `-f` elsewhere (false positives), while still
  missing dangerous variants like `git push -f` written as
  `git push --force-with-lease` (not literally on the blocklist) or
  destructive commands not yet enumerated (`git branch -D`, `git
  checkout -- .` discarding uncommitted work, `git filter-branch`, etc.)
- The check operates on a naive joined string, so `args` ordering or
  spacing edge cases could slip through.

**Improvements:**
- Replace substring matching with **structured checks** on the parsed
  `command` + `args` (e.g. `cmd.command == "git" and "reset" in cmd.args
  and "--hard" in cmd.args`), which is harder to accidentally bypass.
- Expand the dangerous-command list: force pushes in all forms,
  `branch -D`, `clean` variants, `checkout --` on tracked files,
  `filter-branch`, `gc --aggressive` with prune, credential-related
  commands.
- Consider a **dry-run confirmation diff** — before executing, show
  what `git status`/`git diff --stat` looks like so the user sees the
  actual blast radius, not just the command text.
- Add a config option / flag for "always confirm destructive ops
  individually" vs. current all-or-nothing confirmation.

## 3. Error handling & UX

**Problem observed live:** "nothing to commit, working tree clean" is
a normal git state but is currently treated identically to a real
failure (red "Git Error" message), which is misleading.

**Improvements:**
- Special-case common non-error git outputs (`nothing to commit`,
  `Already up to date.`, `Everything up-to-date` for push) and print
  them as informational (yellow/blue), not red errors.
- Surface *why* the AI proposed a given command (a one-line rationale)
  so users can sanity-check intent before confirming.
- Handle the case where `generate_commands()` returns an empty command
  list gracefully (currently unclear what happens).
- Add a `--dry-run` flag that shows proposed commands without ever
  prompting to execute them — useful for testing prompts/fine-tunes.
- Add basic logging (to a local file) of intent → proposed commands →
  outcome, useful both for debugging and as a future training-data
  source (real usage, not just synthetic).

## 4. Engineering / code quality

- `engine.py` hardcodes `format=CommandSequence.model_json_schema()`
  and `temperature=0` — fine defaults, but no way to override per-call
  for exploration/testing.
- No test suite. Add unit tests for `is_safe()` (this is the most
  security-critical function in the project and currently has zero
  coverage), and integration tests that mock `ollama.chat` to verify
  `GitAgent.generate_commands()` handles malformed/unexpected model
  output without crashing.
- No handling for Ollama being unreachable (connection refused) vs. a
  model error — `main.py` currently catches all exceptions generically
  in one `except Exception as e` block, losing useful diagnostic detail.
- `main.py` comment says "Execute safely in Windows shell" but uses
  `shell=True` with string concatenation of args — on Windows this is
  reasonably safe for git's own arg parsing, but if this tool is ever
  ported to Linux/macOS, `shell=True` + naive string joining is a
  classic injection risk if any arg ever contains untrusted content
  (e.g. a commit message with backticks/semicolons). Consider
  `subprocess.run([cmd.command, *cmd.args], shell=False)` instead,
  which sidesteps shell interpretation entirely and is cross-platform.
- Add a proper `requirements.txt` / `pyproject.toml` pinning the
  versions confirmed to work (see SETUP.md from earlier in this
  conversation) so the environment is reproducible for other
  contributors, not just documented informally.

## 5. Model / deployment improvements

- Automate steps 3–4 of the pipeline (GGUF export → Ollama registration)
  with a single script instead of manual Modelfile editing — reduces
  the exact kind of path-mismatch issue hit during this session.
- Add a smoke-test script that runs a fixed set of sample intents
  against the deployed Ollama model and checks the output validates
  against `CommandSequence`, as a quick post-deploy sanity check before
  relying on a freshly fine-tuned model.
- Consider keeping the stock `qwen2.5-coder:1.5b` as a fallback model
  and only routing to the fine-tuned model for intents it's confident
  about (or vice versa) until the training data covers more commands —
  right now the fine-tune is a narrow specialist, not a strict upgrade.

## 6. Packaging

- `smartgit.spec` (PyInstaller) targets `main.py` for a standalone
  `.exe` — worth testing that the packaged executable can still reach
  a local Ollama server correctly (network/socket permissions can
  behave differently in frozen executables), and that Rich's console
  output renders correctly outside a normal terminal.

---

## Suggested priority order

1. Expand training data to cover more commands + varied commit messages
   (biggest gap between "works" and "actually useful").
2. Harden `is_safe()` with structured argument checks.
3. Fix "nothing to commit" / non-error UX handling.
4. Add `subprocess` list-form execution instead of shell string
   concatenation.
5. Everything else (tests, packaging, automation) as time allows.