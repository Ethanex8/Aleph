# Aleph Agent Instructions

This document outlines the workflow, constraints, and pitfalls for AI agents (and human contributors) working on the **Aleph** repository. 

Always check this document and the system design guidelines in [DESIGN.md](DESIGN.md) before making code changes or updating logic files.

---

## 📖 System Design & Documentation Maintenance

Refer to [DESIGN.md](DESIGN.md) for a comprehensive overview of the verifier's architecture, pipeline, data structures, and mathematical inference rules.

> [!IMPORTANT]
> If you make any core architecture modifications (such as changing grammar rules, adding mathematical inference rules, or altering scope/context handling logic) or change system behaviors, you **must** update all relevant documentation Markdown files (such as [DESIGN.md](DESIGN.md), [LANGUAGE.md](LANGUAGE.md), and [AGENTS.md](AGENTS.md)) accordingly to reflect the changes.


---

## 🛠️ Verification & Testing Commands

To verify and style changes, execute the following commands in the workspace root:

*   **Verify the Mathematical Book:**
    ```bash
    python -m tools verify
    ```

*   **Run the Test Suite:**
    ```bash
    python -m pytest
    ```
    > [!IMPORTANT]
    > While the end-to-end build test asserts lower-bound counts (meaning new files/axioms/theorems won't break the global total checks), specific tests still verify theorem existence and stand-alone file contexts. You **must** run `python -m pytest` when modifying the math structure to ensure everything passes.

*   **Format Proofs (FOL Blocks):**
    ```bash
    python -m tools format
    ```
    To only check/validate formatting without modifying files (e.g. in CI pipelines):
    ```bash
    python -m tools format --check
    ```

*   **Lint and Format Python Code (Ruff):**
    To format Python files:
    ```bash
    python -m ruff format .
    ```
    To check for lint violations:
    ```bash
    python -m ruff check .
    ```
    To automatically fix lint violations:
    ```bash
    python -m ruff check --fix .
    ```

*   **Static Type Checking (mypy):**
    ```bash
    python -m mypy tools/
    ```

*   **Run Tests with Coverage:**
    ```bash
    python -m pytest -v --cov=tools --cov-report=term-missing
    ```

*   **Pre-commit Hooks:**
    Install hooks (one-time setup):
    ```bash
    pre-commit install
    ```
    Run all hooks manually:
    ```bash
    pre-commit run --all-files
    ```


---

## 📚 Book & Manifest Architecture

All files under `book/` are managed via a Directed Acyclic Graph (DAG) specified in [Manifest.md](file:///c:/Users/erh50/Aleph/book/Manifest.md).

1.  **Strict PascalCase Naming:** Every directory, file, and mathematical identifier (Axioms, Theorems, Definitions) must strictly use `PascalCase`.
2.  **Manifest Registration:** If you create a new `.md` section under `book/`, you **must** register it in [Manifest.md](file:///c:/Users/erh50/Aleph/book/Manifest.md) along with its exact `imports` and `exports`. Orphaned files will fail verification.
3.  **Imports/Exports:** 
    *   `exports` are defined as bare identifiers (e.g., `Extensionality`).
    *   `imports` must be fully qualified (e.g., `SetTheory.Extensionality.Extensionality`).
    *   Self-references within the same file do not need to be imported.

---

## ✍️ Markdown & LaTeX Prose Guidelines

When authoring pedagogical prose in math files, follow these formatting guidelines:

1.  **Use Unicode Math Symbols:** Prefer Unicode characters (e.g., `⊆`, `∀`, `∈`, `⟹`) instead of LaTeX macros (e.g., `\subseteq`, `\forall`) inside prose math blocks (like `$A ⊆ B$`). Markdown parsers can consume backslashes, breaking LaTeX rendering. Unicode symbols match the logic blocks and render reliably.
2.  **Avoid Wrapping Math in Emphasis:** Do not nest inline math directly inside markdown italics or bold blocks (e.g., avoid `*If $A ⊆ B$ ...*`). Apply emphasis only to the surrounding text words instead.
3.  **Strict Identifier Spelling:** All references to mathematical terms in prose must match the exact PascalCase spelling of the identifier defined in the `fol` blocks.

---

## 🔍 Logic & Proof Rules

When writing or editing fenced logic blocks (` ```fol `), respect the parser constraints defined in [LANGUAGE.md](file:///c:/Users/erh50/Aleph/LANGUAGE.md):

1.  **Explicit Axiom Loading:** The `UI` (Universal Instantiation) rule and other rules expect a proof line reference (e.g., `[UI 16, A]`). You cannot directly instantiate an axiom by name (e.g., `[UI Extensionality, A]`). You must first load the axiom onto a standalone proof line using `[Axiom Extensionality]` and then reference that line number.
2.  **Isolated Logic Context:** The verifier only parses content within `fol` blocks and does not inherit any variables or assumptions declared in the surrounding markdown prose.
3.  **Inference Rules:** The verifier only supports the rules explicitly defined in [tools/inference/](file:///c:/Users/erh50/Aleph/tools/inference/). If a mathematical proof requires a new inference pattern, the verifier's Python code must be updated first.
4.  **Strict Proof Indentation:** Proof lines inside `fol` blocks must be indented strictly according to their logical scoping depth (4 spaces per scope level). `Let` statements and `Assume` statements open one new scope level each. Scope-closing rules (`UG`, `ImplIntro`, `ExistsElim`) sit at the parent scope's indentation level (sharing the column of their opener). Mismatched indentation causes a verifier parse error.
5.  **Header and Body Indentation:** Top-level declaration headers (`axiom`, `theorem`, `proof:`, etc.) must have **zero** indentation. The formulas immediately following these headers must have exactly **4 spaces** of indentation.
