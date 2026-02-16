# Backend Tests

## Database Tests

- **test_database.py** - Database connection and operation tests

## WebSocket Event Tests

These scripts test WebSocket event broadcasting from the backend to verify agent events are properly streamed.

### Test Scripts

1. **test_agent_events.py**
   - Basic WebSocket listener for debugging agent events
   - Shows all agent_log events with formatting
   - Useful for verifying events are broadcast in real-time

2. **test_display.py**
   - Rich console display with live-updating table
   - Shows agent names and tool usage in a clean format
   - Best for monitoring agent activity during development

3. **test_websocket_raw.py**
   - Raw WebSocket message logger
   - Shows ALL WebSocket messages (except heartbeats)
   - Useful for debugging what exact data is being sent

### Usage

Make sure the backend is running first:
```bash
cd ../.. && ./start_be.sh
```

Then run any test script:
```bash
# Basic agent event listener
python test_agent_events.py

# Clean display with table
python test_display.py

# Raw message debugging
python test_websocket_raw.py
```

### What to Look For

When agent events are working correctly, you should see:
- Agent names (not UUIDs) in the "Agent" column
- Tool names for ToolUseBlock events
- Real-time updates as agents execute commands
- Both hook events (PreToolUse, PostToolUse) and response events (TextBlock, ToolUseBlock)