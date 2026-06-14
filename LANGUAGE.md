# Aleph FOL Language Reference

Aleph uses a custom First-Order Logic (FOL) language parsed via Lark. This document describes the
syntax and structure of the `fol` blocks that the verifier processes.

## Top-Level Declarations

The language supports several top-level declarations that construct the mathematical foundation.

### Axioms

Axioms are fundamental truths accepted without proof.

```text
axiom Extensionality:
    ∀x ∀y (∀z (z ∈ x ⟺ z ∈ y) ⟹ x = y)
```

### Schemas

Axiom schemas are parameterized templates that can be instantiated with arbitrary formulas. They use
Greek letters for formula variables (`Φ`, `φ`, `ψ`, `χ`).

```text
schema Specification(φ(x)):
    ∀A ∃B ∀x (x ∈ B ⟺ (x ∈ A ∧ φ(x)))
```

### Definitions

Definitions act as macros and introduce new notation (symbols or predicates) as biconditionals. They
can be simple identifiers, infix relations, or predicates.

```text
// Infix definition
definition A ⊆ B:
    ∀x (x ∈ A ⟹ x ∈ B)

// Predicate definition
definition IsEmpty(A):
    ∀x ¬(x ∈ A)
```

### Constants & Operations

Constants and Operations are rigorously verified constructs that require both an existence and
uniqueness theorem to have been previously proven.

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

Theorems are statements followed by a rigorous, line-by-line proof. To visually mirror logical
scopes, proofs must use indentation (see [Proof Indentation Scoping](#proof-indentation-scoping)).

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

## Proof Syntax

Proofs are a sequence of numbered lines, each consisting of a statement and a justification in
brackets `[ ... ]`.

### Proof Indentation Scoping

Proof blocks enforce indentation rules matching the logical scope stack of variables and
assumptions. A linter pass in the verifier validates these indentation depths at parse time
(rejecting malformed proofs with a verification error):

1. **Base Indentation**: The first proof line starts at depth 1 (4 spaces).
2. **Indentation Step**: Each scope level increases indentation by 4 spaces.
3. **Scope Openers**:
   - `Let x1, ..., xN be arbitrary` opens **one** logical scope level. Lines inside this scope must
     be indented by 4 additional spaces.
   - `Assume P` opens **one** logical scope level. Lines inside this scope must be indented by 4
     additional spaces.
4. **Scope Closers**:
   - Rules that discharge assumptions (`ImplIntro`, `ExistsElim`) or generalize variables (`UG`)
     close their corresponding scopes.
   - The scope-closing line sits at the **parent scope depth** (matching the column of the opener),
     as the resulting conclusion belongs to the parent scope.

### Header and Body Indentation

To ensure consistency and readability across the book, top-level headers and declaration bodies must
also follow strict indentation rules:

1. **Declaration Headers**: Keywords that start a declaration (`axiom`, `theorem`, `definition`,
   `constant`, `operation`) and proof markers (`proof:`, `qed`, `existence:`, `uniqueness:`) must
   have **zero** indentation.
2. **Declaration Bodies**: Formulas that immediately follow a declaration header (the "claim") must
   have exactly **4 spaces** of indentation.

### Statements

A statement in a proof line can be:

- **Let Statement**: `Let x, y be arbitrary`
- **Assume Statement**: `Assume P(x)`
- **Formula**: Any valid FOL formula (e.g., `x ∈ A ⟹ x ∈ B`)

### Justifications

Every line must end with a justification tag. Justifications are parsed structurally at compile time
into typed AST nodes, validating the rule name and arguments (line references, terms, formulas, and
substitutions) upfront.

| Rule | Justification Tag | Description | | :--- | :--- | :--- | | Hypothesis | `[Hypothesis]` |
Introduces an assumption or declares arbitrary variables | | Modus Ponens | `[MP i, j]` | From
`P ⟹ Q` (line `i`) and `P` (line `j`), derive `Q` | | Modus Tollens | `[MT i, j]` | From `P ⟹ Q`
(line `i`) and `¬Q` (line `j`), derive `¬P` | | Disjunctive Syllogism | `[DS i, j]` | From `P ∨ Q`
(line `i`) and `¬P` (line `j`), derive `Q` | | Conjunction Introduction | `[AndIntro i, j]` | From
`P` (line `i`) and `Q` (line `j`), derive `P ∧ Q` | | Conjunction Elimination |
`[AndElim i, Left/Right]` | From `P ∧ Q` (line `i`), derive `P` (`Left`) or `Q` (`Right`) | |
Disjunction Introduction | `[OrIntro i, Left/Right]` | From `P` (line `i`), derive `P ∨ Q` (`Left`)
or `Q ∨ P` (`Right`) | | Double Negation Elimination| `[DNE i]` | From `¬¬P` (line `i`), derive `P`
| | Double Negation Introduction| `[DNI i]` | From `P` (line `i`), derive `¬¬P` | | Reductio Ad
Absurdum | `[RAA i, j, k]` | From `Assume ¬P` (line `i`) and contradiction (lines `j, k`), derive
`P` | | Vacuous Truth | `[Vacuous i]` | From `¬P` (line `i`), derive `P ⟹ Q` | | Universal
Instantiation | `[UI i, t]` | From `∀x φ(x)` (line `i`), derive `φ(t)` by substituting term `t` | |
Universal Generalization | `[UG i, x, ...]` | From `φ(c)` (line `i`) where variable `c` is
arbitrary, generalize to `∀x φ(x)` | | Existential Introduction | `[ExistsIntro i, t, x]` | From
`φ(t)` (line `i`), derive `∃x φ(x)` by replacing term `t` with bound variable `x` | | Existential
Elimination | `[ExistsElim i, j, c]` | From `∃x φ(x)` (line `i`) and `φ(c) ⟹ Q` (line `j`) with
arbitrary `c`, derive `Q` | | Implication Introduction | `[ImplIntro i, j]` | From assumption `P`
(line `i`) to conclusion `Q` (line `j`), derive `P ⟹ Q` | | Biconditional Introduction |
`[IffIntro i, j]` | From `P ⟹ Q` (line `i`) and `Q ⟹ P` (line `j`), derive `P ⟺ Q` | | Biconditional
Elimination | `[IffElim i, Left/Right]` | From `P ⟺ Q` (line `i`), derive `P ⟹ Q` (`Left`) or
`Q ⟹ P` (`Right`) | | Biconditional Modus Ponens | `[IffMP i, j]` | From `P ⟺ Q` (line `i`) and `P`
(line `j`), derive `Q` | | Biconditional Modus Tollens | `[IffMT i, j]` | From `P ⟺ Q` (line `i`)
and `¬P` (line `j`), derive `¬Q` | | Explosion (Contradiction) | `[Contradiction i, j]` | From `P`
(line `i`) and `¬P` (line `j`), derive any claimed formula | | Equality Introduction | `[EqIntro]` |
Derive `t = t` for any term `t` | | Equality Replacement | `[EqReplace i, j]` | From `φ` (line `i`)
and `t = s` (line `j`), derive `φ` with one `t` replaced by `s` | | Replace All Occurrences |
`[EqReplaceAll i, j]` | From `φ` (line `i`) and `t = s` (line `j`), derive `φ` with all `t` replaced
by `s` | | Definition Expansion | `[Def Name, i]` | Expand or contract a named definition `Name`
using line `i` (or the claimed formula) | | Axiom Reference | `[Axiom Name, t, i, ...]` | Cite axiom
`Name`, optionally applying UI (terms `t`) and MP (lines `i`) | | Theorem Reference |
`[Theorem Name, t, i, ...]` | Cite theorem `Name`, optionally applying UI (terms `t`) and MP (lines
`i`) | | Constant Reference | `[Constant Name, t, i, ...]` | Cite constant `Name`, optionally
applying UI (terms `t`) and MP (lines `i`) | | Operation Reference | `[Operation Name, t, i, ...]` |
Cite operation `Name`, optionally applying UI (terms `t`) and MP (lines `i`) | | Schema
Instantiation | `[Schema Name, φ := formula]` | Instantiate an axiom schema with a concrete formula
|

## Formulas and Operators

Formulas are built using standard logical connectives and quantifiers. The order of operations
(precedence from lowest to highest) is:

1. `⟺` (Biconditional)
2. `⟹` (Implication)
3. `∨` (Disjunction)
4. `∧` (Conjunction)
5. `¬` (Negation)
6. `∀x`, `∃x` (Quantifiers)
7. Atoms (Predicates, Relations, Equality)

### Atoms and Terms

- **Variables**: `A`, `x`, `y` (Must start with a letter, optionally followed by alphanumeric
  characters or underscores).
- **Equality**: `x = y`.
- **Membership**: `x ∈ A`.
- **Function Application**: `F(x, y)`.
- **Infix Relations**: Supported operators include `⊆`, `⊂`, `≈`, `≅`, `∼`, `≃`, `≤`, `≥`, `<`, `>`.
- **Infix Term Operations**: Supported operators include `∪`, `∩`, `∖`.
- **Set Enumeration**: `{x, y}`.

*Note: Use parentheses `( ... )` to explicitly group formulas or terms and override default
precedence.*
