# AGENTS.md

## Purpose

This repository should be maintained with a strong emphasis on:

- modularity
- readability
- maintainability
- consistency
- safe refactoring
- low-complexity solutions

All agents working in this codebase should optimize for **DRY**, **KISS**, and **separation of concerns**.

The goal is not just to make the code “work,” but to make it easy for future developers to understand, extend, and safely modify.

---

## Guiding principles

### DRY
Do not duplicate logic, constants, types, or configuration unnecessarily.

If the same logic appears in multiple places, extract it into a helper, utility, shared component, or reusable abstraction where appropriate.

Do not over-abstract prematurely. Shared code should only be extracted when it improves clarity and reduces duplication.

### KISS
Prefer the simplest solution that is easy to understand and maintain.

Avoid cleverness, unnecessary indirection, deep abstraction layers, or patterns that make the code harder to follow.

### Single responsibility
Each file, module, function, and component should have one clear purpose.

Do not allow large files to accumulate unrelated responsibilities.

### Separation of concerns
Keep data, business logic, rendering, helpers, configuration, and types separated into appropriate files/modules.

A file should not simultaneously define raw data, rendering behavior, helper logic, and application flow unless there is a strong reason.

### Readability over cleverness
Code should be easy to scan and understand quickly.

Prefer explicit naming, simple control flow, and predictable organization.

### Safe change over broad rewrites
When refactoring, preserve current behavior unless a change is explicitly required.

Do not perform unnecessary rewrites that increase risk.

---

## File and module organization

### General expectations
- Keep files focused and reasonably small.
- Split large files when they contain multiple responsibilities.
- Group related logic into clearly named folders.
- Prefer colocating related files when they belong to the same feature or domain.
- Prefer shared modules only when code is genuinely cross-cutting.

### Suggested module boundaries
Where applicable, separate code into:
- components
- objects/entities
- services
- helpers/utils
- constants/config
- types/interfaces
- hooks/composables
- data definitions
- feature-specific modules

### Imports
- Import from the most appropriate source, not from arbitrary deep files unless needed.
- Avoid circular dependencies.
- Keep dependency direction clean and intentional.
- Shared utilities should not depend on feature modules.

---

## Refactoring rules

When performing refactors:

1. Preserve behavior unless explicitly told otherwise.
2. Prefer incremental refactors over massive rewrites.
3. Update imports and exports cleanly.
4. Remove dead code only when clearly unused and safe to delete.
5. Consolidate duplicate logic carefully.
6. Extract helpers when it improves clarity and reuse.
7. Do not introduce abstractions that are harder to understand than the original duplication.
8. Keep public APIs stable unless there is a strong reason to change them.
9. If you must change an API, update all call sites safely.
10. Leave the codebase in a cleaner state than you found it.

---

## Function and component standards

### Functions
- Functions should do one thing well.
- Keep functions short where practical.
- Prefer descriptive names over comments explaining vague logic.
- Extract deeply nested or repeated logic into helpers.
- Avoid long parameter lists when a structured object is clearer.

### Components
- Components should be focused and composable.
- Split overly large components into smaller child components or feature modules.
- Keep rendering concerns separate from heavy business logic where possible.
- Reuse shared UI patterns rather than duplicating markup and behavior.

### Helpers and utilities
- Helpers should be pure when possible.
- Utility files should not become dumping grounds.
- Group helpers by domain or purpose, not just by convenience.

---

## Naming conventions

- Use clear, descriptive, intention-revealing names.
- Prefer explicit names over overly short ones.
- Avoid vague names like `stuff`, `data`, `helpers`, `misc`, `temp`, or `newCode`.
- Name files based on responsibility.
- Name modules according to what they own, not where they happened to be created.

Examples:
- good: `userProfileService.ts`
- good: `renderToolbar.ts`
- good: `pricingConstants.ts`
- avoid: `utils2.ts`
- avoid: `randomHelpers.ts`
- avoid: `finalFinalVersion.ts`

---

## Comments and documentation

- Write code that is readable enough to reduce the need for excessive comments.
- Add comments only where intent, constraints, or non-obvious reasoning need explanation.
- Do not add noisy comments that restate obvious code.
- Keep README and relevant docs updated when architecture changes meaningfully.

---

## Error handling

- Handle errors deliberately.
- Do not silently swallow failures unless there is a clear reason.
- Prefer predictable failure behavior.
- Surface actionable errors when appropriate.
- Validate assumptions at boundaries.

---

## Consistency rules

- Follow existing project conventions unless there is a strong reason to improve them.
- If introducing a better pattern, apply it consistently within the touched area.
- Do not mix multiple competing patterns in the same feature without reason.

Consistency across the codebase is often more valuable than a locally “perfect” pattern.

---

## Dependency rules

- Do not add new dependencies unless clearly justified.
- Prefer existing platform or project utilities before introducing libraries.
- Avoid dependencies for trivial problems.
- Keep the dependency graph as simple as possible.

---

## Performance and complexity

- Do not over-optimize prematurely.
- Avoid obviously wasteful patterns in hot paths.
- Prefer maintainable code first, then optimize where real bottlenecks exist.
- If a change increases complexity for performance reasons, document why.

---

## Testing and validation

When making changes:
- ensure the code still builds
- ensure imports resolve correctly
- ensure no circular dependencies are introduced
- ensure the affected behavior still works
- ensure refactors do not introduce accidental API regressions

If tests exist, update or add tests where appropriate.
If tests do not exist, do not invent a massive testing framework as part of a simple refactor unless requested.

---

## What to avoid

Do not:
- create giant multi-purpose files
- mix unrelated concerns in one module
- duplicate constants or business logic
- introduce unnecessary abstractions
- perform stylistic rewrites with no architectural value
- rename things gratuitously
- leave dead code behind after replacing it
- add dependencies for minor convenience
- break behavior in the name of “cleanup”
- create confusing folder structures with unclear ownership

---

## Preferred workflow for agents

When working on a task:

1. Understand the current structure first.
2. Identify clear boundaries of responsibility.
3. Make the smallest meaningful improvement that moves the code toward better structure.
4. Refactor incrementally when possible.
5. Keep imports, naming, and ownership clean.
6. Summarize architectural changes clearly.

---

## Refactor decision checklist

Before making a change, ask:

- Does this reduce duplication?
- Does this simplify the code?
- Does this make ownership clearer?
- Does this separate concerns more cleanly?
- Does this preserve current behavior?
- Is this abstraction actually helpful?
- Will the next developer understand this quickly?

If the answer to most of these is no, do not make the change.

---

## End goal

The end state of this repository should be a codebase where:

- each module has a clear purpose
- shared logic lives in intentional reusable places
- components and objects are modular
- helpers are extracted thoughtfully
- files are easy to navigate
- adding new features does not require editing giant monolith files
- refactors are safe and predictable
- the code remains simple, clean, and easy to extend