# Plan: Vue 3 Markdown Preview App

## Task Description
Create a standalone markdown preview application in `apps/markdown_preview/` using Vue 3 and TypeScript. The application features a split-pane interface with a markdown editor on the left and a live preview on the right. It includes syntax highlighting for markdown content and a copy-to-clipboard button for the rendered HTML output.

## Objective
Deliver a fully functional, responsive markdown preview app that allows users to write markdown content and see the rendered HTML in real-time, with the ability to copy the rendered HTML to their clipboard.

## Problem Statement
Developers and content creators need a quick, local tool to preview markdown content as they write it. Current solutions often require online services or complex IDE plugins. This app provides a lightweight, self-contained solution with live preview and HTML export capabilities.

## Solution Approach
Build a Vue 3 application following the existing project patterns in the codebase:
- Use the same project structure as `apps/orchestrator_3_stream/frontend/`
- Leverage existing dependencies where appropriate (marked, highlight.js, dompurify)
- Implement a resizable split-pane layout using CSS grid and @vueuse/core utilities
- Create modular Vue components with TypeScript for type safety

## Relevant Files
Use these files as reference for patterns and structure:

- `apps/orchestrator_3_stream/frontend/package.json` - Reference for dependencies and scripts
- `apps/orchestrator_3_stream/frontend/vite.config.ts` - Reference for Vite configuration
- `apps/orchestrator_3_stream/frontend/tsconfig.json` - Reference for TypeScript configuration
- `apps/orchestrator_3_stream/frontend/src/main.ts` - Reference for app initialization
- `apps/orchestrator_3_stream/frontend/index.html` - Reference for HTML template

### New Files
Files to be created in `apps/markdown_preview/`:

```
apps/markdown_preview/
├── index.html                  # HTML entry point
├── package.json                # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
├── tsconfig.node.json          # Node TypeScript config
├── vite.config.ts              # Vite bundler configuration
└── src/
    ├── main.ts                 # App entry point
    ├── App.vue                 # Root component
    ├── vite-env.d.ts           # Vite type definitions
    ├── components/
    │   ├── MarkdownEditor.vue  # Textarea with syntax highlighting
    │   ├── MarkdownPreview.vue # Rendered HTML preview
    │   ├── SplitPane.vue       # Resizable split container
    │   └── CopyButton.vue      # Copy to clipboard button
    ├── composables/
    │   └── useMarkdown.ts      # Markdown parsing logic
    └── styles/
        └── global.css          # Global styles and theme
```

## Implementation Phases

### Phase 1: Foundation
Set up the project structure, configuration files, and install dependencies. Ensure the basic Vue 3 + TypeScript + Vite stack is working.

### Phase 2: Core Implementation
Build the core components:
1. SplitPane container with resizable divider
2. MarkdownEditor with syntax highlighting
3. MarkdownPreview with live rendering
4. CopyButton with clipboard API integration

### Phase 3: Integration & Polish
Connect all components, add responsive design, implement keyboard shortcuts, and ensure smooth user experience.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Project Directory Structure
- Create `apps/markdown_preview/` directory
- Create `src/`, `src/components/`, `src/composables/`, `src/styles/` subdirectories

### 2. Create Configuration Files
- Create `package.json` with Vue 3, TypeScript, Vite, marked, highlight.js, dompurify, and @vueuse/core dependencies
- Create `tsconfig.json` and `tsconfig.node.json` following the orchestrator frontend pattern
- Create `vite.config.ts` with Vue plugin and path aliases

### 3. Create HTML Entry Point
- Create `index.html` with modern HTML5 structure
- Include app mount point and module script reference
- Add base styles for dark theme

### 4. Create App Entry Point
- Create `src/main.ts` to initialize Vue app
- Import global styles and highlight.js theme
- Create `src/vite-env.d.ts` for Vite type references

### 5. Create useMarkdown Composable
- Create `src/composables/useMarkdown.ts`
- Implement markdown parsing with marked library
- Configure syntax highlighting with highlight.js
- Sanitize output with DOMPurify
- Export reactive markdown content and rendered HTML

### 6. Create SplitPane Component
- Create `src/components/SplitPane.vue`
- Implement resizable split layout using CSS grid
- Use @vueuse/core for mouse drag handling
- Support horizontal split with configurable initial ratio
- Store split ratio in localStorage for persistence

### 7. Create MarkdownEditor Component
- Create `src/components/MarkdownEditor.vue`
- Implement textarea with monospace font
- Add line numbers display (optional enhancement)
- Emit input events for live preview
- Support Tab key for indentation

### 8. Create MarkdownPreview Component
- Create `src/components/MarkdownPreview.vue`
- Render sanitized HTML from markdown
- Apply prose styling for readability
- Handle code block syntax highlighting
- Support scrolling synchronized with editor (optional)

### 9. Create CopyButton Component
- Create `src/components/CopyButton.vue`
- Use Clipboard API to copy rendered HTML
- Show visual feedback on successful copy
- Handle copy failures gracefully

### 10. Create App Component
- Create `src/App.vue`
- Compose all components together
- Implement split pane with editor and preview
- Add header with app title and copy button
- Apply responsive layout

### 11. Create Global Styles
- Create `src/styles/global.css`
- Define CSS variables for theming
- Style markdown preview (headings, code, lists, etc.)
- Add responsive breakpoints

### 12. Install Dependencies and Test
- Run `npm install` in the markdown_preview directory
- Run `npm run dev` to start development server
- Verify markdown editing and preview work
- Test copy-to-clipboard functionality
- Verify split pane resizing works

## Testing Strategy
- Manual testing of markdown rendering for various syntax (headings, lists, code blocks, links, images, tables)
- Verify syntax highlighting works for common languages (JavaScript, Python, TypeScript, etc.)
- Test copy-to-clipboard on different browsers
- Test responsive layout at various screen sizes
- Verify split pane resize persists across page reloads

## Acceptance Criteria
- [ ] App runs successfully with `npm run dev`
- [ ] Split pane displays editor on left, preview on right
- [ ] Markdown text in editor renders live in preview
- [ ] Code blocks have syntax highlighting
- [ ] Copy button copies rendered HTML to clipboard
- [ ] Split pane is resizable via drag
- [ ] App is responsive on mobile devices
- [ ] No TypeScript errors on build

## Validation Commands
Execute these commands to validate the task is complete:

- `cd apps/markdown_preview && npm install` - Install dependencies
- `cd apps/markdown_preview && npm run dev` - Start dev server and manually test
- `cd apps/markdown_preview && npm run build` - Verify production build succeeds
- `cd apps/markdown_preview && npx vue-tsc --noEmit` - Verify no TypeScript errors

## Notes
- Use `npm install` (not uv) for Node.js project dependencies
- The app follows the same patterns as `apps/orchestrator_3_stream/frontend/`
- Dependencies to install:
  ```json
  {
    "dependencies": {
      "@vueuse/core": "^14.0.0",
      "dompurify": "^3.3.0",
      "highlight.js": "^11.11.1",
      "marked": "^16.4.1",
      "vue": "^3.4.0"
    },
    "devDependencies": {
      "@types/dompurify": "^3.0.5",
      "@types/marked": "^5.0.2",
      "@vitejs/plugin-vue": "^5.0.0",
      "typescript": "^5.0.0",
      "vite": "^5.0.0",
      "vue-tsc": "^1.8.0"
    }
  }
  ```
- Default port should be 5180 to avoid conflicts with other apps
- Consider adding keyboard shortcut Cmd/Ctrl+S to copy HTML
