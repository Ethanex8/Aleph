"""Inference rules for definitions, constants, and operations."""

from __future__ import annotations

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.inference.core import _get_line_ref, inference_rule
from tools.inference.references import _apply_bindings, _try_match
from tools.parser.ast_nodes import (
    Biconditional,
    Equality,
    Formula,
    Node,
    ProofLine,
)
from tools.parser.ast_utils import unwrap_forall


@inference_rule("Def")
def apply_definition(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Def Name, i] — Definition Expansion / Contraction.

    Expands or contracts a definition one layer deep. The definition must
    be a biconditional ∀...∀(LHS ⟺ RHS). This rule matches the claimed_formula
    formula against the definition, verifying the expansion/contraction.

    If a line reference is given, the input formula is taken from that line.
    The rule verifies the claimed_formula formula is a valid expansion or contraction
    of the input using the named definition.
    """
    rule_args = line.justification.args
    step_number = line.number
    assert line.formula is not None
    claimed_formula = line.formula

    if len(rule_args) < 1:
        raise VerificationError(
            f"Def requires at least a definition name, got {rule_args}", step_number
        )

    def_name = str(rule_args[0]).strip()
    source_line = _get_line_ref(rule_args[1]) if len(rule_args) > 1 else None

    # Retrieve definition/operation/constant from context
    defn = (
        ctx.definitions.get(def_name) or ctx.operations.get(def_name) or ctx.constants.get(def_name)
    )

    if defn is None:
        raise VerificationError(
            f"Def: unknown definition, operation, or constant '{def_name}'", step_number
        )

    source = ctx.get_line(source_line) if source_line is not None else None

    # Unwrap universal quantifiers from the definition to get the underlying biconditional
    def_body, def_vars = unwrap_forall(defn)

    # Check definition format
    if isinstance(def_body, (Biconditional, Equality)):
        lhs_template = def_body.left
        rhs_template = def_body.right
    else:
        raise VerificationError(
            f"Def: definition '{def_name}' is not a biconditional or equality", step_number
        )

    # Dispatch based on whether a premise line reference was supplied
    if source is not None and source_line is not None:
        return _apply_definition_with_source(
            def_name,
            source_line,
            source,
            claimed_formula,
            lhs_template,
            rhs_template,
            def_vars,
            step_number,
        )
    else:
        return _apply_definition_without_source(
            def_name, claimed_formula, def_body, def_vars, step_number
        )


def _apply_definition_with_source(
    def_name: str,
    source_line: int,
    source: Formula,
    claimed_formula: Formula,
    lhs_template: Node,
    rhs_template: Node,
    def_vars: list[str],
    step_number: int,
) -> Formula:
    """Apply a definition where an input source line is specified.

    Matches the source line against either the LHS or RHS template,
    applies the resulting bindings to the opposite side template, and
    verifies that it produces the claimed formula.
    """
    # Try to find variable bindings by matching source against LHS
    bindings = _try_match(lhs_template, source, def_vars)
    if bindings is not None:
        # Source matches LHS → claimed_formula should match RHS with same bindings
        expected = _apply_bindings(rhs_template, bindings)
        if expected == claimed_formula:
            return claimed_formula

    # Try matching source against RHS
    bindings = _try_match(rhs_template, source, def_vars)
    if bindings is not None:
        # Source matches RHS → claimed_formula should match LHS with same bindings
        expected = _apply_bindings(lhs_template, bindings)
        if expected == claimed_formula:
            return claimed_formula

    raise VerificationError(
        f"Def: cannot match line {source_line} against definition "
        f"'{def_name}' to produce the claimed_formula formula",
        step_number,
    )


def _apply_definition_without_source(
    def_name: str,
    claimed_formula: Formula,
    def_body: Formula,
    def_vars: list[str],
    step_number: int,
) -> Formula:
    """Apply a definition without a source line specified.

    Matches the claimed formula against the definition body (e.g. LHS ⟺ RHS or LHS = RHS)
    to verify it is a valid instantiation of the definition.
    """
    bindings = _try_match(def_body, claimed_formula, def_vars)
    if bindings is not None:
        return claimed_formula
    raise VerificationError(
        f"Def: claimed_formula formula does not match definition '{def_name}'",
        step_number,
    )
