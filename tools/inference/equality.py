from __future__ import annotations

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.inference.core import extract_line_refs, inference_rule
from tools.parser.ast_nodes import (
    Equality,
    Formula,
    ProofLine,
)
from tools.parser.ast_utils import substitute_equality, substitute_term


@inference_rule("EqReplace")
def apply_eq_replace(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """
    [EqReplace i, j] — Equality Replacement.

    From φ (line i) and t = s (line j), derive φ' where one occurrence
    of t has been replaced by s (or s by t).
    """
    assert line.formula is not None
    claimed_formula = line.formula

    line_i, line_j = extract_line_refs("EqReplace", line.justification.args, 2, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Referenced premise j must be an equality (t = s)
    if not isinstance(formula_j, Equality):
        raise VerificationError(f"EqReplace: line {line_j} must be an equality", line.number)

    # Try replacing t with s (left to right replacement)
    if substitute_equality(formula_i, formula_j.left, formula_j.right, claimed_formula):
        return claimed_formula

    # Try replacing s with t (right to left replacement)
    if substitute_equality(formula_i, formula_j.right, formula_j.left, claimed_formula):
        return claimed_formula

    raise VerificationError(
        f"EqReplace: claimed_formula formula is not a valid replacement of {formula_j} in line {line_i}",
        line.number,
    )


@inference_rule("EqReplaceAll")
def apply_eq_replace_all(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """
    [EqReplaceAll i, j] — Equality Replacement (All Occurrences).

    From φ (line i) and t = s (line j), derive φ' where ALL occurrences
    of t have been replaced by s (or s by t).
    """
    assert line.formula is not None
    claimed_formula = line.formula

    line_i, line_j = extract_line_refs("EqReplaceAll", line.justification.args, 2, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Referenced premise j must be an equality (t = s)
    if not isinstance(formula_j, Equality):
        raise VerificationError(f"EqReplaceAll: line {line_j} must be an equality", line.number)

    # Try replacing t with s
    if substitute_term(formula_i, formula_j.left, formula_j.right) == claimed_formula:
        return claimed_formula

    # Try replacing s with t
    if substitute_term(formula_i, formula_j.right, formula_j.left) == claimed_formula:
        return claimed_formula

    raise VerificationError(
        f"EqReplaceAll: claimed_formula formula is not a valid 'replace-all' of {formula_j} in line {line_i}",
        line.number,
    )


@inference_rule("EqIntro")
def apply_eq_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """
    [EqIntro] — Equality Introduction (Reflexivity).

    Derive t = t for any term t.
    """
    rule_args = line.justification.args
    assert line.formula is not None
    claimed_formula = line.formula

    if len(rule_args) != 0:
        raise VerificationError(f"EqIntro requires no arguments, got {rule_args}", line.number)

    # Claimed formula must be an equality of the form t = t
    if not isinstance(claimed_formula, Equality) or claimed_formula.left != claimed_formula.right:
        raise VerificationError(
            f"EqIntro: claimed formula must be of the form t = t, got {claimed_formula}",
            line.number,
        )

    return claimed_formula
