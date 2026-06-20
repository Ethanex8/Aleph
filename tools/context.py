"""Proof Context — tracks all state during verification.

Maintain axioms, schemas, definitions, proven theorems, and per-proof
state (hypotheses, proof lines, free variables).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.parser.ast_nodes import (
    Formula,
    SchemaDecl,
)


class VerificationError(Exception):
    """Raised when a proof step fails verification."""

    def __init__(self, message: str, line_number: int | None = None):
        """Initialize VerificationError."""
        self.line_number = line_number
        if line_number is not None:
            message = f"Line {line_number}: {message}"
        super().__init__(message)


@dataclass
class Scope:
    """Represents a proof scope containing its own variables and assumptions."""

    id: int  # Line number that started the scope, or 0 for root
    parent: Scope | None = None
    free_vars: set[str] = field(default_factory=set)
    assumptions: set[int] = field(default_factory=set)
    derived_lines: set[int] = field(default_factory=set)

    @property
    def depth(self) -> int:
        """Return the depth of this scope (root scope has depth 1)."""
        d = 1
        curr = self.parent
        while curr is not None:
            d += 1
            curr = curr.parent
        return d

    def is_ancestor_of(self, other: Scope) -> bool:
        """Check if this scope is an ancestor of (or equal to) the other scope."""
        curr: Scope | None = other
        while curr is not None:
            if curr is self:
                return True
            curr = curr.parent
        return False


@dataclass
class ProofContext:
    """Central state object threaded through verification.

    Global state (persists across files):
        - axioms, schemas, definitions, proven_theorems, imports

    Per-proof state (reset for each theorem):
        - hypotheses, proof_lines, free_vars, assumptions
    """

    axioms: dict[str, Formula] = field(default_factory=dict)
    schemas: dict[str, SchemaDecl] = field(default_factory=dict)
    definitions: dict[str, Formula] = field(default_factory=dict)
    symbols: dict[str, Formula] = field(default_factory=dict)
    proven_theorems: dict[str, Formula] = field(default_factory=dict)

    proof_lines: dict[int, Formula] = field(default_factory=dict)
    free_vars: set[str] = field(default_factory=set)
    assumptions: dict[int, Formula] = field(default_factory=dict)

    root_scope: Scope = field(default_factory=lambda: Scope(id=0))
    current_scope: Scope = field(init=False)
    line_to_scope: dict[int, Scope] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize current_scope to root_scope."""
        self.current_scope = self.root_scope

    def reset_proof(self) -> None:
        """Reset per-proof state for a new theorem."""
        self.proof_lines.clear()
        self.free_vars.clear()
        self.assumptions.clear()
        self.root_scope = Scope(id=0)
        self.current_scope = self.root_scope
        self.line_to_scope.clear()

    def register_axiom(self, name: str, formula: Formula) -> None:
        """Register a new axiom. Raises VerificationError if the name is already used."""
        if name in self.axioms:
            raise VerificationError(f"Duplicate axiom: {name}")
        self.axioms[name] = formula

    def register_schema(self, schema: SchemaDecl) -> None:
        """Register a new schema. Raises VerificationError if the name is already used."""
        if schema.name in self.schemas:
            raise VerificationError(f"Duplicate schema: {schema.name}")
        self.schemas[schema.name] = schema

    def register_definition(self, name: str, formula: Formula) -> None:
        """Register a new definition. Raises VerificationError if the name is already used."""
        if name in {"=", "∈"}:
            raise VerificationError(f"Cannot redefine primitive symbol: {name}")
        if name in self.definitions:
            raise VerificationError(f"Duplicate definition: {name}")
        self.definitions[name] = formula

    def register_symbol(self, name: str, formula: Formula) -> None:
        """Register a new symbol definition. Raises VerificationError if the name is already used."""
        if name in {"=", "∈"}:
            raise VerificationError(f"Cannot redefine primitive symbol: {name}")
        if name in self.symbols:
            raise VerificationError(f"Duplicate symbol: {name}")
        self.symbols[name] = formula

    def register_theorem(self, name: str, formula: Formula) -> None:
        """Register a proven theorem. Raises VerificationError if the name is already used."""
        if name in self.proven_theorems:
            raise VerificationError(f"Duplicate theorem: {name}")
        self.proven_theorems[name] = formula

    def get_line(self, line_num: int) -> Formula:
        """Retrieve a previously established proof line. Raises VerificationError if the line number is invalid."""
        if line_num not in self.proof_lines:
            raise VerificationError(f"Reference to unestablished line {line_num}")
        return self.proof_lines[line_num]
