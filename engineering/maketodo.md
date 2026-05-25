---
name: todo-generator
description: >
  Generate a structured, recheck-driven TODO.md from a codebase and a problem/feature description.
  Use this skill whenever the user provides code (files, repo dump, or directory structure) alongside
  a bug report, GitHub issue, feature request, or any description of "what needs to change."
  Trigger even if the user just says "ช่วยทำ todo", "สร้าง task list", "วางแผนแก้บัก",
  "plan this feature", "break this down into steps", or pastes an issue with code attached.
  The output is always a TODO.md file — not a chat reply — with phases, recheck criteria per step,
  relevant code snippets, and a final smoke test checklist.
---

# TODO Generator Skill

Produce a **TODO.md** from a codebase + problem description. The output must be a real file
the developer can work through sequentially, checking off tasks and rechecking after each one.

---

## 1. Understand Before Planning

**First: identify the tech stack from the codebase itself.** Do not assume. Read what is there:
- Check `package.json`, `requirements.txt`, `go.mod`, `Gemfile`, `pom.xml`, etc.
- Note the DB layer (Supabase/Postgres, Firebase, Prisma, Django ORM, raw SQL, …)
- Note the frontend framework (Vanilla JS, React/Next.js, Vue, Laravel Blade, …)
- Note the hosting/build setup (Vite, Webpack, Vercel, Cloudflare Pages, …)

Adapt every snippet, file path, and terminal command in the TODO to match the actual stack found.
Never write generic pseudocode when you can write real, runnable commands for that stack.

Before writing a single task, also extract:

| Question | Where to look |
|----------|---------------|
| What files are affected? | Trace from the issue description into the code |
| What is the root cause / feature gap? | Understand current behaviour vs desired |
| Are there DB schema changes? | Look for ORM models, SQL files, migration dirs |
| Are there UI changes? | Look for HTML/JSX/templates |
| Are there logic/handler changes? | Look for controllers, JS handlers, API routes |
| What must NOT change? | Identify adjacent code to stay untouched |
| What are the user-facing effects? | Define a smoke test scenario |

**State your assumptions explicitly at the top of the TODO.md.** If something is ambiguous in
the issue, name it as an assumption rather than silently guessing.

---

## 2. Output Format

Always write to a file: `TODO.md` (use the `create_file` tool, output to `/mnt/user-data/outputs/TODO.md`).
Then call `present_files` to surface it.

### Required sections (in order):

```markdown
# TODO: <Issue Title or Feature Name>

> **Goal:** <One sentence: what done looks like>

---

## Assumptions
- <Any ambiguities resolved by assumption>

---

## Plan Overview

\```
Phase 1: <area>   → verify: <check>
Phase 2: <area>   → verify: <check>
...
\```

---

## Phase N — <Area Name>

### [ ] N.M <Task title>

<Brief explanation of what and why>

<Code snippet if helpful — SQL, JS diff, HTML block>

**Recheck:**
- [ ] <Concrete verifiable check>
- [ ] <Another check>

---

## Final Smoke Test

1. [ ] <End-to-end step>
2. [ ] <End-to-end step>
...

---

## Notes & Known Assumptions

- <Any design decisions, known risks, or out-of-scope items>
```

---

## 3. Phase Design Rules

**Split by concern, not by file.** Group tasks by layer:
- Database / Schema migrations first (blocking everything else)
- Backend / API logic second
- Frontend UI third
- JS/TS wiring fourth
- Cleanup & orphan removal last

**Each phase must have a verify line** in the Plan Overview — one sentence stating how you know
it's done before moving on.

**Every task gets a Recheck block** with ≥1 checkbox that is concrete and testable:
- ❌ "It works" — not specific enough
- ✅ "Row in DB shows `department_id = 3` after save"
- ✅ "`grep -r 'old_field' js/` returns zero matches"
- ✅ "Dropdown shows 10 options when page loads"

---

## 4. Code Snippet Rules

**Every task that changes code must include a ready-to-paste snippet.** No exceptions.
A developer should be able to open the file, find the spot, and paste — never guess.

---

### 4a. Always state WHERE to put the code

Every snippet must open with a placement comment in this format:

```
📁 FILE:     js/admin-page.js
📍 LOCATION: inside function createActivity(), after line that reads `const bonus = ...`
✏️  ACTION:   REPLACE / ADD AFTER / ADD BEFORE / DELETE
```

Use the exact function/block name from the real codebase, not a generic description.

**Placement comment rules by action:**

| Action | When to use | Location phrasing |
|--------|-------------|-------------------|
| `REPLACE` | Swapping old code for new | "Replace lines X–Y" or "Replace the block starting with `const cont =`" |
| `ADD AFTER` | Inserting new code with no existing equivalent | "Add after the line `setupSubDepartmentToggle(...)`" |
| `ADD BEFORE` | New code that must precede something | "Add before the closing `}` of `init()`" |
| `DELETE` | Removing code with no replacement | Show the exact lines to delete, no NEW block needed |

---

### 4b. Snippet format by action type

**REPLACE — show old code, then new code ready to paste over it:**

```js
📁 FILE:     js/admin-page.js
📍 LOCATION: inside createActivity(), replace the continent block
✏️  ACTION:   REPLACE

// ── OLD (delete this) ──────────────────────────────────────
const cont = document.getElementById('act-continent').value || null;

// ── NEW (paste this in its place) ──────────────────────────
const dept    = document.getElementById('act-department').value     || null;
const subDept = document.getElementById('act-sub-department').value || null;
```

**ADD AFTER — no old code to show, just placement + new block:**

```js
📁 FILE:     js/admin-page.js
📍 LOCATION: inside init(), add after the two existing setupSubDepartmentToggle() calls
✏️  ACTION:   ADD AFTER

setupSubDepartmentToggle('act-department', 'act-sub-department');
setupSubDepartmentToggle('edit-department', 'edit-sub-department');
// ↑ already exists — add the line below after these two:
loadDepartmentOptions();
```

**DELETE — show exact code to remove, no replacement:**

```html
📁 FILE:     html/admin.html
📍 LOCATION: inside #activity-form, the continent <select> block
✏️  ACTION:   DELETE

<select id="act-continent">
  <option value="">Select Continent Theme (Optional)</option>
  <option value="1">Novatopia (Green)</option>
  <option value="2">Empathia (Red)</option>
</select><br />
```

---

### 4c. What "ready-to-paste" means by layer

| Layer | Snippet must include |
|-------|----------------------|
| SQL / DB migration | Full `ALTER TABLE`, `CREATE TABLE`, or `INSERT` — runnable as-is |
| JS/TS logic | Exact function or block with placement header + OLD/NEW clearly separated |
| HTML / template | Complete element being added or replaced, with placement header |
| Shell / terminal | Exact command with flags, e.g. `grep -r "continent_id" js/ html/` |
| Config / env | Exact key and example value |

---

### 4d. Long snippets

**When a snippet exceeds 30 lines:** split into sub-tasks, each with its own placement header and
its own Recheck. Never dump 80 lines into one task — a developer should verify after each piece.

**Match the codebase's existing style** (indentation, quote style, semicolons, naming).
Read 2–3 surrounding lines of the real file and mirror them exactly.

---

## 5. Smoke Test Section

Always end with a numbered end-to-end test checklist.
Each item must be doable in a browser or terminal — no abstract checks.

Format:
```markdown
## Final Smoke Test

1. [ ] <Actor> does <action> → expect <result>
2. [ ] <Actor> does <action> → expect <result>
```

Cover the happy path + at least one negative/edge case (e.g., duplicate scan, missing required field).

---

## 6. Notes & Assumptions Section

Always include this section at the bottom. Use it for:
- Design decisions made without explicit instruction ("hardcoded in JS, not fetched from DB, because list is fixed")
- Things intentionally left untouched and why
- Known security gaps or tech debt surfaced but out of scope
- Features explicitly excluded from this issue

---

## 7. Surgical Change Reminder

When analysing the codebase:
- **Do not plan changes to adjacent code** that the issue does not mention
- **Flag but do not fix** pre-existing issues you notice
- If your changes create orphaned references (old field names, unused imports), include cleanup as a
  dedicated task in the Cleanup phase
- Match the existing code style in all snippets

---

## 8. Quick Self-Check Before Writing

Ask yourself before finalising the TODO.md:

1. Can a developer work through this **top to bottom without backtracking**?
2. Does every task have a **recheck** that proves it's done?
3. Does every snippet have a **placement header** (📁 FILE / 📍 LOCATION / ✏️ ACTION)?
4. For every REPLACE snippet — is the **old code shown** so the dev knows exactly what to remove?
5. Are there **zero tasks** that touch code not mentioned in the issue?
6. Does the smoke test cover the **full user journey** from trigger to visible result?
7. Are all **assumptions named** rather than silently baked in?

If any answer is no — fix the TODO before outputting.