# Plan: Global Command Input Bar

## Task Description
Reposition the chat input bar as a global command input that lives below the event stream and chat panels, spanning the center and right columns. The input bar should be hidden by default and toggleable via keyboard shortcut (cmd+k / ctrl+k) or a "Prompt" button in the AppHeader. It should feature a larger, more prominent input field with improved visibility and auto-focus capabilities, while maintaining all current messaging functionality to the orchestrator.

## Objective
Transform the current chat-specific input into a globally accessible command bar that provides a more prominent and flexible interface for interacting with the orchestrator, improving user experience through keyboard shortcuts and better visual design.

## Problem Statement
The current chat input is confined within the OrchestratorChat component, limiting its visibility and accessibility. Users need a more prominent, globally accessible command interface that can be quickly toggled and provides a better typing experience with a larger input area.

## Solution Approach
Create a new GlobalCommandInput component that sits at the bottom of the main content area (spanning center and right columns), managed by global state in the orchestratorStore. Implement keyboard shortcuts for quick access, add a toggle button to the AppHeader, and ensure smooth animations for show/hide transitions. The component will feature a larger textarea with improved styling for better visibility and usability.

## Relevant Files
Use these files to complete the task:

- `src/App.vue` - Main app layout that needs grid restructuring to accommodate the new input bar
- `src/components/OrchestratorChat.vue` - Remove the existing chat input container from this component
- `src/components/AppHeader.vue` - Add the "Prompt" toggle button here (left of "Clear All")
- `src/stores/orchestratorStore.ts` - Add state management for command input visibility
- `src/styles/global.css` - Reference for theme variables and consistent styling

### New Files
- `src/components/GlobalCommandInput.vue` - New component for the global command input bar
- `src/composables/useKeyboardShortcuts.ts` - Composable for managing keyboard shortcuts

## Implementation Phases

### Phase 1: Foundation
- Set up state management in orchestratorStore
- Create the useKeyboardShortcuts composable
- Update App.vue grid layout structure

### Phase 2: Core Implementation
- Build the GlobalCommandInput component with all features
- Remove chat input from OrchestratorChat
- Add "Prompt" button to AppHeader
- Implement keyboard shortcut handling

### Phase 3: Integration & Polish
- Connect all components with proper event handling
- Add smooth animations for show/hide
- Ensure proper focus management
- Test across different screen sizes

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update orchestratorStore with Command Input State
- Add `commandInputVisible` ref with default value `false`
- Create `toggleCommandInput()` action to toggle visibility
- Create `showCommandInput()` action to explicitly show and focus
- Create `hideCommandInput()` action to explicitly hide
- Export new state and actions in the return statement

### 2. Create useKeyboardShortcuts Composable
- Create new file `src/composables/useKeyboardShortcuts.ts`
- Implement keyboard event listener for cmd+k (Mac) and ctrl+k (Windows/Linux)
- Use `onMounted` and `onUnmounted` to manage event listeners lifecycle
- Import orchestratorStore and call `toggleCommandInput()` on shortcut
- Prevent default browser behavior for the shortcut

### 3. Create GlobalCommandInput Component
- Create new file `src/components/GlobalCommandInput.vue`
- Structure with a container div that spans the full width
- Add a larger textarea (3-4 rows minimum) with v-model binding to local state
- Implement Enter to submit (with Shift+Enter for newline)
- Add Send button similar to current chat but with better styling
- Include auto-focus directive when component becomes visible
- Emit 'send' event with message content
- Add smooth slide-up/slide-down animation with v-show directive
- Style with prominent appearance: larger font size (1rem), better padding, clear borders

### 4. Update App.vue Grid Layout
- Modify the grid template to add a new row for the command input
- Change main layout from 3-column to include command input area
- Add GlobalCommandInput component below the main grid
- Position it to span from the second column to the end (skipping agent sidebar)
- Use CSS Grid `grid-column: 2 / -1` to achieve proper spanning
- Bind visibility to store state
- Handle send event by calling `store.sendUserMessage`
- Import and use the useKeyboardShortcuts composable

### 5. Remove Input from OrchestratorChat
- Remove the entire `chat-input-container` div and its contents
- Remove the `inputMessage` ref from script section
- Remove the `sendMessage` function (functionality moves to GlobalCommandInput)
- Adjust the chat-messages container to use full available height
- Update any CSS that referenced the removed input container

### 6. Add Prompt Button to AppHeader
- Add new button in header-actions div, positioned before "CLEAR ALL"
- Label the button "PROMPT" with consistent styling
- Add click handler to call `store.toggleCommandInput()`
- Add 'active' class when `store.commandInputVisible` is true
- Style to match existing header buttons but with accent color when active

### 7. Style and Animation Polish
- Add transition classes for smooth show/hide animation (slide and fade)
- Set z-index appropriately to ensure input appears above other content
- Add backdrop shadow when input is visible for better visual separation
- Ensure responsive behavior on smaller screens
- Add hover states and focus styles for better UX
- Use CSS custom properties from global.css for consistency

### 8. Focus Management and Accessibility
- Auto-focus the textarea when command input becomes visible
- Trap focus within the command input when it's open
- Add escape key handler to close the input
- Ensure proper ARIA labels for accessibility
- Maintain focus return to previous element when closed

### 9. Validate Implementation
- Test keyboard shortcut on both Mac and Windows/Linux
- Verify Enter submits and Shift+Enter adds newline
- Ensure messages are sent to orchestrator correctly
- Test toggle button functionality in AppHeader
- Verify animations are smooth and performant
- Check responsive behavior at different screen sizes
- Ensure no layout shifts when toggling input visibility

## Testing Strategy
- **Unit Testing**: Test store actions for command input visibility management
- **Component Testing**: Verify GlobalCommandInput emits correct events and handles props
- **Integration Testing**: Ensure keyboard shortcuts work across the application
- **E2E Testing**: Validate full flow from opening input to sending message
- **Cross-browser Testing**: Verify keyboard shortcuts work in Chrome, Firefox, Safari
- **Responsive Testing**: Check layout at mobile, tablet, and desktop breakpoints
- **Accessibility Testing**: Verify keyboard navigation and screen reader compatibility

## Acceptance Criteria
- [ ] Command input bar is hidden by default on page load
- [ ] Pressing cmd+k (Mac) or ctrl+k (Windows/Linux) toggles the input visibility
- [ ] Clicking "Prompt" button in header toggles the input visibility
- [ ] Input bar spans center and right columns, not extending under agent sidebar
- [ ] Textarea is at least 3 rows tall with larger, more readable text
- [ ] Enter key sends message, Shift+Enter adds newline
- [ ] Input auto-focuses when shown via any method
- [ ] Smooth animation when showing/hiding the input
- [ ] Messages sent from new input reach the orchestrator correctly
- [ ] Original chat display remains functional, just without input
- [ ] Escape key closes the input when it's open
- [ ] No console errors or warnings during operation

## Validation Commands
Execute these commands to validate the task is complete:

- `npm run dev` - Start the development server and verify the UI works correctly
- `npm run type-check` - Ensure TypeScript types are correct
- `npm run lint` - Verify code follows linting standards
- Manual testing checklist:
  - Open browser console and verify no errors
  - Press cmd+k or ctrl+k and verify input toggles
  - Click "Prompt" button and verify input toggles
  - Type a message and press Enter to send
  - Type a message with Shift+Enter for multiline
  - Press Escape to close the input

## Notes
- The command input should maintain the same WebSocket connection and message handling as the current chat input
- Consider adding a visual indicator (like a subtle pulse or glow) when the input is focused
- Future enhancement could include command history navigation with up/down arrows
- The animation duration should be around 200-300ms for optimal feel
- Ensure the input bar doesn't interfere with the agent sidebar's scroll behavior
- Consider adding a keyboard shortcut hint in the UI for discoverability