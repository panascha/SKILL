---
name: vanilla-hybrid-fullstack-dev
description: Behavioral and architectural guidelines for AI agents (Claude Code, Cursor, etc.) working on Vanilla HTML5 + Tailwind CSS + Firebase Auth/RTDB + Google Apps Script projects. Trigger this on every task — writing, refactoring, debugging, or feature additions.
license: MIT
allowed-tools:
  - glob
  - grep
  - write_file
  - view_file
---

# VIBE.md — AI Agent Coding Instructions

> **MANDATORY:** Read this entire file before touching a single line of code.
> These are non-negotiable behavioral and architectural constraints for this repository.

---

## 🧠 Part 1: Core Behavior — Karpathy Guidelines

Derived from Andrej Karpathy's observations on common LLM coding pitfalls.
**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

---

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing any code:

- State your assumptions explicitly. If uncertain, **ask — do not guess**.
- If a prompt has multiple valid interpretations, **present them all** before picking one.
- If a simpler Vanilla JS/HTML approach can solve the problem, **say so and push back**.
- If something is unclear about the Firebase schema or GAS payload structure, **stop and ask**. Wrong field names silently corrupt data in a Schemaless system.

```
✅ "I'm assuming `user_id` maps to Firebase Auth UID. Is that correct?"
❌ Silently using `uid`, `userId`, and `user_id` interchangeably.
```

---

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- No React-like state management, event buses, or custom lifecycle systems. This is **Vanilla JS**.

If you write 200 lines and it could be 50, rewrite it.

Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

---

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Do **not** "improve" adjacent code, comments, or formatting.
- Do **not** refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, **mention it — don't delete it**.

When your changes create orphans:
- Remove imports/variables/functions that **your changes** made unused.
- Do **not** remove pre-existing dead code unless explicitly asked.

**The test:** Every changed line must trace directly to the user's request.

---

### 4. Goal-Driven Execution

**Define success criteria. Execute in steps. Verify each one.**

Transform every task into a verifiable goal before coding:

```
"Add form validation"  →  "Console.log the error object when email is empty, then show it in #error-msg"
"Fix the GAS bug"      →  "POST returns 200 and the new row appears in Sheet within 5 seconds"
"Refactor service"     →  "Existing callers in pages/ still work after rename"
```

For every multi-step task, output a brief plan before execution:

```
[PLAN]
1. Modify gas.service.js → add timeout to fetch() → verify: catch block logs "GAS_TIMEOUT"
2. Modify home.js → call new service → verify: UI shows error toast on failure
3. Clean up: remove old fetchData() that my changes made unused
```

Weak criteria ("make it work") require constant clarification. Strong criteria let you loop independently.

---

## 🏗️ Part 2: Architecture Guardrails

### Layer Rules — Separation of Concerns (Non-Negotiable)

| File / Folder | ✅ Allowed | ❌ Forbidden |
|---|---|---|
| `src/pages/**/*.html` | Structural markup, `<script type="module" src="...">` | Inline `<script>` logic, inline styles |
| `src/pages/**/*.js` | Import services → bind events → manipulate DOM | Direct `fetch()`, Firebase SDK calls, writing `import.meta.env` |
| `src/services/firebase.js` | Firebase `initializeApp()`, export `app`, `auth`, `db` | Any DOM, any business logic |
| `src/services/auth.service.js` | `signIn()`, `signOut()`, `onAuthStateChanged()` | DOM manipulation |
| `src/services/db.service.js` | Firebase RTDB `get()`, `set()`, `onValue()`, `off()` | DOM manipulation |
| `src/services/gas.service.js` | `fetch()` to `VITE_GAS_WEBAPP_URL`, return parsed JSON | DOM manipulation |
| `src/components/*.js` | Create/update own DOM subtree, emit custom events | Call services directly |
| `src/utils/helpers.js` | Pure stateless functions (format, parse, transform) | Side effects, API calls, DOM |
| `src/main.js` | Global auth guard — check session, redirect if unauth | Page-specific logic |

**The rule in one sentence:** `services/` talks to the backend. `pages/` talks to the DOM. Never cross the line.

---

### Data Layer Decision

Before writing any data operation, identify the mode from the task context:

| Condition | Use | File |
|---|---|---|
| Real-time sync needed (live score, presence, notifications, chat) | Firebase Realtime DB | `db.service.js` |
| Form submission, bulk records, static data, reports | Google Apps Script + Sheets | `gas.service.js` |
| Auth state, session, user identity | Firebase Auth | `auth.service.js` |

**When in doubt, ask.** Choosing the wrong layer creates technical debt that's painful to unwind.

---

## 🔥 Part 3: Stack-Specific Code Patterns

Use these exact patterns. Do not invent alternatives.

### Firebase Auth — Session Guard (Every Page)

Every `src/pages/**/*.js` must start with this pattern before any rendering logic:

```javascript
// pages/home/home.js
import { requireAuth } from '../../services/auth.service.js';

const user = await requireAuth(); // redirects to /index.html if not logged in
// Only code below this line renders the page
renderHomePage(user);
```

```javascript
// services/auth.service.js
import { auth } from './firebase.js';
import { onAuthStateChanged } from 'firebase/auth';

export function requireAuth() {
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      if (!user) {
        window.location.href = '/index.html';
      } else {
        resolve(user);
      }
    });
  });
}
```

---

### Firebase RTDB — Real-time Listener Pattern

Always return a cleanup function. Always call it when navigating away.

```javascript
// services/db.service.js
import { ref, onValue, off, set } from 'firebase/database';
import { db } from './firebase.js';

export function listenTo(path, callback) {
  const dbRef = ref(db, path);
  onValue(dbRef, (snapshot) => callback(snapshot.val()));
  return () => off(dbRef); // caller MUST invoke this to prevent memory leaks
}

export async function writeTo(path, data) {
  await set(ref(db, path), data);
}
```

```javascript
// pages/home/home.js — usage
const cleanup = listenTo('presence/user_123', (data) => renderStatus(data));
window.addEventListener('beforeunload', cleanup); // always clean up
```

---

### Google Apps Script — Fetch Pattern

Always use `try/catch`. Always validate response shape. Never trust GAS to return consistent types.

```javascript
// services/gas.service.js
const GAS_URL = import.meta.env.VITE_GAS_WEBAPP_URL;

export async function gasPost(action, data) {
  try {
    const res = await fetch(GAS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' }, // GAS requires text/plain for doPost
      body: JSON.stringify({ action, data }),
    });
    if (!res.ok) throw new Error(`HTTP_ERROR: ${res.status}`);
    const json = await res.json();
    if (json.status !== 'success') throw new Error(`GAS_ERROR: ${json.message}`);
    return json.data;
  } catch (err) {
    console.error(`[gasPost] action=${action}`, err);
    throw err; // re-throw so caller can handle UI feedback
  }
}

export async function gasGet(action, params = {}) {
  try {
    const query = new URLSearchParams({ action, ...params }).toString();
    const res = await fetch(`${GAS_URL}?${query}`);
    if (!res.ok) throw new Error(`HTTP_ERROR: ${res.status}`);
    const json = await res.json();
    if (json.status !== 'success') throw new Error(`GAS_ERROR: ${json.message}`);
    return json.data;
  } catch (err) {
    console.error(`[gasGet] action=${action}`, err);
    throw err;
  }
}
```

**GAS Payload Contract** — always match `DATABASE.md`:
```json
// POST body
{ "action": "registerUser", "data": { "user_id": "...", "email": "..." } }

// Expected GAS response
{ "status": "success", "data": { ... } }
{ "status": "error",   "message": "Reason for failure" }
```

---

### Tailwind CSS Rules

```html
<!-- ✅ Correct: utility classes, responsive prefix -->
<div class="flex flex-col gap-4 p-4 sm:flex-row sm:p-6">
  <button class="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Submit</button>
</div>

<!-- ❌ Wrong: inline styles -->
<div style="display: flex; padding: 16px;">

<!-- ❌ Wrong: custom class in global.css for one-off styling -->
<div class="my-special-box">
```

- Every new UI element must be tested at `sm` (mobile) breakpoint before marking done.
- Add to `src/styles/global.css` **only** for: `@tailwind` directives or CSS animations that utility classes cannot achieve.

---

### Environment Variables

```javascript
// ✅ Always use import.meta.env
const GAS_URL = import.meta.env.VITE_GAS_WEBAPP_URL;
const API_KEY = import.meta.env.VITE_FIREBASE_API_KEY;

// ❌ Never hardcode
const GAS_URL = 'https://script.google.com/macros/s/AKfy.../exec';
```

---

## 📋 Part 4: Standard Execution Protocol

When given any task, follow this exact loop:

```
[PHASE 1: UNDERSTAND]
- Re-state the goal in one sentence.
- List all assumptions (schema field names, which data layer, which page).
- If anything is ambiguous → STOP and ask. Do not proceed.

[PHASE 2: PLAN]
- List files to be modified (only what's necessary).
- For each file: state the exact function/block being changed.
- Define success criteria: what does "done" look like?
  1. Modify [file] → [what changes] → verify: [observable outcome]
  2. ...

[PHASE 3: EXECUTE]
- Make changes surgically, one file at a time.
- Output the diff or the complete updated function (not the entire file unless new).
- Do not touch adjacent code.

[PHASE 4: VERIFY]
- State how to verify each success criterion.
- Remove only the orphans YOUR changes created.
- Confirm no environment variables were hardcoded.
```

---

## 🚫 Part 5: Absolute Red Lines

These are never acceptable under any circumstances:

1. **DO NOT** rewrite an entire file when only one function needs updating.
2. **DO NOT** install npm packages without explicit permission. Use native Web APIs first (`fetch`, `crypto`, `URL`, `localStorage`).
3. **DO NOT** mix Tailwind classes with inline `style="..."` attributes.
4. **DO NOT** hardcode `VITE_*` values in source code. Always use `import.meta.env`.
5. **DO NOT** write DOM manipulation code inside `src/services/`.
6. **DO NOT** write Firebase/GAS calls inside `src/pages/` — use the service layer.
7. **DO NOT** leave a listener open (`onValue`, `onAuthStateChanged`) without a cleanup path.
8. **DO NOT** use field names that differ from `DATABASE.md`. When in doubt, check the schema first.
9. **DO NOT** silently pick an interpretation when a task is ambiguous. Ask.
10. **DO NOT** add error handling for scenarios that cannot happen in this stack's normal operation.