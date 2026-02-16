#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "anthropic",
# ]
# ///

"""
Event summarizer for Claude Desktop Hooks
"""

import json
import os
import sys


def generate_event_summary(event_data):
    """
    Generate a natural language summary of the event using Anthropic's API.
    
    Args:
        event_data: Dictionary containing the event information
        
    Returns:
        str: Natural language summary of the event, or None if error
    """
    # Extract key information from event
    event_type = event_data.get('hook_event_type', 'Unknown')
    session_id = event_data.get('session_id', 'Unknown')
    source_app = event_data.get('source_app', 'Unknown')
    payload = event_data.get('payload', {})
    
    # Build context for summary
    context_parts = []
    
    if event_type == 'PreToolUse' or event_type == 'PostToolUse':
        tool_name = payload.get('tool_name', 'Unknown')
        tool_input = payload.get('tool_input', {})
        context_parts.append(f"Tool: {tool_name}")
        
        # Add tool-specific context
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            if command:
                context_parts.append(f"Command: {command[:100]}...")
        elif tool_name in ['Read', 'Edit', 'Write']:
            file_path = tool_input.get('file_path', '')
            if file_path:
                context_parts.append(f"File: {file_path}")
    
    elif event_type == 'UserPromptSubmit':
        prompt = payload.get('prompt', '')
        if prompt:
            context_parts.append(f"Prompt: {prompt[:100]}...")
    
    elif event_type == 'Notification':
        message = payload.get('message', '')
        if message:
            context_parts.append(f"Message: {message}")
    
    # Create prompt for summary
    context = " | ".join(context_parts) if context_parts else "No specific context"
    
    prompt = f"""Summarize this Claude Desktop event in one concise sentence:

Event Type: {event_type}
App: {source_app}
Session: {session_id}
Context: {context}

Write a brief, natural language summary that captures what happened."""

    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast model for summaries
            max_tokens=50,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text.strip()
        
    except Exception:
        return None


def main():
    """Command line interface for testing."""
    if len(sys.argv) > 1:
        # Read event data from file
        event_file = sys.argv[1]
        try:
            with open(event_file, 'r') as f:
                event_data = json.load(f)
            
            summary = generate_event_summary(event_data)
            if summary:
                print(summary)
            else:
                print("Failed to generate summary")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Read from stdin
        try:
            event_data = json.load(sys.stdin)
            summary = generate_event_summary(event_data)
            if summary:
                print(summary)
        except Exception:
            pass


if __name__ == "__main__":
    main()