# Aleph Agent Instructions

This document outlines the workflow, constraints, and critical rules for AI agents and contributors.

## 🛠️ Setup & Commands

> [!IMPORTANT]
> **Prerequisite:** You must complete the setup in [README.md](README.md) before running tools.

- **Verify Book**: `python -m tools verify`
- **Run Tests**: `python -m pytest`
- **Format Logic**: `python -m tools format`
- **Lint/Format Python**: `python -m ruff check --fix .` and `python -m ruff format .`
- **Type Check**: `python -m mypy tools/`

## 🔄 Contribution Workflow

1. Create a branch for changes.
2. Run all local checks (verify, test, lint, format).
3. Submit a Pull Request. CI must pass before merging.

## ⚠️ Critical Constraints

### Naming & Registration
- **PascalCase**: All directories, files, and identifiers (Axioms, Theorems, etc.) must use
  `PascalCase`.
- **Manifest**: New `.md` sections must be registered in [Manifest.md](book/Manifest.md) with
  `imports` and `exports`.
- **Imports**: Must be fully qualified (e.g., `SetTheory.Extensionality.Extensionality`).

### Logic & Indentation
- **Header Indentation**: Keywords (`axiom`, `theorem`, `proof:`, etc.) must have **0 indentation**.
- **Body Indentation**: Claims immediately following headers must have **4 spaces**.
- **Proof Scoping**: Each `Let` or `Assume` opens one scope (+4 spaces). Closing rules (`UG`,
  `ImplIntro`, `ExistsElim`) must match the opener's column.
- **Axiom Citation**: You cannot instantiate an axiom by name in a rule (e.g., `[UI AxiomName, x]`).
  You must first load it: `1. P [Axiom AxiomName]`.

### Prose & Formatting
- **Unicode Math**: Use `⊆`, `∀`, `∈`, `⟹` in prose. Avoid LaTeX macros (e.g., `\forall`).
- **No Wrapped Math**: Do not nest `$math$` inside `*italics*` or `**bold**`.
- **Identifier Accuracy**: Prose references must match the exact PascalCase identifier.

## 📖 Documentation Maintenance

If you modify the verifier's architecture, grammar, or inference rules, you **must** update
[DESIGN.md](DESIGN.md) and [LANGUAGE.md](LANGUAGE.md) accordingly.
