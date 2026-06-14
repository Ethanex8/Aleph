# Aleph

### 📖 [Read the book](book/Manifest.md)

Aleph is a dual-purpose hobby project: it is a rigorously verified mathematical textbook built from Zermelo-Fraenkel set theory (ZFC), and it is the custom, companion Python verifier built to check it.

By utilizing Literate Formalization, this repository contains the definitive Markdown source of the text—blending human-readable pedagogical prose with machine-readable First-Order Logic (FOL) proofs—alongside the deterministic tooling required to verify its absolute correctness. The mathematical content focuses entirely on standard, theoretical domains, including set theory, algebra, analysis, and topology.

The verification engine is built as a local, offline toolchain with a codebase restricted entirely to standard, open-source libraries. The Python script operates without cloud dependencies or generative AI components, relying instead on a deterministic execution model designed solely to validate explicit, hardcoded mathematical rules against static Markdown files. The ultimate goal of this toolchain is to formally verify the correctness of the stated mathematics.

## Setup & Development

To clone, set up the development environment, and verify the project using the pre-commit workflow:

```bash
# Clone the repository
git clone https://github.com/ethanex8/aleph.git
cd aleph

# Install dependencies (requires uv)
uv pip install -e ".[dev]"

# Install the pre-commit hooks (one-time setup)
python -m pre_commit install

# Run all checks manually to verify setup (formats, tests, type checks, and verifies the book)
python -m pre_commit run --all-files
```

These checks run automatically on every `git commit` to ensure code quality and logical consistency.

If you add a new mathematical section `.md` file under `book/`, register it in [`Manifest.md`](book/Manifest.md) with its `imports` and `exports`. For a full list of invariants checked during verification, see [Integrity Invariants](#integrity-invariants).

## System Boundaries

To maintain a strict scope, the Aleph verifier operates under the following constraints:

**Goals:**
*   Create a deterministic, Python-based First-Order Logic (FOL) verifier.
*   Maintain a single source of truth (`.md`) for both pedagogy and logic.
*   Prevent proof explosion via shallow AST pattern matching.
*   Support axiom schemas (Specification, Replacement) parameterized by arbitrary formulas.

**Non-Goals:**
*   **Automated Theorem Proving:** Aleph does not generate proofs; it only verifies explicitly provided steps.
*   **Hardcoded Axioms:** The verifier does not hardcode ZFC; axioms are ingested as baseline `.md` data files.

## System Architecture

For a detailed analysis of the Aleph verification pipeline, parser subsystems, topological graph builds, and scoping/inference internals, see the [Aleph System Design Document](DESIGN.md).

The system enforces a strict boundary between human pedagogy and machine logic. All naming conventions across directories, files, and mathematical identifiers are strictly unified under **PascalCase** to maintain logical coherence.

| Layer | Medium | Purpose | Verifier Action |
| :--- | :--- | :--- | :--- |
| **Prose Layer** | Standard Markdown & LaTeX | Pedagogical intuition, narrative, formatting | Ignored by verifier |
| **Logic Layer** | Fenced `fol` blocks | Strict First-Order Logic proofs | Parsed, AST-matched, verified |

### Verification Mechanics

The custom Python verifier uses deterministic structural AST matching rather than deep logical expansion to evaluate proofs efficiently.

*   **Rules of Inference:** Hardcoded as Python evaluation functions for instant evaluation.
*   **Opaque Theorems:** Previously proven theorems are verified via shallow signature matching. The verifier verifies input lines match the required AST signature and authorizes the output without re-evaluating the internal proof tree.
*   **Shallow Macros:** Definitions act as syntactic sugar and are unpacked exactly one layer deep unless recursively commanded.
*   **Axiom Schemas:** Parameterized axiom templates (e.g., Specification, Replacement) that can be instantiated with any concrete first-order formula via second-order substitution.

### Inference Rules

The verifier currently supports 11 hardcoded rules of inference (such as Modus Ponens, Universal Instantiation, etc.). For a complete list of inference rules and their syntax, please see the [Aleph FOL Language Reference](LANGUAGE.md).

## Mathematical Scope

The textbook builds a self-contained, unbroken chain of formal reasoning from primitive set assumptions to advanced mathematical machinery. Dependency resolution and execution sequence are governed dynamically by a Directed Acyclic Graph (DAG). The textbook content spans four major logical epochs:

```text
[Axioms & FirstOrderLogic] --> [SetTheory] --> [AbstractAlgebra] --> [MathPhysics]
                                    |
                                    +---> [Analysis] -----------------+
```

*   **Epoch I: Foundations (Axioms, FirstOrderLogic, SetTheory)**
    *   First-Order Logic deduction, inference rules, and syntax.
    *   ZFC Axiomatization, the empty set, power sets, and pairing.
    *   Relations, functions, order theory, and the construction of the Ordinals and Cardinals.
*   **Epoch II: Algebraic Structures (AbstractAlgebra)**
    *   Monoids, Groups (Lagrange's theorem, quotient groups), Rings, and Fields.
    *   Vector Spaces, linear transformations, inner product spaces, and spectral theory.
*   **Epoch III: Continuum & Topology (Analysis)**
    *   Construction of the Number Systems: $\mathbb{N} \rightarrow \mathbb{Z} \rightarrow \mathbb{Q} \rightarrow \mathbb{R}$ (via Dedekind cuts or Cauchy sequences) $\rightarrow \mathbb{C}$.
    *   General Topology: Metric spaces, open/closed sets, compactness, and continuity.
    *   Real Analysis: Limits, differentiation, Riemann/Lebesgue integration, and functional spaces ($L^p$ spaces).
*   **Epoch IV: Mathematical Physics Foundations (MathPhysics)**
    *   Differential Geometry: Manifolds, tangent spaces, exterior calculus, and curvature (the language of General Relativity).
    *   Operator Theory: Hilbert spaces, self-adjoint operators, and bounded/unbounded operators (the language of Quantum Mechanics).

## Literate Formalization

The source code of the textbook consists entirely of Markdown (`.md`) files. The system strictly separates the layers using fenced code blocks explicitly tagged with `fol`.

For a full breakdown of the allowed FOL block declarations (Axioms, Schemas, Definitions, Theorems, etc.) and proof syntax, see the [Aleph FOL Language Reference](LANGUAGE.md).

During compilation, the verifier extracts all contents within the `fol` fences and passes them to the verifier. The surrounding Markdown prose is entirely ignored.

### Authoring & Development Guidelines

For specific mathematical formatting conventions, LaTeX/Unicode usage guidelines, and logical/verification constraints when writing or editing math sections, please consult [AGENTS.md](AGENTS.md).

For developers looking to understand or extend the verification engine, parser grammar, or AST nodes, please consult the [Aleph System Design Document](DESIGN.md).

## Dependency Management

The system enforces a strict, hierarchical dependency graph through [`Manifest.md`](book/Manifest.md), which is the **single source of truth** for section ordering, imports, and exports.

### The Manifest ([`Manifest.md`](book/Manifest.md))

The `Manifest.md` file acts as the central registry, using **Literate Formalization** to embed `yaml` blocks within markdown headers. Each section declares its **imports** (fully qualified identifiers it consumes from other sections) and **exports** (bare identifier names it produces):

```markdown
## [SetTheory.Extensionality](SetTheory/Extensionality.md)

```yaml
sections:
  - name: SetTheory.Extensionality
    imports: []
    exports: [Extensionality]
```
```

**Exports** are bare identifier names. Their fully qualified path is implicit from the section path (e.g., `SetTheory/Extensionality.md` exports `Extensionality` → qualified name is `SetTheory.Extensionality.Extensionality`).

**Imports** are fully qualified. Self-references within a file are not imports — they are inherently available.

The verifier **derives the dependency graph** automatically from import/export resolution. No manual dependency edges are needed.

### Integrity Invariants

The verifier enforces these invariants on every verification run:

1.  **Completeness:** Every `.md` file under `book/` must be registered in [`Manifest.md`](book/Manifest.md). Orphaned files are an error.
2.  **Export Validation:** Every section's declared exports must exactly match what the file actually produces. Renamed or removed identifiers are caught immediately.
3.  **Import Resolution:** Every qualified import must resolve to a valid section and exported identifier. Dangling references are an error.
4.  **Acyclicity:** The dependency graph must be a DAG. Cycles are detected and rejected.

## Repository Structure

Directories, files, and core identifiers are named strictly using PascalCase. Ordering and compilation hierarchies are decoupled from file names to prevent refactoring cascades.

```text
Aleph/
├── tools/                       # The Python verification toolchain
│   ├── parser/                  # Lark EBNF grammar and AST transformers
│   └── verifier/                # Verification loop and inference rules
├── book/                        # The mathematical source code (Markdown)
│   ├── SetTheory/               # ZFC Foundations
│   └── Manifest.md                 # Topological manifest (the DAG)
├── tests/                       # Test suites
├── pyproject.toml               # Python packaging (PEP 621)
├── LANGUAGE.md                  # Aleph FOL Language Reference
└── README.md
```
