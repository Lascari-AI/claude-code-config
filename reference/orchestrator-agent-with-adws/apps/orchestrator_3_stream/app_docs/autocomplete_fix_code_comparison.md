# Code Comparison: Autocomplete Session Fix

## 🔴 BEFORE (Broken)

### Missing Import
```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    SystemMessage,
    TextBlock,
    # ❌ ResultMessage missing!
)
```

### Broken Message Handler
```python
async for message in self.client.receive_response():
    message_count += 1

    if isinstance(message, SystemMessage):
        # ❌ WRONG: session_id is NOT a direct attribute!
        session_id = getattr(message, "session_id", None)  # Always None!
        continue

    if isinstance(message, AssistantMessage):
        # ... handle text blocks ...
        pass

    # ❌ MISSING: No ResultMessage handler!

# Later...
if session_id and not self.expertise_data.completion_agent_id:
    self.expertise_data.completion_agent_id = session_id  # Never executes!
```

**Result:** `completion_agent_id` always stays `null` ❌

---

## 🟢 AFTER (Fixed)

### Added Import
```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    SystemMessage,
    TextBlock,
    ResultMessage,  # ✅ ADDED
)
```

### Fixed Message Handler
```python
async for message in self.client.receive_response():
    message_count += 1

    if isinstance(message, SystemMessage):
        # ✅ CORRECT: Extract from data dictionary
        data = getattr(message, "data", {})
        subtype = getattr(message, "subtype", "unknown")
        extracted_session = data.get("session_id") if isinstance(data, dict) else None
        if extracted_session:
            session_id = extracted_session
        self.logger.debug(
            f"SystemMessage received (subtype: {subtype}, session_id: {session_id[:20] if session_id else 'None'}...)"
        )
        continue

    if isinstance(message, AssistantMessage):
        # ... handle text blocks ...
        pass

    # ✅ ADDED: ResultMessage handler
    elif isinstance(message, ResultMessage):
        session_id = message.session_id  # Direct attribute
        self.logger.debug(
            f"ResultMessage received (session_id: {session_id[:20] if session_id else 'None'}...)"
        )

# Later...
if session_id and not self.expertise_data.completion_agent_id:
    self.expertise_data.completion_agent_id = session_id  # ✅ Now executes!
    self._save_expertise()
    self.logger.info(f"Captured autocomplete session_id: {session_id[:20]}...")
```

**Result:** `completion_agent_id` gets captured and saved! ✅

---

## 📊 Side-by-Side Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **ResultMessage import** | ❌ Missing | ✅ Added |
| **SystemMessage handling** | ❌ Wrong pattern | ✅ Correct pattern |
| **ResultMessage handling** | ❌ Not handled | ✅ Properly handled |
| **session_id capture** | ❌ Always fails | ✅ Always works |
| **expertise.yaml** | `completion_agent_id: null` | `completion_agent_id: "msg_bdrk_..."` |
| **Session resumption** | ❌ Never resumes | ✅ Resumes correctly |

---

## 🎯 Key Learning

**Claude Agent SDK sends session_id in TWO places:**

1. **SystemMessage.data["session_id"]** (from data dict)
2. **ResultMessage.session_id** (direct attribute)

**Our fix handles BOTH** to ensure session_id is captured reliably!

---

## 📚 Reference Implementation

This pattern is used successfully in:

### orchestrator_service.py
```python
# SystemMessage handling (lines 556-604)
if isinstance(message, SystemMessage):
    data = getattr(message, "data", {})
    session_id = data.get("session_id")  # ✅ From data dict

# ResultMessage handling (lines 752-756)
elif isinstance(message, ResultMessage):
    final_session_id = message.session_id  # ✅ Direct attribute
```

### agent_manager.py
```python
# SystemMessage handling (lines 1022-1035)
if isinstance(message, SystemMessage):
    data = getattr(message, 'data', {})  # ✅ From data dict

# ResultMessage handling (lines 1178-1179)
elif isinstance(message, ResultMessage):
    session_id = message.session_id  # ✅ Direct attribute
```

**Now autocomplete_agent.py follows the same proven pattern!** 🎉
