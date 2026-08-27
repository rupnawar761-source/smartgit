import json
import random

# 1. Define our variations of English prompts
save_verbs = ["save", "commit", "update", "backup", "record"]
save_nouns = ["my work", "the files", "changes", "my code", "everything"]
push_verbs = ["upload", "push", "send", "sync"]
push_nouns = ["to github", "to the cloud", "to origin", "online"]

# 2. The exact JSON output the model MUST learn to generate
ideal_json_output = {
    "commands": [
        {"command": "git", "args": ["add", "."]},
        {"command": "git", "args": ["commit", "-m", "update files"]},
        {"command": "git", "args": ["push"]}
    ]
}
ideal_json_string = json.dumps(ideal_json_output).replace('"', '\\"')

# 3. Generate the dataset
dataset = []
for sv in save_verbs:
    for sn in save_nouns:
        for pv in push_verbs:
            for pn in push_nouns:
                # Combine words to make natural sentences
                prompt = f"{sv} {sn} and {pv} {pn}"
                
                # Format into the exact instruction structure required for training
                training_pair = {
                    "messages": [
                        {"role": "system", "content": "Translate English into a strict JSON sequence of Git commands."},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": ideal_json_string}
                    ]
                }
                dataset.append(training_pair)

# 4. Save to a JSONL file
with open("git_dataset.jsonl", "w") as f:
    for item in dataset:
        f.write(json.dumps(item) + "\n")

print(f"Success! Generated {len(dataset)} training examples.")