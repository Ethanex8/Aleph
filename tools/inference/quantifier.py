"""Inference rules for first-order quantifiers."""

from __future__ import annotations

from typing import cast

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.inference.core import _get_line_ref, inference_rule
from tools.parser.ast_nodes import (
    Exists,
    ForAll,
    Formula,
    FuncApp,
    Implies,
    InfixTerm,
    ProofLine,
    Variable,
)
from tools.parser.ast_utils import (
    get_free_vars,
    substitute,
    substitute_term,
    wrap_forall,
)


@inference_rule("UI")
def apply_universal_instantiation(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[UI i, t1, t2, ...] — Universal Instantiation.

    From ∀x1 ∀x2 ... φ(x1, x2, ...) (line i), derive φ(t1, t2, ...) by substituting terms.
    Supports multi-variable instantiation.
    """
    rule_args = line.justification.args
    if len(rule_args) < 2:
        raise VerificationError(
            f"UI requires a line reference and at least one term, got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    replacements = rule_args[1:]

    current_formula = ctx.get_line(line_i)

    for replacement in replacements:
        # Verify that the argument is a term node in the AST
        if not isinstance(replacement, (Variable, FuncApp, InfixTerm)):
            raise VerificationError(f"UI: expected term, got: {replacement}", line.number)

        # Formula must be universally quantified for each step
        if not isinstance(current_formula, ForAll):
            raise VerificationError(
                f"UI: formula is not a universal quantification: {current_formula}",
                line.number,
            )

        # Perform the term substitution
        current_formula = cast(
            Formula, substitute(current_formula.body, current_formula.variable, replacement)
        )

    return current_formula


@inference_rule("UG")
def apply_universal_generalization(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[UG i, x, y, ...] — Universal Generalization.

    From φ(c) where c is free (line i), derive ∀x φ(x).
    Supports multi-variable generalization: [UG i, A, B, C] produces
    ∀A ∀B ∀C φ.
    """
    rule_args = line.justification.args
    if len(rule_args) < 2:
        raise VerificationError(
            f"UG requires a line reference and variable name(s), got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    var_names = [str(a).strip() for a in rule_args[1:]]

    body = ctx.get_line(line_i)

    # Validate that targeted variables are in the current scope
    if set(var_names) != ctx.current_scope.free_vars:
        raise VerificationError(
            f"UG: variables {var_names} do not match the innermost active free variables {ctx.current_scope.free_vars}",
            line.number,
        )

    # Validate generalization constraint: var must not be free in any active assumptions in S.parent
    active_assumptions: list[int] = []
    curr = ctx.current_scope.parent
    while curr is not None:
        active_assumptions.extend(curr.assumptions)
        curr = curr.parent
    for var in var_names:
        for a_line in active_assumptions:
            a_formula = ctx.get_line(a_line)
            if var in get_free_vars(a_formula):
                raise VerificationError(
                    f"UG: variable '{var}' is free in active assumption at line {a_line}: '{a_formula}'",
                    line.number,
                )

    # Close the variable scope
    parent = ctx.current_scope.parent
    assert parent is not None
    ctx.current_scope = parent

    # Wrap in universal quantifiers (innermost first, outermost last)
    return wrap_forall(body, var_names)


@inference_rule("ExistsIntro")
def apply_exists_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[ExistsIntro i, t, x] — Existential Introduction.

    From φ(t) (line i), derive ∃x φ(x).

    Args:
        ctx: The proof context.
        line: The current proof line.
    """
    rule_args = line.justification.args
    if len(rule_args) != 3:
        raise VerificationError(
            f"ExistsIntro requires a line reference, a term name, and a bound variable name, got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    term_val = rule_args[1]
    var_name = str(rule_args[2]).strip()

    if not isinstance(term_val, (Variable, FuncApp, InfixTerm)):
        raise VerificationError(
            f"ExistsIntro: expected term as second argument, got: {term_val}", line.number
        )

    formula = ctx.get_line(line_i)
    bound_var = Variable(name=var_name)

    # Fallback/alternative check: if line.formula is provided and is an existential formula,
    # we can verify it by checking if substituting term_val for var_name in the existential's body yields the premise formula.
    if (
        line.formula is not None
        and isinstance(line.formula, Exists)
        and line.formula.variable == var_name
        and substitute(line.formula.body, var_name, term_val) == formula
    ):
        return line.formula

    # Substitute all occurrences of term_val in the formula with bound_var
    body = cast(Formula, substitute_term(formula, term_val, bound_var))
    return Exists(variable=var_name, body=body)


@inference_rule("ExistsElim")
def apply_exists_elim(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[ExistsElim i, j, c] — Existential Elimination.

    From ∃x φ(x) (line i) and (φ(c) ⟹ Q) (line j) where c is free, derive Q.
    Note: c must have been declared free and must not be free in Q or ∃x φ(x) or any active assumptions.
    """
    rule_args = line.justification.args
    if len(rule_args) != 3:
        raise VerificationError(
            f"ExistsElim requires 2 line references and a constant name, got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    line_j = _get_line_ref(rule_args[1])
    c_name = str(rule_args[2]).strip()

    formula_i = ctx.get_line(line_i)
    if not isinstance(formula_i, Exists):
        raise VerificationError(
            f"ExistsElim: line {line_i} is not an existential quantification", line.number
        )

    formula_j = ctx.get_line(line_j)
    if not isinstance(formula_j, Implies):
        raise VerificationError(
            f"ExistsElim: line {line_j} must be an implication (φ(c) ⟹ Q)", line.number
        )

    # Verify that the witness variable is the innermost active free variable (LIFO)
    if c_name not in ctx.current_scope.free_vars:
        raise VerificationError(
            f"ExistsElim: witness variable '{c_name}' is not the innermost active free variable",
            line.number,
        )

    scope_parent = ctx.current_scope.parent

    # Perform witness leakage and freshness checks
    if c_name in get_free_vars(formula_j.consequent):
        raise VerificationError(
            f"ExistsElim: witness variable '{c_name}' cannot be free in the conclusion: {formula_j.consequent}",
            line.number,
        )
    # 2. c must not be free in the existential formula (line i)
    if c_name in get_free_vars(formula_i):
        raise VerificationError(
            f"ExistsElim: witness variable '{c_name}' cannot be free in the existential formula: {formula_i}",
            line.number,
        )
    # 3. c must not be free in any active assumptions in scope_parent and its ancestors
    active_assumptions: list[int] = []
    curr = scope_parent
    while curr is not None:
        active_assumptions.extend(curr.assumptions)
        curr = curr.parent

    for a_line in active_assumptions:
        a_formula = ctx.get_line(a_line)
        if c_name in get_free_vars(a_formula):
            raise VerificationError(
                f"ExistsElim: witness variable '{c_name}' is free in active assumption at line {a_line}: '{a_formula}'",
                line.number,
            )

    # Close scope S
    assert scope_parent is not None
    ctx.current_scope = scope_parent

    # Reconstruct φ(c) from ∃x φ(x) by substituting c for bound variable x
    phi_c = substitute(formula_i.body, formula_i.variable, Variable(name=c_name))

    # Implication's antecedent must exactly match phi(c)
    if formula_j.antecedent != phi_c:
        raise VerificationError(
            f"ExistsElim: implication antecedent {formula_j.antecedent} does not match instantiated existential {phi_c}",
            line.number,
        )

    return formula_j.consequent
