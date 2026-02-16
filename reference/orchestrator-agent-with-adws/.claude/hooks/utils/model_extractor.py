#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Model Extractor Utility
Extracts model name from Claude Code transcript with caching.
"""

import json
import os
import time
from pathlib import Path


def get_model_from_transcript(session_id: str, transcript_path: str, ttl: int = 60) -> str:
    """
    Extract model name from transcript with file-based caching.

    Args:
        session_id: Claude session ID
        transcript_path: Path to the .jsonl transcript file
        ttl: Cache time-to-live in seconds (default: 60)

    Returns:
        Model name string (e.g., "claude-haiku-4-5-20251001") or empty string if not found
    """
    # Set up cache directory relative to this file location
    # __file__ is .claude/hooks/utils/model_extractor.py
    # We want .claude/data/claude-model-cache/
    cache_dir = Path(__file__).parent.parent.parent / "data" / "claude-model-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"{session_id}.json"
    current_time = time.time()

    # Try to read from cache
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still fresh
            cache_age = current_time - cache_data.get('timestamp', 0)
            if cache_age < ttl:
                return cache_data.get('model', '')
        except (json.JSONDecodeError, IOError):
            # Cache file corrupted or unreadable, will regenerate
            pass

    # Cache miss or stale - extract from transcript
    model_name = extract_model_from_transcript(transcript_path)

    # Save to cache
    try:
        cache_data = {
            'model': model_name,
            'timestamp': current_time,
            'ttl': ttl
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    except IOError:
        # Cache write failed, not critical - continue without cache
        pass

    return model_name


def extract_model_from_transcript(transcript_path: str) -> str:
    """
    Extract model name from transcript by finding most recent assistant message.

    Args:
        transcript_path: Path to the .jsonl transcript file

    Returns:
        Model name string or empty string if not found
    """
    if not os.path.exists(transcript_path):
        return ''

    model_name = ''

    try:
        # Read transcript file
        with open(transcript_path, 'r') as f:
            lines = f.readlines()

        # Iterate in REVERSE to find most recent assistant message with model
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)

                # Check if this is an assistant message with a model field
                # Entry structure:
                # {
                #   "type": "assistant",
                #   "message": {
                #     "model": "claude-haiku-4-5-20251001",
                #     "role": "assistant",
                #     "content": [...]
                #   }
                # }
                if (entry.get('type') == 'assistant' and
                    'message' in entry and
                    'model' in entry['message']):
                    model_name = entry['message']['model']
                    break  # Found the most recent one

            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue

    except IOError:
        # File read error
        return ''

    return model_name
