# TN Scheme Compass Frontend Design Spec

## Problem Statement
The current frontend does not match a professional AI-chat product experience. The user requested a polished dark theme, a premium chat-first layout, and a Spline scene at the top of chat to create a classy visual identity.

## Goals
- Deliver a professional dark AI-chat UI.
- Add Spline hero using `@splinetool/react-spline/next`.
- Auto-collapse hero after the first successful user message.
- Render scheme results inline in chat for a focused single-column experience.
- Preserve current backend API contracts and chat behavior.

## Non-Goals
- No backend API contract changes.
- No new feature expansion beyond UI/UX redesign and inline scheme result rendering.
- No auth/session architecture changes.

## Approved Direction
Approach: **Cinematic Chat** (approved by user)

- Spline hero at top on initial load.
- Auto-collapse to compact header once conversation starts.
- Single focused chat panel.
- Dark glassmorphism visual language.
- Scheme results displayed inline as assistant content.

## UX and Visual Design

### Layout
- `App` becomes a chat shell with:
  - Top hero region (Spline scene).
  - Primary chat timeline.
  - Composer at bottom.
- No persistent side panel for scheme cards.

### Theme
- Global dark background with depth gradients.
- High-contrast readable text.
- Subtle glows, soft borders, and elevated surfaces.
- Distinct user vs assistant bubble styles.

### Motion
- Hero collapse animation triggers after first successful message exchange.
- Smooth scroll to latest message continues.
- Respect lightweight transitions (no heavy animation loops beyond Spline).

## Component Design

### `App.jsx`
- Owns:
  - Session bootstrap
  - Message send lifecycle
  - Loading/error handling
  - Hero collapse state (`isHeroCollapsed`)
- Adds inline scheme rendering model in chat stream.

### `SplineHero.jsx` (new)
- Wraps Spline scene:
  - `scene="https://prod.spline.design/XLBNexSpNR4za0AV/scene.splinecode"`
- Supports expanded and collapsed states via props/classes.
- Degrades gracefully if scene load is delayed.

### `ChatBubble.jsx`
- Professional dark bubble treatment:
  - User: accent gradient and bright text.
  - Assistant: glass/dark panel with readable contrast.

### `SchemeCard.jsx`
- Redesigned dark card style.
- Used inline in message stream after assistant response.

### `index.css`
- Introduce dark tokens and utility classes for shell, panels, and micro-interactions.
- Custom scrollbar and focus-state polish.

## Data Flow and Rendering
1. App boots session via `POST /api/chat/session`.
2. User submits message.
3. User bubble appended immediately.
4. Request to `POST /api/chat/message`.
5. Assistant text bubble appended from `payload.reply`.
6. Optional follow-up appended as assistant bubble.
7. `payload.schemes` appended inline as scheme cards in timeline.
8. After first successful response, hero transitions to collapsed state.

This preserves server payload shape and existing conversational behavior.

## Error Handling
- Session init errors are shown as assistant messages.
- Message request failures append explicit assistant error bubbles with backend detail when available.
- Send remains disabled when no session, empty input, or in-flight request.
- Hero visual failures do not block chat functionality.

## Accessibility and Usability
- Maintain keyboard-friendly composer and submit behavior.
- Ensure contrast meets practical dark-theme readability.
- Preserve clear focus styles for textarea/button/links.
- Keep card links explicit and safely opened with `target="_blank" rel="noreferrer"`.

## Dependency and Build Impact
- Add dependency: `@splinetool/react-spline`.
- No framework migration required; continue Vite + React.
- Verify successful build via existing script: `npm run build`.

## Validation Plan
- Baseline build before edits.
- Post-change build after edits.
- Manual checks:
  - Spline hero renders.
  - Hero auto-collapses after first successful message.
  - Dark theme is globally applied.
  - Inline scheme cards render correctly.
  - Error messaging remains visible and clear.

## Risks and Mitigations
- **Spline package compatibility risk:** use package compatible with React 18 and Vite setup.
- **Performance risk on low-end devices:** keep hero area compact after first interaction.
- **Readability risk in dark UI:** enforce conservative contrast and spacing.

## Scope Check
This design is scoped to a single frontend implementation cycle and does not require decomposition into multiple specs.

