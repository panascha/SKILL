# Universal Refactor Principles
> A language-agnostic instruction set for AI-assisted code refactoring.
> **Prime Directive:** Preserve all behaviour. Change structure only.

---

## 1. Audit Before You Move

- Read the entire file before touching anything.
- Map every function, class, and variable to one of: **Logic / Data / UI / Config / I/O**.
- List all globals and shared state explicitly before extraction begins.
- Identify the entry point (the first thing that runs) — it becomes your `app` / `main` file.

---

## 2. Separation of Concerns — The Five Layers

| Layer | Responsibility | Typical filename |
|---|---|---|
| **Config** | Constants, environment values, feature flags | `config`, `constants`, `env` |
| **Data** | Storage, cache, DB queries, migrations | `db`, `store`, `repository` |
| **I/O** | Network, API calls, file read/write | `api`, `client`, `service` |
| **Logic** | Business rules, algorithms, state machines | `core`, `engine`, `utils` |
| **UI** | DOM, events, rendering, user interaction | `ui`, `view`, `components` |

A function belongs in the layer it *primarily* serves. If it spans two layers, split it.

---

## 3. Extraction Order (Always Bottom-Up)

Extract in this sequence to avoid undefined reference errors:

```
Config → Data → I/O → Logic → UI → Entry Point
```

Never extract a file that depends on something not yet extracted.

---

## 4. Global State Rules

- Declare shared mutable state **once**, in one place (e.g. `config.js` or a `state.js`).
- All modules reference the same object — they never re-declare it.
- Prefer a single namespace object over scattered globals:
  ```js
  window.APP = { user: null, data: [], status: 'idle' };  // JS example
  ```
- After extraction, grep for duplicate variable declarations across all files.

---

## 5. The Non-Negotiables (Never Break These)

1. **Do not rename** functions or variables during a refactor pass — that is a separate task.
2. **Do not simplify logic** — move code verbatim first, optimise later.
3. **Do not merge files** that serve different layers just because they are small.
4. **Do not split files** that share tightly coupled state — keep them together.
5. **Preserve fragile code as-is** — mark it with `// FRAGILE: do not refactor` and skip it.

---

## 6. Load Order & Dependency Management

- In script-tag projects: load files in extraction order (Config first, Entry Point last).
- In module systems (`import`/`export`, `require`): enforce the same order via imports.
- Draw a dependency graph if circular dependencies are suspected — resolve before moving files.

```
config ← db ← api ← logic ← ui ← app
         ↑___________________________↑  (app wires everything)
```

---

## 7. Stylesheet / CSS Extraction

- Move all styles to an external file before touching JS.
- Preserve CSS custom properties (`:root` variables) at the very top.
- Group rules in this order: **Reset → Variables → Base/Typography → Layout → Components → Utilities**.
- Never inline styles in JS unless the original code does so (leave those intact).

---

## 8. Validation Checklist (Run After Each File Is Created)

- [ ] No function is defined in more than one file.
- [ ] No variable is declared at global scope more than once.
- [ ] The entry point file calls everything in the correct order.
- [ ] The app loads and behaves identically to before the refactor.
- [ ] Each file has a single, describable purpose (the "one-sentence test").

---

## 9. Commit Strategy

```
refactor: extract config constants        ← one file per commit
refactor: extract db/storage helpers
refactor: extract api/network layer
refactor: extract core logic
refactor: extract ui event handlers
refactor: wire entry point, clean index
```

Small commits make regressions easy to locate and revert.

---

## 10. The One-Sentence Test

Before finalising any file, complete this sentence:

> *"This file is responsible for ___________  and nothing else."*

If you cannot complete it with a single concern, the file needs to be split further.