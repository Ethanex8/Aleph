# Aleph FOL Language Reference

Aleph uses a custom First-Order Logic (FOL) language. This document describes the syntax and rules
for `fol` blocks.

## Top-Level Declarations

### Axioms & Schemas

Axioms are fundamental truths. Schemas are parameterized templates using Greek letters (`Φ`, `φ`,
`ψ`, `χ`) for formula placeholders.

```text
axiom Extensionality:
    ∀x ∀y (∀z (z ∈ x ⟺ z ∈ y) ⟹ x = y)

schema Specification(φ(x)):
    ∀A ∃B ∀x (x ∈ B ⟺ (x ∈ A ∧ φ(x)))
```

### Definitions

Definitions introduce notation as biconditionals or equalities. They can be identifiers, infix
relations, or predicates.

```text
definition A ⊆ B:
    ∀x (x ∈ A ⟹ x ∈ B)

definition IsEmpty(A):
    ∀x ¬(x ∈ A)
```

### Constants & Operations

Verified constructs requiring prior existence and uniqueness theorems.

```text
constant ∅:
    ∀x ¬(x ∈ ∅)
existence: EmptySetExistence
uniqueness: EmptySetUniqueness

operation A ∪ B:
    ∀x (x ∈ A ∪ B ⟺ (x ∈ A ∨ x ∈ B))
existence: UnionExistence
uniqueness: UnionUniqueness
```

### Theorems

Theorems consist of a claim and a line-by-line proof.

```text
theorem Reflexivity:
    ∀A (A ⊆ A)
proof:
    1. Let A be arbitrary               [Hypothesis]
        2. Let x be arbitrary            [Hypothesis]
            3. Assume x ∈ A              [Hypothesis]
            4. x ∈ A ⟹ x ∈ A           [ImplIntro 3, 3]
        5. ∀x (x ∈ A ⟹ x ∈ A)          [UG 4, x]
        6. A ⊆ A                         [Def ⊆, 5]
    7. ∀A (A ⊆ A)                        [UG 6, A]
qed
```

## Proof Syntax & Scoping

### Indentation Rules

The verifier enforces strict 4-space indentation for logical scopes:

1. **Declaration Headers** (`axiom`, `theorem`, `proof:`, etc.): **0 spaces**.
2. **Declaration Bodies** (the claim): **4 spaces**.
3. **Proof Lines**:
   - Start at **4 spaces** (Depth 1).
   - `Let` and `Assume` statements open a new scope (+4 spaces).
   - Scope-closing rules (`UG`, `ImplIntro`, `ExistsElim`) sit at the **parent** indentation level.

### Justifications

Every line must end with a bracketed justification `[Rule Arg1, Arg2, ...]`.

| Category | Rule | Tag | Description | | :--- | :--- | :--- | :--- | | **Propositional** |
Hypothesis | `[Hypothesis]` | Introduces assumption or arbitrary variable. | | | Modus Ponens |
`[MP i, j]` | From `P ⟹ Q` (i) and `P` (j), derive `Q`. | | | Modus Tollens | `[MT i, j]` | From
`P ⟹ Q` (i) and `¬Q` (j), derive `¬P`. | | | Disj. Syllogism | `[DS i, j]` | From `P ∨ Q` (i) and
`¬P` (j), derive `Q`. | | | Conjunction | `[AndIntro i, j]` | From `P` (i) and `Q` (j), derive
`P ∧ Q`. | | | | `[AndElim i, L/R]` | From `P ∧ Q` (i), derive `P` (L) or `Q` (R). | | | Disjunction
| `[OrIntro i, L/R]` | From `P` (i), derive `P ∨ Q` (L) or `Q ∨ P` (R). | | | Negation | `[DNE i]` /
`[DNI i]` | Double Negation Elimination / Introduction. | | | | `[RAA i, j, k]` | Reductio Ad
Absurdum. | | | | `[Contradiction i, j]` | Derive any formula from a contradiction. | | |
Implication | `[ImplIntro i, j]` | Discharge assumption `P` (i) to conclude `P ⟹ Q` (j). | | | |
`[Vacuous i]` | From `¬P` (i), derive `P ⟹ Q`. | | | Biconditional | `[IffIntro i, j]` | From
`P ⟹ Q` (i) and `Q ⟹ P` (j), derive `P ⟺ Q`. | | | | `[IffElim i, L/R]` | From `P ⟺ Q` (i), derive
`P ⟹ Q` (L) or `Q ⟹ P` (R). | | | | `[IffMP i, j]` | From `P ⟺ Q` (i) and `P` (j), derive `Q`. | | |
| `[IffMT i, j]` | From `P ⟺ Q` (i) and `¬P` (j), derive `¬Q`. | | **Quantifier** | Universal |
`[UI i, t]` | Instantiation: `∀x φ(x)` (i) → `φ(t)`. | | | | `[UG i, x, ...]` | Generalization:
`φ(c)` (i) → `∀x φ(x)`. | | | Existential | `[ExistsIntro i, t, x]` | Introduction: `φ(t)` (i) →
`∃x φ(x)`. | | | | `[ExistsElim i, j, c]` | Elimination: `∃x φ(x)` (i) and `φ(c) ⟹ Q` (j) → `Q`. | |
**Equality** | Equality | `[EqIntro]` | Derive `t = t`. | | | | `[EqReplace i, j]` | Substitute one
occurrence of `t` with `s` using `t = s`. | | | | `[EqReplaceAll i, j]` | Substitute all occurrences
of `t` with `s`. | | **References** | Citation | `[Axiom Name, ...]` | Cite a global symbol. | | | |
`[Theorem Name, ...]` | Supports trailing terms for UI and integers for MP. | | | |
`[Constant Name, ...]` | UI is applied before MP. | | | | `[Operation Name, ...]` | | | | |
`[Schema Name, φ := F]` | Instantiation of a schema with formula `F`. | | **Definitions** |
Expansion | `[Def Name, i]` | Expand/contract named definition `Name` in line `i`. |

## Grammar & Operators

### Precedence (Lowest to Highest)

1. `⟺` (Biconditional)
2. `⟹` (Implication)
3. `∨` (Disjunction)
4. `∧` (Conjunction)
5. `¬` (Negation)
6. `∀x`, `∃x` (Quantifiers)
7. Atoms (Relations, Equality)

### Terminology & Atoms

- **Variables**: `A`, `x`, `y_1` (Must start with a letter).
- **Atoms**: `x = y`, `x ∈ A`.
- **Function Application**: `F(x, y)`.
- **Infix Relations**: `⊆`, `⊂`, `≈`, `≅`, `∼`, `≃`, `≤`, `≥`, `<`, `>`.
- **Infix Operations**: `∪`, `∩`, `∖`.
- **Set Enumeration**: `{x, y}`.
