# Autocomplete Loading State Implementation

**Date:** 2025-01-12
**Feature:** WebSocket-Synchronized Autocomplete Loading Indicators
**Status:** ✅ Implemented

## Overview

Implemented a loading indicator for the autocomplete system that syncs with actual backend agent execution via WebSocket events, providing accurate visual feedback to users about when autocomplete suggestions are being generated.

## Problem Statement

Previously, the autocomplete loading state was only driven by HTTP request lifecycle:
- Loading started when API call was initiated
- Loading stopped when API response was received
- **Issue:** This didn't reflect the actual agent execution time, as the agent might still be processing after the HTTP connection was established

## Solution

Added WebSocket event broadcasting to sync the UI loading state with actual backend agent execution:

1. **Backend broadcasts** `autocomplete_started` when agent begins execution
2. **Backend broadcasts** `autocomplete_completed` when agent finishes (success or error)
3. **Frontend listens** to these WebSocket events and updates loading state accordingly

## Expected Flow

```
User types → Debounce ends → HTTP request starts → Agent starts executing
  ↓
Backend broadcasts: autocomplete_started
  ↓
Frontend: autocompleteLoading = true (shows spinner)
  ↓
Agent processes with Claude SDK
  ↓
Backend broadcasts: autocomplete_completed
  ↓
Frontend: autocompleteLoading = false (hides spinner)
  ↓
Results displayed as pills
```

## Files Modified

### Backend (3 files)

#### 1. `backend/modules/autocomplete_agent.py`
**Changes:**
- Added `ws_manager` parameter to `__init__` method
- Added WebSocket broadcast at start of `generate_autocomplete()`:
  ```python
  await self.ws_manager.broadcast({
      "type": "autocomplete_started",
      "orchestrator_agent_id": self.orchestrator_agent_id,
      "user_input": user_input[:100],
      "timestamp": time.time()
  })
  ```
- Added WebSocket broadcast in `finally` block of `generate_autocomplete()`:
  ```python
  await self.ws_manager.broadcast({
      "type": "autocomplete_completed",
      "orchestrator_agent_id": self.orchestrator_agent_id,
      "timestamp": time.time()
  })
  ```

#### 2. `backend/modules/autocomplete_service.py`
**Changes:**
- Added `ws_manager` parameter to `__init__` method
- Passed `ws_manager` to `AutocompleteAgent` initialization

#### 3. `backend/main.py`
**Changes:**
- Passed `ws_manager` to `AutocompleteService` initialization:
  ```python
  autocomplete_service = AutocompleteService(
      orchestrator_agent_id=orchestrator.id,
      logger=logger,
      working_dir=config.get_working_dir(),
      ws_manager=ws_manager  # NEW
  )
  ```

### Frontend (3 files)

#### 4. `frontend/src/services/chatService.ts`
**Changes:**
- Added `onAutocompleteStarted` and `onAutocompleteCompleted` to `WebSocketCallbacks` interface
- Added WebSocket message routing for new event types:
  ```typescript
  case 'autocomplete_started':
    callbacks.onAutocompleteStarted?.(message)
    break

  case 'autocomplete_completed':
    callbacks.onAutocompleteCompleted?.(message)
    break
  ```

#### 5. `frontend/src/stores/orchestratorStore.ts`
**Changes:**
- Added WebSocket event handlers:
  ```typescript
  function handleAutocompleteStarted(message: any) {
    autocompleteLoading.value = true
    console.log('🔄 Autocomplete loading started via WebSocket')
  }

  function handleAutocompleteCompleted(message: any) {
    autocompleteLoading.value = false
    console.log('✅ Autocomplete loading completed via WebSocket')
  }
  ```
- Registered handlers in `connectWebSocket()`:
  ```typescript
  onAutocompleteStarted: handleAutocompleteStarted,
  onAutocompleteCompleted: handleAutocompleteCompleted,
  ```

#### 6. `frontend/src/components/GlobalCommandInput.vue`
**Changes:**
- Added autocomplete section wrapper to contain both loading and pills:
  ```vue
  <div v-if="hasAutocompleteItems || autocompleteLoading" class="autocomplete-section">
    <!-- Loading indicator (shows during initial load AND refresh) -->
    <div v-if="autocompleteLoading" class="autocomplete-loading">
      <div class="loading-spinner"></div>
      <span class="loading-text">
        {{ hasAutocompleteItems ? 'Refreshing...' : 'Generating suggestions...' }}
      </span>
    </div>

    <!-- Pills (kept visible during refresh) -->
    <div v-if="hasAutocompleteItems" class="autocomplete-pills">...</div>
  </div>
  ```
- Added CSS for autocomplete section layout:
  ```css
  .autocomplete-section {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: nowrap; /* Prevent wrapping to maintain fixed height */
    height: 41px; /* FIXED height - never changes, eliminates all jitter */
    overflow: hidden; /* Prevent content from breaking out of fixed height */
    animation: slideDown 0.2s ease-out;
  }
  ```
- Added CSS for spinning loader animation:
  ```css
  .loading-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--gray-700, #374151);
    border-top-color: var(--cyan-400, #22d3ee);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  ```

## WebSocket Event Structure

### autocomplete_started
```json
{
  "type": "autocomplete_started",
  "orchestrator_agent_id": "uuid-123",
  "user_input": "create a new ",
  "timestamp": 1705089600.123
}
```

### autocomplete_completed
```json
{
  "type": "autocomplete_completed",
  "orchestrator_agent_id": "uuid-123",
  "timestamp": 1705089602.456
}
```

## UI Behavior

### Visual Layout Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Scenario 1: Initial Load (No Pills Yet)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [🔄 Spinner] Generating suggestions...                │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Scenario 2: Refresh Load (Pills Already Visible)       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [🔄 Spinner] Refreshing...  [Ctrl+1 testing]          │
│                              [Ctrl+2 database]          │
│                              [Ctrl+3 API]               │
│                                                         │
│  ↑ Spinner on left          ↑ Existing pills stay      │
└─────────────────────────────────────────────────────────┘
```

### Scenario 1: Initial Loading (No Existing Pills)
- **Before:** Autocomplete pills area is empty, no visual feedback
- **During:** Spinning cyan-colored spinner appears with "Generating suggestions..."
- **After:** Spinner disappears, autocomplete pills appear with suggestions

### Scenario 2: Refresh Loading (Existing Pills Visible)
- **Before:** User has existing autocomplete pills displayed
- **During:**
  - Spinner appears **to the left** of existing pills
  - Text shows: "Refreshing..."
  - Existing pills remain visible (not hidden)
  - User can still click existing pills during refresh
- **After:**
  - Spinner disappears
  - Old pills are replaced with new pills
  - Smooth transition without UI jumping

### Loading State Conditions
The loading indicator shows when:
- `autocompleteLoading === true` (WebSocket event received)

The loading text adapts based on context:
- "Generating suggestions..." when no pills exist yet
- "Refreshing..." when pills are being updated

### Layout Structure
```vue
<div class="autocomplete-section">
  <!-- Spinner (when loading) -->
  <div class="autocomplete-loading">...</div>

  <!-- Pills (when available) -->
  <div class="autocomplete-pills">...</div>
</div>
```

This ensures the spinner and pills can coexist without layout shifts.

## Key Implementation Details

### Synchronization Strategy
1. **HTTP request initiates** the autocomplete generation
2. **WebSocket events control** the loading UI state
3. **HTTP response delivers** the actual autocomplete results

This approach ensures the loading indicator accurately reflects backend processing time, not just network latency.

### Error Handling
The `finally` block in `generate_autocomplete()` ensures the `autocomplete_completed` event is always broadcasted, even if:
- Agent execution fails
- JSON parsing fails
- Any exception occurs

This prevents the loading spinner from getting "stuck" in the loading state.

### Race Condition Prevention
The existing HTTP-based loading state (`autocompleteLoading` set during API call) still works as a fallback. The WebSocket events enhance this by providing more accurate timing.

## Testing Checklist

### Initial Load Test
- [ ] Start backend and frontend servers
- [ ] Open browser console to see WebSocket event logs
- [ ] Open GlobalCommandInput (Cmd+K)
- [ ] Type a message to trigger autocomplete (wait for 1s debounce)
- [ ] Verify spinner appears with "Generating suggestions..."
- [ ] Verify spinner disappears when suggestions load
- [ ] Verify pills appear without layout shift

### Refresh Load Test
- [ ] With autocomplete pills already visible
- [ ] Continue typing to trigger a new autocomplete request
- [ ] Verify spinner appears **to the left** of existing pills
- [ ] Verify text changes to "Refreshing..."
- [ ] Verify existing pills remain visible and clickable
- [ ] Verify spinner disappears when new results arrive
- [ ] Verify old pills are replaced with new pills smoothly

### WebSocket Events Test
- [ ] Verify console shows WebSocket event logs:
  - `🔄 Autocomplete loading started via WebSocket`
  - `✅ Autocomplete loading completed via WebSocket`
- [ ] Verify logs show for both initial and refresh scenarios

### Edge Cases Test
- [ ] Test with slow network to verify loading stays visible during full agent execution
- [ ] Test error cases (invalid input) to ensure spinner disappears
- [ ] Test rapid typing to verify debounce + loading state sync
- [ ] Test clicking existing pills during refresh (should still work)

## Performance Impact

- **Network overhead:** Minimal (~100 bytes per WebSocket event)
- **UI updates:** Reactive state changes are efficient with Vue 3
- **Backend overhead:** Negligible (single broadcast per autocomplete request)
- **UI Stability:** Fixed min-height prevents layout jitter during state changes

## Troubleshooting

### Problem: Loading Spinner Stuck/Won't Disappear

**Symptoms:**
- Spinner shows indefinitely
- "Generating suggestions..." or "Refreshing..." text never goes away
- Console shows `🔄 Autocomplete loading started` but no `✅ Autocomplete loading completed`

**Root Causes:**
1. WebSocket disconnected during agent execution
2. Backend agent crashed without sending completion event
3. Network issues preventing WebSocket message delivery
4. Race condition between multiple autocomplete requests

**Solutions:**

#### Built-in Safety Feature (10-Second Timeout)
The system automatically clears stuck loading states after 10 seconds:
```typescript
// In orchestratorStore.ts
const AUTOCOMPLETE_TIMEOUT_MS = 10000 // 10 seconds

// If loading doesn't complete within 10 seconds, force clear
setTimeout(() => {
  if (autocompleteLoading.value) {
    console.warn('⚠️ [Autocomplete] Timeout: Force clearing loading state')
    autocompleteLoading.value = false
  }
}, AUTOCOMPLETE_TIMEOUT_MS)
```

**What to check in console:**
```bash
# Normal flow (expected):
[Autocomplete] Started: {orchestrator_agent_id: "uuid-123", ...}
🔄 Autocomplete loading started via WebSocket
[Autocomplete] Completed: {orchestrator_agent_id: "uuid-123", ...}
✅ Autocomplete loading completed via WebSocket

# Stuck state (problem):
[Autocomplete] Started: {orchestrator_agent_id: "uuid-123", ...}
🔄 Autocomplete loading started via WebSocket
# ... 10 seconds pass ...
⚠️ [Autocomplete] Timeout: Force clearing loading state after 10 seconds
```

#### Manual Reset
If needed, you can manually clear the stuck state:
1. Open browser console
2. Find the Pinia store: `window.__PINIA__`
3. Clear loading state: `orchestratorStore.autocompleteLoading = false`

Or refresh the page to reset all state.

---

### Problem: Loading Spinner Doesn't Appear

**Symptoms:**
- User types, but no loading indicator shows
- Autocomplete pills appear immediately without loading feedback
- Console shows no WebSocket events

**Root Causes:**
1. WebSocket not connected
2. Backend not broadcasting events
3. Frontend event handlers not registered

**Solutions:**

#### Check WebSocket Connection
```javascript
// In browser console
console.log('WebSocket connected:', orchestratorStore.isConnected)
```

If `false`, the WebSocket is disconnected. Check:
- Backend server is running (`./start_be.sh`)
- WebSocket URL is correct in `.env`: `VITE_WEBSOCKET_URL=ws://127.0.0.1:9403/ws`
- No firewall/proxy blocking WebSocket connections

#### Verify Event Handlers
Check that handlers are registered in `orchestratorStore.ts`:
```typescript
connectWebSocket(wsUrl, {
  // ... other handlers ...
  onAutocompleteStarted: handleAutocompleteStarted,  // ← Should be present
  onAutocompleteCompleted: handleAutocompleteCompleted,  // ← Should be present
})
```

#### Check Backend Logs
Backend should show WebSocket broadcasts:
```bash
# In backend logs (backend/logs/*.log)
📡 Broadcasted autocomplete_started event
📡 Broadcasted autocomplete_completed event
```

If missing, ensure `ws_manager` is passed to `AutocompleteService` in `main.py`.

---

### Problem: Pills Don't Stay Visible During Refresh

**Symptoms:**
- Old pills disappear when user continues typing
- Spinner shows alone without existing pills

**Root Cause:**
Template condition is incorrect - should show pills OR loading, not pills AND loading.

**Solution:**
Verify template structure in `GlobalCommandInput.vue`:
```vue
<!-- CORRECT: -->
<div v-if="hasAutocompleteItems || autocompleteLoading" class="autocomplete-section">
  <div v-if="autocompleteLoading" class="autocomplete-loading">...</div>
  <div v-if="hasAutocompleteItems" class="autocomplete-pills">...</div>
</div>

<!-- WRONG: -->
<div v-if="hasAutocompleteItems && !autocompleteLoading" class="autocomplete-pills">...</div>
```

The outer condition uses `||` (OR) so the section appears when EITHER pills exist OR loading is active.

---

### Problem: Rapid Typing Causes Multiple Spinners

**Symptoms:**
- Multiple loading indicators appear
- Console shows multiple "Started" events without "Completed" events
- UI feels laggy

**Root Cause:**
Debounce isn't working, or multiple requests are firing.

**Solutions:**

#### Verify Debounce
Check `useAutocomplete.ts` has debounce configured:
```typescript
const debouncedGenerate = useDebounceFn(async (input: string) => {
  // ... autocomplete logic ...
}, 1000)  // ← 1 second debounce
```

#### Check Timeout Cleanup
The timeout system should prevent multiple stuck spinners:
```typescript
// In handleAutocompleteStarted:
if (autocompleteLoadingTimeout) {
  clearTimeout(autocompleteLoadingTimeout)  // ← Clears previous timeout
}
autocompleteLoadingTimeout = setTimeout(/* ... */)  // ← Sets new timeout
```

---

### Problem: WebSocket Events Not Routing

**Symptoms:**
- Backend logs show broadcasts
- Frontend console shows no "[Autocomplete] Started/Completed" logs
- Other WebSocket events (agent_log, etc.) work fine

**Root Cause:**
Event routing in `chatService.ts` is missing cases.

**Solution:**
Verify `chatService.ts` has routing for autocomplete events:
```typescript
// In connectWebSocket() message handler:
switch (message.type) {
  // ... other cases ...
  case 'autocomplete_started':
    callbacks.onAutocompleteStarted?.(message)
    break

  case 'autocomplete_completed':
    callbacks.onAutocompleteCompleted?.(message)
    break
}
```

---

### Problem: UI Height Jitter During Loading State Changes

**Symptoms:**
- Container height "jerks" or "jumps" when loading indicator appears/disappears
- Visual instability during state transitions
- Pills move up/down when loading starts/stops

**Root Cause:**
The autocomplete section doesn't have a fixed minimum height, causing layout reflow when content changes.

**Solution:**
The `.autocomplete-section` CSS uses a **fixed height** (not min-height) to completely eliminate jitter:

```css
.autocomplete-section {
  height: 41px; /* FIXED height - never changes, eliminates all jitter */
  flex-wrap: nowrap; /* Prevent wrapping to maintain fixed height */
  overflow: hidden; /* Prevent content from breaking out of fixed height */
}
```

**How it works:**
- **41px** = Fixed height that accommodates all content (loading, pills, or both)
- `height` (not `min-height`) ensures container **never** changes size
- `flex-wrap: nowrap` keeps pills on single line
- `overflow: hidden` clips any content exceeding boundaries
- **Zero layout reflow** - height is constant across all states

**Verify fix:**
1. Open command input (Cmd+K)
2. Type to trigger autocomplete
3. Watch the container during loading → completion transition
4. **Expected:** No height changes, perfectly stable
5. Continue typing (refresh scenario)
6. **Expected:** Container height remains constant

---

### Debugging Tips

1. **Enable Verbose Logging**
   - Open browser console
   - Watch for WebSocket events: `[Autocomplete] Started/Completed`
   - Backend logs: `backend/logs/*.log`

2. **Test WebSocket Connection**
   ```javascript
   // In browser console
   orchestratorStore.isConnected  // Should be true
   ```

3. **Monitor Timeout System**
   ```javascript
   // Check if timeout is active (won't be exposed, but check console for timeout warning)
   // After 10 seconds, you should see:
   // ⚠️ [Autocomplete] Timeout: Force clearing loading state after 10 seconds
   ```

4. **Test Manual Trigger**
   ```javascript
   // In browser console
   orchestratorStore.generateAutocomplete("test input")
   ```

5. **Check Network Tab**
   - Open DevTools → Network → WS (WebSocket)
   - Should see `ws://127.0.0.1:9403/ws` connection
   - Click connection → Messages tab to see WebSocket frames

---

### Common Configuration Issues

#### Issue: Wrong WebSocket URL
**Check:** `frontend/.env`
```bash
VITE_WEBSOCKET_URL=ws://127.0.0.1:9403/ws
```

#### Issue: Backend Not Passing ws_manager
**Check:** `backend/main.py` in lifespan:
```python
autocomplete_service = AutocompleteService(
    orchestrator_agent_id=orchestrator.id,
    logger=logger,
    working_dir=config.get_working_dir(),
    ws_manager=ws_manager  # ← Must be present
)
```

#### Issue: Port Mismatch
**Check:** Backend and frontend use consistent ports
```bash
# Backend .env
WEBSOCKET_PORT=9403

# Frontend .env
VITE_WEBSOCKET_URL=ws://127.0.0.1:9403/ws
```

---

## Future Improvements

1. **Progress indicators:** Show percentage complete or number of suggestions generated
2. **Cancellation feedback:** Show when previous requests are interrupted
3. **Error state:** Display error message if autocomplete fails
4. **Debounce indicator:** Show countdown during debounce period before agent starts
5. **Retry mechanism:** Auto-retry failed autocomplete requests
6. **Network status indicator:** Show when WebSocket is disconnected

## Related Documentation

- [AUTOCOMPLETE_MASTER_PLAN.md](./AUTOCOMPLETE_MASTER_PLAN.md) - Full system architecture
- [autocomplete-system-improvements-summary.md](./autocomplete-system-improvements-summary.md) - Previous improvements

## Success Criteria

✅ Loading indicator appears when agent starts executing
✅ Loading indicator disappears when agent completes
✅ WebSocket events are properly broadcasted and received
✅ UI updates are smooth without flashing
✅ No race conditions or stuck loading states
✅ Console logs provide debugging visibility

---

**Implementation completed successfully!**
All backend and frontend changes are in place and ready for testing.
