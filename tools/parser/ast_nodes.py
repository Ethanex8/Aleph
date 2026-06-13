"""AST node definitions for Aleph's First-Order Logic.

Every node is a frozen dataclass, making ASTs immutable, hashable, and
structurally comparable via ``==``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Variable:
    """A variable or constant identifier, e.g. ``x``, ``A``, ``∅``.

    Variables must start with a letter and can contain alphanumeric characters or underscores.
    """

    name: str

    def __repr__(self) -> str:
        """Return the string representation of the variable/constant."""
        return self.name


@dataclass(frozen=True)
class FuncApp:
    """Function application over terms, e.g. ``f(x, y)``."""

    name: str
    args: tuple[Term, ...]

    def __repr__(self) -> str:
        """Return the prefix string representation of the function application."""
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.name}({args_str})"


@dataclass(frozen=True)
class InfixTerm:
    """Infix term operator, e.g. ``A ∪ B``, ``A ∩ B``, ``A ∖ B``.

    Used to combine two terms into a new term.
    """

    left: Term
    operator: str
    right: Term

    def __repr__(self) -> str:
        """Return the parenthesized infix string representation of the term operation."""
        return f"({self.left} {self.operator} {self.right})"


Term = Variable | FuncApp | InfixTerm


@dataclass(frozen=True)
class Predicate:
    """Predicate application over terms, e.g. ``P(x, y)`` or ``IsEmpty(A)``.

    Evaluates to a boolean formula.
    """

    name: str
    args: tuple[Term, ...]

    def __repr__(self) -> str:
        """Return the prefix string representation of the predicate application."""
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.name}({args_str})"


@dataclass(frozen=True)
class SchemaApp:
    """Schema variable application, e.g. ``φ(x)`` or ``ψ(x, y)``.

    Acts as a placeholder for an arbitrary formula during schema instantiation.
    """

    name: str
    args: tuple[Term, ...]

    def __repr__(self) -> str:
        """Return the prefix string representation of the schema variable application."""
        args_str = ", ".join(repr(a) for a in self.args)
        return f"{self.name}({args_str})"


@dataclass(frozen=True)
class Membership:
    """Set membership, ``t ∈ s``."""

    element: Term
    set_: Term

    def __repr__(self) -> str:
        """Return the membership string representation."""
        return f"({self.element} ∈ {self.set_})"


@dataclass(frozen=True)
class InfixPredicate:
    """Infix relation application, e.g. ``A ⊆ B``, ``x < y``.

    Operators can include ⊆, ⊂, ≈, ≅, ∼, ≃, ≤, ≥, <, >.
    """

    left: Term
    operator: str
    right: Term

    def __repr__(self) -> str:
        """Return the infix predicate representation."""
        return f"({self.left} {self.operator} {self.right})"


@dataclass(frozen=True)
class Equality:
    """Equality, ``t = s``."""

    left: Term
    right: Term

    def __repr__(self) -> str:
        """Return the equality formula representation."""
        return f"({self.left} = {self.right})"


@dataclass(frozen=True)
class Not:
    """Negation, ``¬φ``."""

    operand: Formula

    def __repr__(self) -> str:
        """Return the prefix negation formula representation."""
        return f"¬{self.operand}"


@dataclass(frozen=True)
class And:
    """Conjunction, ``φ ∧ ψ``."""

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        """Return the parenthesized conjunction representation."""
        return f"({self.left} ∧ {self.right})"


@dataclass(frozen=True)
class Or:
    """Disjunction, ``φ ∨ ψ``."""

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        """Return the parenthesized disjunction representation."""
        return f"({self.left} ∨ {self.right})"


@dataclass(frozen=True)
class Implies:
    """Implication, ``φ ⟹ ψ``."""

    antecedent: Formula
    consequent: Formula

    def __repr__(self) -> str:
        """Return the parenthesized implication representation."""
        return f"({self.antecedent} ⟹ {self.consequent})"


@dataclass(frozen=True)
class Biconditional:
    """Biconditional, ``φ ⟺ ψ``."""

    left: Formula
    right: Formula

    def __repr__(self) -> str:
        """Return the parenthesized biconditional representation."""
        return f"({self.left} ⟺ {self.right})"


@dataclass(frozen=True)
class ForAll:
    """Universal quantifier, ``∀x φ``. The variable is bound in the body."""

    variable: str
    body: Formula

    def __repr__(self) -> str:
        """Return the universal quantifier representation."""
        return f"∀{self.variable} {self.body}"


@dataclass(frozen=True)
class Exists:
    """Existential quantifier, ``∃x φ``. The variable is bound in the body."""

    variable: str
    body: Formula

    def __repr__(self) -> str:
        """Return the existential quantifier representation."""
        return f"∃{self.variable} {self.body}"


Formula = (
    Predicate
    | SchemaApp
    | Membership
    | InfixPredicate
    | Equality
    | Not
    | And
    | Or
    | Implies
    | Biconditional
    | ForAll
    | Exists
)

# Unified type for any AST node (formula or term). Used by the transformer
# and utility functions that operate on both levels of the AST.
Node = Formula | Term


@dataclass(frozen=True)
class AxiomDecl:
    """An axiom declaration (trusted fundamental truth, no proof required).

    e.g. ``axiom Extensionality: ...``.
    """

    name: str
    formula: Formula


@dataclass(frozen=True)
class SchemaParam:
    """A single schema parameter, e.g. ``φ(x)`` or ``φ(x, y)``."""

    name: str
    variables: tuple[str, ...]


@dataclass(frozen=True)
class SchemaDecl:
    """An axiom schema declaration parameterized by formula placeholders.

    e.g. ``schema Specification(φ(x)): ...``.
    """

    name: str
    params: tuple[SchemaParam, ...]
    formula: Formula


@dataclass(frozen=True)
class DefinitionDecl:
    """A definition / macro declaration.

    Used to introduce new notation (symbols, relations, or predicates) as biconditionals.
    """

    name: str
    formula: Formula


@dataclass(frozen=True)
class ConstantDecl:
    """A constant definition rigorously backed by existence and uniqueness proofs."""

    name: str
    formula: Formula
    existence_proof: str
    uniqueness_proof: str


@dataclass(frozen=True)
class OperationDecl:
    """An n-ary operation definition rigorously backed by existence and uniqueness proofs."""

    name: str
    params: tuple[str, ...]
    formula: Formula
    existence_proof: str
    uniqueness_proof: str


@dataclass(frozen=True)
class Justification:
    """A structured proof justification containing a rule name and arguments.

    Example:
        `[MP 1, 2]` has rule_name='MP' and args=(1, 2).
        `[UI 10, A]` has rule_name='UI' and args=(10, Variable('A')).
    """

    rule_name: str
    args: tuple[Term | Formula | int | str | tuple[str, Formula], ...]

    def __str__(self) -> str:
        """Serialize the justification into a human-readable string.

        Converts the rule name and arguments into the standard Aleph
        syntax for justifications (e.g., "MP 1, 2").
        """
        if not self.args:
            return self.rule_name

        arg_strs = []
        for arg in self.args:
            if isinstance(arg, tuple) and len(arg) == 2 and isinstance(arg[0], str):
                # schema subst: (variable, formula)
                arg_strs.append(f"{arg[0]} := {arg[1]}")
            else:
                arg_strs.append(str(arg))
        return f"{self.rule_name} {', '.join(arg_strs)}"

    def __repr__(self) -> str:
        """Return the serialized representation of the justification."""
        return str(self)


@dataclass(frozen=True)
class ProofLine:
    """A single numbered proof step within a theorem.

    A proof line consists of a line number, a claim (formula), and a
    justification. It can also be a structural line like 'Let' or 'Assume'.

    Attributes:
        number: The 1-based line number in the proof.
        formula: The logical formula derived or assumed at this step.
        justification: How this line was derived.
        is_let: True if this is a 'Let' statement introducing free variables.
        let_vars: The names of variables introduced in a 'Let' statement.
        is_assume: True if this is an 'Assume' statement opening an assumption.
    """

    number: int
    formula: Formula | None
    justification: Justification

    # Note: the formula field may be None for ``Let`` statements.
    is_let: bool = False
    let_vars: tuple[str, ...] = ()
    is_assume: bool = False
    depth: int = 1
    actual_indent: int = 0


@dataclass(frozen=True)
class TheoremDecl:
    """A theorem with its proof."""

    name: str
    formula: Formula
    proof_lines: tuple[ProofLine, ...]
