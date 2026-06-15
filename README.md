# Aleph

### 📖 [Read the book](book/Manifest.md)

Aleph is a dual-purpose project: it is a rigorously verified mathematical textbook built from
Zermelo-Fraenkel set theory (ZFC), and a custom Python verifier built to check it.

By utilizing **Literate Formalization**, this repository contains the definitive Markdown source of
the text—blending human-readable pedagogical prose with machine-readable First-Order Logic (FOL)
proofs—alongside the deterministic tooling required to verify its absolute correctness.

## Setup & Development

To clone, set up the environment, and verify the project:

```bash
# Clone the repository
git clone https://github.com/ethanex8/aleph.git
cd aleph

# Install dependencies (requires uv)
uv pip install -e ".[dev]"

# Install pre-commit hooks
python -m pre_commit install

# Run all checks (formats, tests, type checks, and verifies the book)
python -m pre_commit run --all-files
```

## System Overview

To maintain a strict scope, the Aleph verifier operates under the following constraints:

- **Deterministic:** A Python-based First-Order Logic (FOL) verifier with zero cloud dependencies.
- **Verification, Not Proving:** Aleph does not generate proofs; it only verifies explicit steps.
- **Ingested Foundations:** The verifier does not hardcode ZFC; axioms are ingested from the
  textbook files themselves.
- **Literate Source:** A single source of truth (`.md`) for both pedagogy and logic.

### Documentation Map

- **[System Design](DESIGN.md):** Deep dive into the verification pipeline, pipeline architecture,
  dependency management, and internal lifecycles.
- **[Language Reference](LANGUAGE.md):** Detailed syntax for FOL blocks, indentation rules, and the
  full table of inference rules.
- **[Agent Instructions](AGENTS.md):** Workflow guidelines, verification commands, and critical
  constraints for contributors and AI agents.

## Mathematical Scope

The textbook builds a chain of formal reasoning from primitive set assumptions to advanced
mathematical machinery across four major epochs:

- **Epoch I: Foundations**: FOL deduction, ZFC Axiomatization, Set Theory (Relations, Functions,
  Ordinals).
- **Epoch II: Algebraic Structures**: Groups, Rings, Fields, Vector Spaces, and Linear Algebra.
- **Epoch III: Continuum & Topology**: Construction of Number Systems ($\mathbb{R}$, $\mathbb{C}$),
  General Topology, and Real Analysis.
- **Epoch IV: Mathematical Physics**: Differential Geometry (Manifolds, Exterior Calculus) and
  Operator Theory (Hilbert Spaces).

## Repository Structure

```text
Aleph/
├── tools/                       # The Python verification toolchain
├── book/                        # The mathematical source code (Markdown)
│   └── Manifest.md              # The topological build manifest
├── tests/                       # Test suites
├── LANGUAGE.md                  # Syntax & Rules Reference
├── DESIGN.md                    # Architecture & Internals
├── AGENTS.md                    # Workflow & Constraints
└── README.md
```
