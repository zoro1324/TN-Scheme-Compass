# Dark Cinematic Chat UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the current frontend into a professional dark AI chat experience with a Spline hero that auto-collapses after the first successful chat response, while preserving existing API behavior.

**Architecture:** Keep the existing Vite + React app and backend API contract, but refactor UI composition around a single chat timeline. Add a dedicated `SplineHero` component and move scheme rendering inline in the chat stream. Apply global dark-theme styles and update message/card components for a premium AI-chat look.

**Tech Stack:** React 18, Vite 5, Tailwind CSS, Axios, `@splinetool/react-spline`

---

## File Structure and Responsibilities

- Modify: `frontend/package.json`  
  Add `@splinetool/react-spline` dependency.

- Create: `frontend/src/components/SplineHero.jsx`  
  Encapsulate Spline scene rendering and expanded/collapsed hero states.

- Modify: `frontend/src/App.jsx`  
  Replace side-panel layout with single-column chat shell, add hero-collapse state, and render scheme cards inline in timeline.

- Modify: `frontend/src/components/ChatBubble.jsx`  
  Apply dark premium bubble styles and content wrapper compatibility.

- Modify: `frontend/src/components/SchemeCard.jsx`  
  Redesign card visuals for dark inline chat usage.

- Modify: `frontend/src/index.css`  
  Set global dark theme tokens, shell classes, motion, focus, and scrollbar polish.

---

### Task 1: Baseline verification and dependency installation

**Files:**
- Modify: `frontend/package.json`
- Verify: `frontend/package-lock.json` (auto-updated by npm)

- [ ] **Step 1: Run baseline build before changes**

Run:
```bash
cd frontend
npm run build
```

Expected: `vite build` completes successfully with no errors.

- [ ] **Step 2: Add Spline dependency**

Run:
```bash
cd frontend
npm install @splinetool/react-spline --save
```

Expected: package is added under `dependencies` and lockfile updates.

- [ ] **Step 3: Confirm dependency entry**

Expected `frontend/package.json` dependency block includes:
```json
"dependencies": {
  "@splinetool/react-spline": "^4.0.0",
  "axios": "^1.8.4",
  "react": "^18.3.1",
  "react-dom": "^18.3.1"
}
```

- [ ] **Step 4: Commit**

Run:
```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): add spline dependency for hero scene"
```

---

### Task 2: Create reusable Spline hero component

**Files:**
- Create: `frontend/src/components/SplineHero.jsx`
- Test (manual): `frontend/src/App.jsx` (integration in next task)

- [ ] **Step 1: Create `SplineHero.jsx` component**

Add:
```jsx
import Spline from "@splinetool/react-spline";

export default function SplineHero({ collapsed }) {
  return (
    <section
      className={`hero-shell ${collapsed ? "hero-shell--collapsed" : "hero-shell--expanded"}`}
      aria-label="Decorative 3D hero"
    >
      <div className="hero-overlay">
        <p className="hero-kicker">TN Scheme Compass</p>
        <h1 className="hero-title">Professional AI Scheme Assistant</h1>
      </div>

      <div className="hero-scene" aria-hidden="true">
        <Spline scene="https://prod.spline.design/XLBNexSpNR4za0AV/scene.splinecode" />
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Add defensive UX note in code style (non-blocking scene)**

Ensure no app logic depends on Spline loading; component remains purely presentational.

- [ ] **Step 3: Commit**

Run:
```bash
git add frontend/src/components/SplineHero.jsx
git commit -m "feat(frontend): add reusable spline hero component"
```

---

### Task 3: Refactor app layout and message flow for inline results

**Files:**
- Modify: `frontend/src/App.jsx`
- Reuse: `frontend/src/components/ChatBubble.jsx`
- Reuse: `frontend/src/components/SchemeCard.jsx`
- Reuse: `frontend/src/components/SplineHero.jsx`

- [ ] **Step 1: Introduce timeline message model with scheme attachments**

Replace `messages` state with an object-capable array:
```jsx
const [messages, setMessages] = useState([
  {
    id: "welcome",
    role: "assistant",
    text: "Tell me your situation, and I will find Tamil Nadu schemes with full eligibility, benefits, documents, and application details.",
    schemes: [],
  },
]);
```

- [ ] **Step 2: Add hero collapse state**

Add:
```jsx
const [isHeroCollapsed, setIsHeroCollapsed] = useState(false);
```

Collapse only after successful API response:
```jsx
setIsHeroCollapsed(true);
```

- [ ] **Step 3: Update send flow to attach schemes inline**

In success branch:
```jsx
setMessages((prev) => {
  const next = [
    ...prev,
    {
      id: crypto.randomUUID(),
      role: "assistant",
      text: payload.reply,
      schemes: payload.schemes || [],
    },
  ];

  if (payload.follow_up_question) {
    next.push({
      id: crypto.randomUUID(),
      role: "assistant",
      text: `Next question: ${payload.follow_up_question}`,
      schemes: [],
    });
  }

  return next;
});
```

- [ ] **Step 4: Remove right-side `aside` panel and render a single chat column**

Main structure target:
```jsx
<div className="app-shell">
  <SplineHero collapsed={isHeroCollapsed} />

  <main className="chat-shell">
    <div className="chat-scroll">
      {messages.map((msg) => (
        <ChatBubble key={msg.id} role={msg.role} text={msg.text}>
          {msg.schemes?.length ? (
            <div className="inline-scheme-stack">
              {msg.schemes.map((scheme) => (
                <SchemeCard key={scheme.scheme_id} scheme={scheme} />
              ))}
            </div>
          ) : null}
        </ChatBubble>
      ))}
      <div ref={listEndRef} />
    </div>
    {/* composer stays at bottom */}
  </main>
</div>
```

- [ ] **Step 5: Keep existing error behavior explicit**

Ensure catch blocks append assistant error text, e.g.:
```jsx
setMessages((prev) => [
  ...prev,
  { id: crypto.randomUUID(), role: "assistant", text: `Error: ${detail}`, schemes: [] },
]);
```

- [ ] **Step 6: Commit**

Run:
```bash
git add frontend/src/App.jsx
git commit -m "refactor(frontend): convert to single-column cinematic chat flow"
```

---

### Task 4: Dark theme styling and component polish

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/components/ChatBubble.jsx`
- Modify: `frontend/src/components/SchemeCard.jsx`

- [ ] **Step 1: Update `ChatBubble.jsx` to accept children and dark variants**

Use:
```jsx
export default function ChatBubble({ role, text, children }) {
  const isUser = role === "user";

  return (
    <div className={`bubble-row ${isUser ? "bubble-row--user" : "bubble-row--assistant"}`}>
      <article className={`bubble ${isUser ? "bubble--user" : "bubble--assistant"}`}>
        <p className="bubble-text">{text}</p>
        {children}
      </article>
    </div>
  );
}
```

- [ ] **Step 2: Redesign `SchemeCard.jsx` for dark inline cards**

Target structure:
```jsx
<article className="scheme-card">
  <div className="scheme-card__header">
    <h4>{scheme.scheme_name}</h4>
    <span>{scheme.scheme_level || "N/A"}</span>
  </div>
  <p className="scheme-card__reason">{scheme.match_reason}</p>
  <ul className="scheme-card__meta">
    <li><strong>Benefit:</strong> {scheme.benefit_description || "N/A"}</li>
    <li><strong>Amount:</strong> {scheme.benefit_amount || "N/A"}</li>
    <li><strong>Eligibility:</strong> {scheme.eligibility_criteria || "N/A"}</li>
    <li><strong>Documents:</strong> {scheme.required_documents || "N/A"}</li>
    <li><strong>Apply:</strong> {scheme.application_process || "N/A"}</li>
  </ul>
</article>
```

- [ ] **Step 3: Replace `index.css` root styles with dark cinematic theme**

Include concrete classes:
```css
:root {
  color: #e6ebff;
  background: radial-gradient(circle at 10% 10%, #1a2340 0%, #0a0d18 45%, #05070f 100%);
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "IBM Plex Sans", sans-serif;
  background: #05070f;
}

.hero-shell { transition: height 300ms ease, opacity 300ms ease; }
.hero-shell--expanded { height: 320px; }
.hero-shell--collapsed { height: 96px; }

.chat-shell { max-width: 980px; margin: 0 auto; }
.bubble--assistant { background: rgba(16, 22, 40, 0.78); border: 1px solid rgba(145, 163, 255, 0.25); }
.bubble--user { background: linear-gradient(135deg, #4f6bff, #7a5cff); color: #fff; }

.scheme-card { background: rgba(13, 18, 33, 0.9); border: 1px solid rgba(139, 156, 255, 0.25); }
```

- [ ] **Step 4: Ensure composer and focus states remain keyboard-visible**

Add explicit `:focus-visible` ring styles for textarea/button/links in `index.css`.

- [ ] **Step 5: Commit**

Run:
```bash
git add frontend/src/components/ChatBubble.jsx frontend/src/components/SchemeCard.jsx frontend/src/index.css
git commit -m "feat(frontend): apply professional dark chat theme and inline cards"
```

---

### Task 5: Verification and final integration check

**Files:**
- Verify: `frontend/src/App.jsx`
- Verify: `frontend/src/components/SplineHero.jsx`
- Verify: `frontend/src/components/ChatBubble.jsx`
- Verify: `frontend/src/components/SchemeCard.jsx`
- Verify: `frontend/src/index.css`

- [ ] **Step 1: Run production build after all edits**

Run:
```bash
cd frontend
npm run build
```

Expected: successful build output and generated `dist` bundle.

- [ ] **Step 2: Run local app for manual UX validation**

Run:
```bash
cd frontend
npm run dev
```

Manual checklist:
- Hero initially expanded with Spline visible.
- First successful assistant response collapses hero.
- Dark theme applied across app surfaces.
- Scheme cards render inline beneath assistant response.
- Session init and send errors show explicit assistant messages.
- Composer remains usable with keyboard and visible focus.

- [ ] **Step 3: Final commit**

Run:
```bash
git add frontend/src/App.jsx frontend/src/components/SplineHero.jsx frontend/src/components/ChatBubble.jsx frontend/src/components/SchemeCard.jsx frontend/src/index.css
git commit -m "feat(frontend): deliver cinematic dark AI chat redesign"
```

---

## Self-Review

### 1) Spec Coverage Check
- Professional dark AI chat UI: covered by Tasks 3 and 4.
- Spline integration via `@splinetool/react-spline`: covered by Tasks 1 and 2.
- Auto-collapse hero after first successful message: covered by Task 3.
- Inline scheme cards in chat stream: covered by Tasks 3 and 4.
- Preserve API contracts and error clarity: covered by Task 3.
- Build verification and manual checks: covered by Task 5.

No spec gaps identified.

### 2) Placeholder Scan
- No `TBD`, `TODO`, or unresolved placeholder text in execution steps.
- Every task contains explicit files, commands, and expected outcomes.

### 3) Type/Signature Consistency Check
- `SplineHero` prop is consistently named `collapsed`.
- Message object consistently uses `id`, `role`, `text`, and `schemes`.
- `ChatBubble` consistently accepts `children` for inline scheme rendering.

No naming/signature inconsistencies identified.

