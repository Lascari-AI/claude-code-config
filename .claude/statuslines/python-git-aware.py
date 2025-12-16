#!/usr/bin/env python3
import json
import os
import sys

# Read JSON from stdin
data = json.load(sys.stdin)

# Extract values
model = data["model"]["display_name"]
current_dir = os.path.basename(data["workspace"]["current_dir"])

# ANSI color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
ORANGE = "\033[38;5;208m"
RED = "\033[31m"
RESET = "\033[0m"

# Calculate context window usage
context_info = ""
context_window = data.get("context_window", {})
context_size = context_window.get("context_window_size", 0)
current_usage = context_window.get("current_usage")

if current_usage and context_size > 0:
    current_tokens = (
        current_usage.get("input_tokens", 0)
        + current_usage.get("cache_creation_input_tokens", 0)
        + current_usage.get("cache_read_input_tokens", 0)
    )
    percent_used = (current_tokens * 100) // context_size

    # Color based on usage threshold
    if percent_used < 25:
        color = GREEN
    elif percent_used < 50:
        color = YELLOW
    elif percent_used < 75:
        color = ORANGE
    else:
        color = RED

    # Round to nearest hundred and format as thousands
    rounded_tokens = round(current_tokens / 100) * 100
    tokens_k = rounded_tokens / 1000

    context_info = f" | Context: {color}{percent_used}%{RESET} ({tokens_k:.1f}k)"
else:
    context_info = f" | Context: {GREEN}0%{RESET} (0.0k)"

# Check for git branch
git_branch = ""
if os.path.exists(".git"):
    try:
        with open(".git/HEAD", "r") as f:
            ref = f.read().strip()
            if ref.startswith("ref: refs/heads/"):
                git_branch = f" | 🌿 {ref.replace('ref: refs/heads/', '')}"
    except:
        pass

print(f"[{model}] 📁 {current_dir}{git_branch}{context_info}")
