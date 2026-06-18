---
name: karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria.
license: MIT
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Clean Code Delivery

**Send only what changed. Two parts per section: original then replacement. Review before sending.**

When returning code changes, split every changed section into exactly two parts.

### Output Format — Use Artifact with Copy Buttons

Always render ORIGINAL and REPLACEMENT with two separate code blocks, each with its own copy button. output plain markdown code fences for code changes.

Structure per changed section:

```
Section: <function/block name or location>
```

Then render containing:
- **ORIGINAL block** — exact code from the source file, with a "Copy Original"
- **REPLACEMENT block** — new code ready to paste, with a "Copy Replacement"

### Rules

- Both parts must cover the same scope — same start line, same end line.
- Never show a partial original (no `...` or trimmed context). Full block only.
- One section per logical change. If two functions change, two sections.
- Do not include unchanged code outside the section boundaries.

### Self-review checklist before every code reply

1. Is this the minimal change that solves the problem?
2. Does each ORIGINAL block match exactly what's in the file?
3. Does each REPLACEMENT fully cover the same scope as the ORIGINAL?
4. Did I re-read it once after writing?
5. Are ORIGINAL and REPLACEMENT in separate copy-able blocks in the artifact?