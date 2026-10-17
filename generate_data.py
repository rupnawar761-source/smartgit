import json
import random
from collections import Counter

from prompt import SYSTEM_PROMPT   # train on the SAME prompt engine.py uses at inference

random.seed(42)

# ---------- helpers ----------
def g(*args):
    return {"command": "git", "args": list(args)}

# Sample repo states, injected the same way engine.py injects them
STATUSES = [
    "No changes detected.",
    " M main.py",
    " M engine.py\n M prompt.py",
    "?? notes.txt",
    "A  README.md\n M train.py",
    "?? new_feature.py\n M main.py",
    " D old_script.py",
]

COMMIT_MESSAGES = [
    "fix login bug", "add readme", "update documentation", "refactor engine",
    "add unit tests", "fix typo", "initial commit", "update dependencies",
    "improve error handling", "add new feature", "clean up code", "update config",
]
BRANCH_NAMES = ["dev", "feature-login", "bugfix", "testing", "experiment", "release", "ui-update", "hotfix"]
FILE_NAMES = ["main.py", "engine.py", "README.md", "train.py", "notes.txt", "prompt.py"]

# ---------- intent definitions ----------
# Each intent: list of phrasings (may contain {m}, {b}, {f}, {n}) + builder for the commands.
INTENTS = {}

def intent(name, phrasings, builder, needs=None):
    INTENTS[name] = (phrasings, builder, needs)

intent("status",
    ["show status", "what changed", "check my repo status", "which files did I modify",
     "show me the current state of my repo", "git status please", "are there any uncommitted changes",
     "what files are modified"],
    lambda v: [g("status")])

intent("pull",
    ["pull the latest changes", "download updates", "get the latest code", "sync from github",
     "update my local repo", "fetch and merge the newest changes", "download the latest version",
     "bring my repo up to date"],
    lambda v: [g("pull")])

intent("push",
    ["push my commits", "upload my commits", "send my commits to github", "push to origin",
     "upload my changes to the cloud", "publish my commits", "push everything online"],
    lambda v: [g("push")])

intent("add_all",
    ["stage all files", "add everything", "track all my changes", "stage all changes",
     "add all modified files"],
    lambda v: [g("add", ".")])

intent("add_file",
    ["stage {f}", "add {f}", "track {f}", "add only {f} to the next commit"],
    lambda v: [g("add", v["f"])], needs=["f"])

intent("commit_msg",
    ['commit with message "{m}"', 'save my work with message "{m}"', 'commit my changes: {m}',
     'record my changes as "{m}"', 'commit everything with the message {m}', 'save changes, message: {m}'],
    lambda v: [g("add", "."), g("commit", "-m", v["m"])], needs=["m"])

intent("commit_generic",
    ["save my work", "commit my changes", "add and commit my changes", "commit everything",
     "backup my code", "record my progress", "save the files"],
    lambda v: [g("add", "."), g("commit", "-m", "update files")])

intent("save_push",
    ["save my work and push to github", "commit and push", "commit my changes and push",
     "backup my code and upload it", "update my files and send them online",
     "save everything and sync to origin", "record my changes and push them"],
    lambda v: [g("add", "."), g("commit", "-m", "update files"), g("push")])

intent("save_push_msg",
    ['commit with message "{m}" and push', 'save my work as "{m}" and push to github',
     'commit everything: {m}, then upload it'],
    lambda v: [g("add", "."), g("commit", "-m", v["m"]), g("push")], needs=["m"])

intent("log",
    ["show commit history", "show the git log", "what are my previous commits",
     "list past commits", "show history"],
    lambda v: [g("log", "--oneline")])

intent("log_n",
    ["show the last {n} commits", "show my last {n} commits", "list the latest {n} commits"],
    lambda v: [g("log", "--oneline", "-n", v["n"])], needs=["n"])

intent("diff",
    ["show what I changed", "show differences", "what is different from the last commit",
     "show the diff", "show my uncommitted changes in detail"],
    lambda v: [g("diff")])

intent("branch_list",
    ["list branches", "show all branches", "what branches do I have", "which branch exist"],
    lambda v: [g("branch")])

intent("branch_new",
    ["create a branch called {b}", "make a new branch named {b}", "start a new branch {b}",
     "new branch {b}", "create and switch to branch {b}"],
    lambda v: [g("checkout", "-b", v["b"])], needs=["b"])

intent("branch_switch",
    ["switch to {b}", "go to branch {b}", "checkout {b}", "change to the {b} branch"],
    lambda v: [g("checkout", v["b"])], needs=["b"])

intent("branch_delete",
    ["delete branch {b}", "remove the {b} branch", "get rid of branch {b}"],
    lambda v: [g("branch", "-d", v["b"])], needs=["b"])

intent("merge",
    ["merge {b} into my current branch", "merge branch {b}", "combine {b} with this branch",
     "bring the changes from {b} into this branch"],
    lambda v: [g("merge", v["b"])], needs=["b"])

intent("stash",
    ["stash my changes", "put my changes aside", "temporarily save my work without committing",
     "shelve my modifications"],
    lambda v: [g("stash")])

intent("stash_pop",
    ["restore my stashed changes", "bring back my stash", "apply the stash", "unstash my work"],
    lambda v: [g("stash", "pop")])

intent("undo_commit",
    ["undo my last commit but keep the changes", "uncommit the last commit and keep my files",
     "take back the last commit, keep my work"],
    lambda v: [g("reset", "--soft", "HEAD~1")])

intent("unstage",
    ["unstage everything", "unstage all files", "remove all files from the staging area"],
    lambda v: [g("restore", "--staged", ".")])

intent("remote",
    ["show remote url", "where does this repo push to", "show my remotes", "what is the origin url"],
    lambda v: [g("remote", "-v")])

intent("init",
    ["initialize a git repo", "start a new git repository here", "git init", "make this folder a repo"],
    lambda v: [g("init")])

intent("pull_then_push",
    ["pull the latest and then push my commits", "sync with github in both directions",
     "update from remote then upload my commits"],
    lambda v: [g("pull"), g("push")])

# ---------- generation ----------
def fill(template, v):
    return template.format(**v)

def make_vars(needs):
    v = {}
    if needs:
        if "m" in needs: v["m"] = random.choice(COMMIT_MESSAGES)
        if "b" in needs: v["b"] = random.choice(BRANCH_NAMES)
        if "f" in needs: v["f"] = random.choice(FILE_NAMES)
        if "n" in needs: v["n"] = str(random.choice([3, 5, 10]))
    return v

SAMPLES_PER_INTENT = 40   # cap; small intents simply dedupe down
dataset, seen, counts = [], set(), Counter()

for name, (phrasings, builder, needs) in INTENTS.items():
    for _ in range(SAMPLES_PER_INTENT * 3):          # oversample, dedupe below
        if counts[name] >= SAMPLES_PER_INTENT:
            break
        v = make_vars(needs)
        user_text = fill(random.choice(phrasings), v)
        if random.random() < 0.3:                    # light casing/punctuation noise
            user_text = random.choice([user_text.capitalize(), user_text + ".", user_text + " please"])
        status = random.choice(STATUSES)
        key = (user_text, status)
        if key in seen:
            continue
        seen.add(key)

        # EXACT same system content engine.py builds at inference time
        system_content = f"{SYSTEM_PROMPT}\n\nCURRENT REPOSITORY STATUS (Git Status):\n{status}"
        answer = {"commands": builder(v)}

        dataset.append({"messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(answer)},   # valid JSON, no extra escaping
        ]})
        counts[name] += 1

random.shuffle(dataset)

with open("git_dataset.jsonl", "w", encoding="utf-8") as f:
    for item in dataset:
        f.write(json.dumps(item) + "\n")

print(f"Success! Generated {len(dataset)} training examples across {len(INTENTS)} intents.")
for k, c in sorted(counts.items()):
    print(f"  {k:16s} {c}")