# Sidebar Layout Redesign

## Goal

Replace the current top navigation with a Kimi-inspired left application sidebar. The default homepage becomes the Workflow chat. The sidebar shows Skills and Agents navigation by default, can collapse to icon-only mode, and includes a bottom history area for recent Workflow chat sessions.

## Current Context

The Vue 3 frontend currently uses `src/App.vue` to render a top `Navbar.vue` and a padded main content area. Routing currently redirects `/` to `/skills`. Workflow rendering currently uses `WorkflowView.vue`, which delegates to `ChatLayout.vue`; `ChatLayout.vue` contains both `ChatSidebar.vue` for chat session management and the main chat area.

This redesign moves application navigation and Workflow history into one left sidebar and removes the separate Workflow session sidebar from the main Workflow layout.

## Routes

- `/` redirects to `/workflow`.
- `/workflow` remains the Workflow chat view and is the default landing experience.
- `/skills` remains the Skills market page.
- `/agents` remains the Agents market page.

The application sidebar displays only Skills and Agents as primary navigation items. It does not display a Workflows/Workflow menu item. Users return to Workflow by visiting `/`, `/workflow`, creating a new chat from the history area, or selecting a history item.

## Layout

The root layout changes from a vertical top-nav shell to a horizontal app shell:

```text
┌──────────────────┬──────────────────────────────────────┐
│ AppSidebar        │ Main Content                         │
│                  │                                      │
│ Harness / Logo    │ /workflow: chat                      │
│ Skills            │ /skills: Skills market               │
│ Agents            │ /agents: Agents market               │
│                  │                                      │
│                  │                                      │
│ History           │                                      │
│ - Recent chat     │                                      │
│ - Recent chat     │                                      │
│                  │                                      │
│ Theme / Collapse  │                                      │
└──────────────────┴──────────────────────────────────────┘
```

Expanded sidebar:

- Shows product/brand text.
- Shows Skills and Agents labels with icons.
- Shows a bottom history section with a heading and recent chat session titles.
- Shows theme toggle and collapse control.

Collapsed sidebar:

- Uses a narrower icon-only width.
- Shows brand icon/initial, Skills icon, Agents icon, history icon, theme/collapse controls.
- Hides history titles and text labels.

The collapsed state is local component state. It is not persisted in local storage in this scope.

## Components

### `src/components/layout/AppSidebar.vue`

New application-level sidebar component. It replaces `Navbar.vue` in active use.

Responsibilities:

1. Render brand area.
2. Render Skills and Agents navigation.
3. Highlight active route for Skills and Agents.
4. Render bottom Workflow history area.
5. Provide new-session action in the history heading while expanded.
6. Allow selecting recent sessions.
7. Allow deleting sessions from the history list via hover action while expanded.
8. Render theme toggle.
9. Render collapse/expand control.

### `src/App.vue`

Changes to render the app shell:

```vue
<div class="app-shell">
  <AppSidebar />
  <main class="app-main">
    <router-view />
  </main>
</div>
```

The old top navigation is removed from the root shell. `Navbar.vue` is no longer referenced by `App.vue`; implementation may delete it only if no other file imports it.

### `src/components/workflow/ChatLayout.vue`

Changes from a two-column internal layout to a main chat-only layout. It no longer renders `ChatSidebar.vue` as a separate Workflow side panel.

The main chat layout contains:

- A lightweight Workflow top bar.
- `ChatStream`.
- `ChatInput`.

### Workflow top bar

A lightweight top bar inside the Workflow main area shows:

- Current session title, or `新对话` when no session is selected.
- Model selector.
The top bar does not add a new engine/status widget in this scope. The model selector moves out of the old chat sidebar and into this top bar.

## State and Data Flow

Session list management moves into `src/stores/chat.ts` so both `AppSidebar.vue` and `WorkflowView.vue` can use the same source of truth.

The store owns:

- `sessions`
- `currentSessionId`
- `messages`
- `model`
- `agentSessionId`
- `isStreaming`
- `pendingPermission`
- `loadSessions()`
- `createSession()`
- `deleteSession(id)`
- `selectSession(id)`
- `clearSession()`
- model and agent session updates

`AppSidebar.vue` uses the store to:

- Display recent sessions in the bottom history area.
- Create a new session and route to `/workflow`.
- Select a session and route to `/workflow`.
- Delete a session.

`WorkflowView.vue` uses the store to:

- Display the current session messages.
- Send chat messages through `useChatStream`.
- Update current agent session id after the backend returns it.
- Refresh sessions after a completed message so history metadata stays current.

`useChatStream` remains focused on chat streaming. It should not become responsible for global navigation or history rendering.

## Key Interactions

### First visit

Opening `/` redirects to `/workflow`. The Workflow page shows an empty chat state when no session is selected.

### First message without a selected session

If the user sends a message without a selected session, the frontend creates a session first, selects it, and then sends the message. This matches the default-chat feel of Kimi-like products and avoids forcing the user to click `+` first.

### Select history session

```text
Click history item
→ chatStore.selectSession(id)
→ router.push('/workflow')
→ WorkflowView displays that session's messages
```

### Create new session

```text
Click + in history heading
→ chatStore.createSession()
→ router.push('/workflow')
→ WorkflowView shows empty conversation state
```

### Delete session

```text
Click delete action on history item
→ DELETE /api/chat/sessions
→ remove from chatStore.sessions
→ if deleted session is current, clear current session and messages
```

### Send message

```text
WorkflowView sends through useChatStream
→ backend streams response
→ on done, update agentSessionId
→ refresh session list
```

## Visual Direction

Use a restrained Kimi-inspired light style:

- Near-white sidebar.
- Light gray page background.
- Thin borders.
- Rounded hover states.
- Soft active state instead of saturated brand colors.
- Single-line history titles with ellipsis.
- Delete action appears only on hover while expanded.
- No heavy gradients or strong brand panels.

The content area should feel more immersive after removing the top navigation height.

## Responsive Behavior

Desktop-first behavior:

- At widths `>= 900px`, the sidebar is fixed on the left and supports expanded/collapsed states.
- At widths `< 900px`, the sidebar defaults to or behaves like icon-only mode to preserve chat width.
- At very narrow widths, history titles remain hidden; only the history icon/entry remains visible.

This scope does not include a full mobile drawer implementation.

## Out of Scope

This redesign does not include:

- Sidebar collapse state persistence.
- History search.
- Session rename.
- Full mobile drawer behavior.
- A Workflow primary nav item.
- Major theme-system refactoring.
- Backend API changes.
- Chat streaming protocol changes.

## Testing and Verification

Implementation should verify:

1. `/` redirects to `/workflow`.
2. The old top navigation is not visible.
3. The left sidebar displays Skills and Agents only as primary nav items.
4. Skills and Agents navigation works.
5. Sidebar collapse changes to icon-only mode.
6. History sessions appear at the bottom while expanded.
7. Clicking a history session routes to Workflow and displays its messages.
8. Creating a new session from the sidebar routes to Workflow and shows an empty conversation.
9. Deleting the current session clears the chat state.
10. Sending the first message with no selected session creates a session first.
11. Model selection remains available in Workflow.
12. TypeScript/build checks pass.

## Implementation Notes

Keep the implementation incremental:

1. Introduce `AppSidebar.vue` and root app shell.
2. Change route default to `/workflow`.
3. Move session CRUD into the chat store.
4. Wire AppSidebar history to the store.
5. Simplify `ChatLayout.vue` and move model selector into Workflow top bar.
6. Polish visual states and responsive behavior.
7. Run build and manual verification.
