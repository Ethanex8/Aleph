"""Inference rules for propositional logic."""
from __future__ import annotations

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.inference.core import _get_line_ref, extract_line_refs, inference_rule
from tools.parser.ast_nodes import (
    And,
    Biconditional,
    Formula,
    Implies,
    Not,
    Or,
    ProofLine,
)


@inference_rule("Hypothesis")
def apply_hypothesis(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula | None:
    """[Hypothesis] — introduces an assumption or declares free variables.

    For ``Let X, Y be arbitrary``: registers variables as free.
    For ``Assume P``: registers P as an assumption.
    """
    if line.is_let:
        # Bind variables as free for later generalizations or exists-elim
        for var in line.let_vars:
            ctx.free_vars.add(var)
        return None  # Let statements don't produce a formula
    elif line.is_assume:
        assert line.formula is not None
        # Register formula as an active assumption in the context
        ctx.assumptions[line.number] = line.formula
        return line.formula
    else:
        assert line.formula is not None
        # Direct hypothesis — the formula itself is assumed
        ctx.assumptions[line.number] = line.formula
        return line.formula


@inference_rule("MP")
def apply_modus_ponens(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[MP i, j] — Modus Ponens.

    Derive the consequent of an implication given the implication itself
    and its antecedent.

    Example:
        `1. P ⟹ Q  [Axiom ...]`
        `2. P      [Axiom ...]`
        `3. Q      [MP 1, 2]`
    """
    line_i, line_j = extract_line_refs("MP", line.justification.args, 2, line.number)
    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Try order: line_i is implication (P => Q), line_j is antecedent (P)
    if isinstance(formula_i, Implies) and formula_i.antecedent == formula_j:
        return formula_i.consequent
    # Try order: line_j is implication (P => Q), line_i is antecedent (P)
    if isinstance(formula_j, Implies) and formula_j.antecedent == formula_i:
        return formula_j.consequent

    raise VerificationError(
        f"MP failed: line {line_i} and line {line_j} do not form a valid "
        f"Modus Ponens pair. Need P ⟹ Q and P.",
        line.number,
    )


@inference_rule("AndIntro")
def apply_and_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[AndIntro i, j] — Conjunction Introduction.

    From P (line i) and Q (line j), derive P ∧ Q.
    """
    line_i, line_j = extract_line_refs("AndIntro", line.justification.args, 2, line.number)
    # Combine the formulas from both lines into a conjunction
    return And(left=ctx.get_line(line_i), right=ctx.get_line(line_j))


@inference_rule("AndElim")
def apply_and_elim(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[AndElim i, Left|Right] — Conjunction Elimination.

    From P ∧ Q (line i), derive P (Left) or Q (Right).
    """
    rule_args = line.justification.args
    if len(rule_args) != 2:
        raise VerificationError(
            f"AndElim requires a line reference and Left/Right, got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    side = str(rule_args[1]).strip()
    formula = ctx.get_line(line_i)

    # Check that referenced line is actually an And node
    if not isinstance(formula, And):
        raise VerificationError(
            f"AndElim: line {line_i} is not a conjunction: {formula}", line.number
        )

    # Extract requested conjunct
    if side == "Left":
        return formula.left
    elif side == "Right":
        return formula.right
    else:
        raise VerificationError(f"AndElim: expected 'Left' or 'Right', got '{side}'", line.number)


@inference_rule("OrIntro")
def apply_or_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[OrIntro i, Left|Right] — Disjunction Introduction.

    From P (line i), derive P ∨ Q (Left) or Q ∨ P (Right).
    The other disjunct is taken from the claimed_formula formula.
    """
    rule_args = line.justification.args
    claimed_formula = line.formula
    if len(rule_args) != 2:
        raise VerificationError(
            f"OrIntro requires a line reference and Left/Right, got {rule_args}",
            line.number,
        )

    line_i = _get_line_ref(rule_args[0])
    side = str(rule_args[1]).strip()
    formula = ctx.get_line(line_i)

    # The goal formula must be a disjunction
    if not isinstance(claimed_formula, Or):
        raise VerificationError(
            "OrIntro: claimed_formula formula is not a disjunction", line.number
        )

    # Match the side: Left means formula i is LHS, Right means formula i is RHS
    if (side == "Left" and claimed_formula.left == formula) or (
        side == "Right" and claimed_formula.right == formula
    ):
        return claimed_formula
    else:
        raise VerificationError(
            f"OrIntro: line {line_i} does not match the '{side}' side of the claimed_formula disjunction",
            line.number,
        )


@inference_rule("ImplIntro")
def apply_impl_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[ImplIntro i, j] — Implication Introduction.

    From assumption P (line i) and derived Q (line j), derive P ⟹ Q.
    Line i must be an assumption.
    """
    line_i, line_j = extract_line_refs("ImplIntro", line.justification.args, 2, line.number)

    # Enforce LIFO: the discharged assumption must be the innermost active assumption
    if ctx.current_scope.id != line_i or line_i not in ctx.current_scope.assumptions:
        raise VerificationError(
            f"ImplIntro: line {line_i} is not the innermost active assumption",
            line.number,
        )

    # Close the scope
    parent = ctx.current_scope.parent
    assert parent is not None
    ctx.current_scope = parent

    # Retrieve antecedent from assumption and consequent from derivation
    antecedent = ctx.get_line(line_i)
    consequent = ctx.get_line(line_j)

    return Implies(antecedent=antecedent, consequent=consequent)


@inference_rule("IffIntro")
def apply_iff_intro(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[IffIntro i, j] — Biconditional Introduction.

    From P ⟹ Q (line i) and Q ⟹ P (line j), derive P ⟺ Q.
    """
    line_i, line_j = extract_line_refs("IffIntro", line.justification.args, 2, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Both premise lines must be implication nodes
    if not isinstance(formula_i, Implies) or not isinstance(formula_j, Implies):
        raise VerificationError("IffIntro: both lines must be implications", line.number)

    # Verify cross-matching: i = P => Q and j = Q => P
    if (
        formula_i.antecedent == formula_j.consequent
        and formula_i.consequent == formula_j.antecedent
    ):
        return Biconditional(left=formula_i.antecedent, right=formula_i.consequent)

    raise VerificationError("IffIntro: implications do not match P ⟹ Q and Q ⟹ P", line.number)


@inference_rule("IffElim")
def apply_iff_elim(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[IffElim i, Left|Right] — Biconditional Elimination.

    From P ⟺ Q (line i), derive P ⟹ Q (Left) or Q ⟹ P (Right).
    """
    rule_args = line.justification.args
    if len(rule_args) != 2:
        raise VerificationError(
            f"IffElim requires a line reference and Left/Right, got {rule_args}", line.number
        )

    line_i = _get_line_ref(rule_args[0])
    side = str(rule_args[1]).strip()

    formula = ctx.get_line(line_i)
    if not isinstance(formula, Biconditional):
        raise VerificationError(f"IffElim: line {line_i} is not a biconditional", line.number)

    # Left gets P => Q, Right gets Q => P
    if side == "Left":
        return Implies(antecedent=formula.left, consequent=formula.right)
    elif side == "Right":
        return Implies(antecedent=formula.right, consequent=formula.left)
    else:
        raise VerificationError(f"IffElim: expected 'Left' or 'Right', got '{side}'", line.number)


@inference_rule("Contradiction")
def apply_contradiction(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Contradiction i, j] — Explosion / Ex Falso Quodlibet.

    From P (line i) and ¬P (line j), derive any formula.
    """
    line_i, line_j = extract_line_refs("Contradiction", line.justification.args, 2, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Check if one formula is the negation of the other (order-flexible)
    if (isinstance(formula_j, Not) and formula_j.operand == formula_i) or (
        isinstance(formula_i, Not) and formula_i.operand == formula_j
    ):
        assert line.formula is not None
        return line.formula

    raise VerificationError(
        f"Contradiction: lines {line_i} and {line_j} are not P and ¬P", line.number
    )


@inference_rule("OrElim")
def apply_or_elim(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[OrElim i, j, k] — Disjunction Elimination.

    From P ∨ Q (line i), P ⟹ R (line j), and Q ⟹ R (line k), derive R.
    """
    line_i, line_j, line_k = extract_line_refs("OrElim", line.justification.args, 3, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)
    formula_k = ctx.get_line(line_k)

    if not isinstance(formula_i, Or):
        raise VerificationError(f"OrElim: line {line_i} is not a disjunction", line.number)
    if not isinstance(formula_j, Implies):
        raise VerificationError(f"OrElim: line {line_j} is not an implication", line.number)
    if not isinstance(formula_k, Implies):
        raise VerificationError(f"OrElim: line {line_k} is not an implication", line.number)

    if formula_i.left != formula_j.antecedent:
        raise VerificationError(
            f"OrElim: implication {line_j} antecedent does not match left disjunct", line.number
        )
    if formula_i.right != formula_k.antecedent:
        raise VerificationError(
            f"OrElim: implication {line_k} antecedent does not match right disjunct", line.number
        )
    if formula_j.consequent != formula_k.consequent:
        raise VerificationError(
            "OrElim: implications do not share the same consequent", line.number
        )

    return formula_j.consequent


@inference_rule("OrIdem")
def apply_or_idem(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[OrIdem i] — Disjunction Idempotency.

    From P ∨ P (line i), derive P.
    """
    (line_i,) = extract_line_refs("OrIdem", line.justification.args, 1, line.number)
    formula_i = ctx.get_line(line_i)

    if not isinstance(formula_i, Or) or formula_i.left != formula_i.right:
        raise VerificationError(
            f"OrIdem: line {line_i} is not a disjunction of identical formulas: {formula_i}",
            line.number,
        )

    return formula_i.left


@inference_rule("MT")
def apply_modus_tollens(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[MT i, j] — Modus Tollens.

    From P ⟹ Q (line i) and ¬Q (line j), derive ¬P.
    """
    line_i, line_j = extract_line_refs("MT", line.justification.args, 2, line.number)
    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Try order: i is P => Q, j is ~Q
    if (
        isinstance(formula_i, Implies)
        and isinstance(formula_j, Not)
        and formula_i.consequent == formula_j.operand
    ):
        return Not(operand=formula_i.antecedent)
    # Try order: j is P => Q, i is ~Q
    if (
        isinstance(formula_j, Implies)
        and isinstance(formula_i, Not)
        and formula_j.consequent == formula_i.operand
    ):
        return Not(operand=formula_j.antecedent)

    raise VerificationError(
        f"MT failed: lines {line_i} and {line_j} do not form a Modus Tollens pair.",
        line.number,
    )


@inference_rule("DS")
def apply_disjunctive_syllogism(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[DS i, j] — Disjunctive Syllogism.

    From P ∨ Q (line i) and ¬P (line j), derive Q.
    (Or from P ∨ Q and ¬Q, derive P).
    """
    line_i, line_j = extract_line_refs("DS", line.justification.args, 2, line.number)
    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Find which one is the disjunction
    disj, neg = (formula_i, formula_j) if isinstance(formula_i, Or) else (formula_j, formula_i)

    if isinstance(disj, Or) and isinstance(neg, Not):
        if disj.left == neg.operand:
            return disj.right
        if disj.right == neg.operand:
            return disj.left

    raise VerificationError(
        f"DS failed: lines {line_i} and {line_j} do not form a Disjunctive Syllogism pair.",
        line.number,
    )


@inference_rule("DNE")
def apply_double_negation_elimination(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[DNE i] — Double Negation Elimination.

    From ¬¬P (line i), derive P.
    """
    (line_i,) = extract_line_refs("DNE", line.justification.args, 1, line.number)
    formula = ctx.get_line(line_i)

    if isinstance(formula, Not) and isinstance(formula.operand, Not):
        return formula.operand.operand

    raise VerificationError(
        f"DNE failed: line {line_i} is not a double negation.",
        line.number,
    )


@inference_rule("DNI")
def apply_double_negation_introduction(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[DNI i] — Double Negation Introduction.

    From P (line i), derive ¬¬P.
    """
    (line_i,) = extract_line_refs("DNI", line.justification.args, 1, line.number)
    formula = ctx.get_line(line_i)

    return Not(operand=Not(operand=formula))


@inference_rule("RAA")
def apply_reductio_ad_absurdum(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[RAA i, j, k] — Reductio Ad Absurdum (Proof by Contradiction).

    From assumption ¬P (line i) and contradiction Q, ¬Q (lines j, k),
    derive P.
    Also supports assuming P to derive ¬P.
    """
    line_i, line_j, line_k = extract_line_refs("RAA", line.justification.args, 3, line.number)

    # Enforce LIFO: the discharged assumption must be the innermost active assumption
    if ctx.current_scope.id != line_i or line_i not in ctx.current_scope.assumptions:
        raise VerificationError(
            f"RAA: line {line_i} is not the innermost active assumption",
            line.number,
        )

    formula_j = ctx.get_line(line_j)
    formula_k = ctx.get_line(line_k)

    # Check for contradiction
    if not (
        (isinstance(formula_k, Not) and formula_k.operand == formula_j)
        or (isinstance(formula_j, Not) and formula_j.operand == formula_k)
    ):
        raise VerificationError(
            f"RAA: lines {line_j} and {line_k} do not form a contradiction.",
            line.number,
        )

    # Close the scope
    parent = ctx.current_scope.parent
    assert parent is not None
    ctx.current_scope = parent

    # Retrieve the assumption formula
    assumption = ctx.get_line(line_i)

    # If assumption was ¬P, return P. If it was P, return ¬P.
    if isinstance(assumption, Not):
        return assumption.operand
    else:
        return Not(operand=assumption)


@inference_rule("Vacuous")
def apply_vacuous_truth(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Vacuous i] — Vacuous Truth.

    From ¬P (line i), derive P ⟹ Q for any Q.
    Q is taken from the claimed formula.
    """
    (line_i,) = extract_line_refs("Vacuous", line.justification.args, 1, line.number)
    formula_i = ctx.get_line(line_i)
    claimed = line.formula

    if not isinstance(claimed, Implies):
        raise VerificationError(
            "Vacuous: claimed formula must be an implication.",
            line.number,
        )

    if isinstance(formula_i, Not) and formula_i.operand == claimed.antecedent:
        return claimed

    raise VerificationError(
        f"Vacuous: line {line_i} is not the negation of the antecedent of {claimed}",
        line.number,
    )


@inference_rule("IffMP")
def apply_iff_modus_ponens(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[IffMP i, j] — Biconditional Modus Ponens.

    From P ⟺ Q (line i) and P (line j), derive Q.
    (Or from P ⟺ Q and Q, derive P).
    """
    line_i, line_j = extract_line_refs("IffMP", line.justification.args, 2, line.number)
    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Find which one is the biconditional
    iff, prem = (
        (formula_i, formula_j) if isinstance(formula_i, Biconditional) else (formula_j, formula_i)
    )

    if isinstance(iff, Biconditional):
        if iff.left == prem:
            return iff.right
        if iff.right == prem:
            return iff.left

    raise VerificationError(
        f"IffMP: lines {line_i} and {line_j} do not form an IffMP pair.",
        line.number,
    )


@inference_rule("IffMT")
def apply_iff_modus_tollens(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[IffMT i, j] — Biconditional Modus Tollens.

    From P ⟺ Q (line i) and ¬P (line j), derive ¬Q.
    (Or from P ⟺ Q and ¬Q, derive ¬P).
    """
    line_i, line_j = extract_line_refs("IffMT", line.justification.args, 2, line.number)
    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    # Find which one is the biconditional
    iff, neg = (
        (formula_i, formula_j) if isinstance(formula_i, Biconditional) else (formula_j, formula_i)
    )

    if isinstance(iff, Biconditional) and isinstance(neg, Not):
        if iff.left == neg.operand:
            return Not(operand=iff.right)
        if iff.right == neg.operand:
            return Not(operand=iff.left)

    raise VerificationError(
        f"IffMT: lines {line_i} and {line_j} do not form an IffMT pair.",
        line.number,
    )


@inference_rule("IffTrans")
def apply_iff_trans(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[IffTrans i, j] — Transitivity and symmetry of biconditional.

    From P ⟺ Q (line i) and Q ⟺ R (line j) [or any symmetric variant],
    derive P ⟺ R (or R ⟺ P).
    """
    line_i, line_j = extract_line_refs("IffTrans", line.justification.args, 2, line.number)

    formula_i = ctx.get_line(line_i)
    formula_j = ctx.get_line(line_j)

    if not isinstance(formula_i, Biconditional) or not isinstance(formula_j, Biconditional):
        raise VerificationError("IffTrans: both lines must be biconditionals", line.number)

    claimed_formula = line.formula
    if not isinstance(claimed_formula, Biconditional):
        raise VerificationError("IffTrans: claimed formula must be a biconditional", line.number)

    A, B = formula_i.left, formula_i.right
    C, D = formula_j.left, formula_j.right

    # Check all 4 match possibilities for sharing a side and matching the claimed formula:
    # 1. A == C -> B ⟺ D
    if A == C and (
        (claimed_formula.left == B and claimed_formula.right == D)
        or (claimed_formula.left == D and claimed_formula.right == B)
    ):
        return claimed_formula
    # 2. A == D -> B ⟺ C
    if A == D and (
        (claimed_formula.left == B and claimed_formula.right == C)
        or (claimed_formula.left == C and claimed_formula.right == B)
    ):
        return claimed_formula
    # 3. B == C -> A ⟺ D
    if B == C and (
        (claimed_formula.left == A and claimed_formula.right == D)
        or (claimed_formula.left == D and claimed_formula.right == A)
    ):
        return claimed_formula
    # 4. B == D -> A ⟺ C
    if B == D and (
        (claimed_formula.left == A and claimed_formula.right == C)
        or (claimed_formula.left == C and claimed_formula.right == B)
    ):
        return claimed_formula

    raise VerificationError(
        f"IffTrans: cannot derive {claimed_formula} from {formula_i} and {formula_j}", line.number
    )


@inference_rule("OrCases")
def apply_or_cases(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[OrCases i, j, k] — Disjunction Elimination via nested case subproofs.

    From P ∨ Q (line i), Case 1 ending at line j (assuming P), and Case 2 ending at line k (assuming Q),
    derive R (the common conclusion of both cases, which must match the claimed formula of this line).
    """
    line_i, line_j, line_k = extract_line_refs("OrCases", line.justification.args, 3, line.number)

    disjunction = ctx.get_line(line_i)
    if not isinstance(disjunction, Or):
        raise VerificationError(
            f"OrCases: line {line_i} is not a disjunction: {disjunction}",
            line.number,
        )

    # Check the scopes:
    # Under sibling scopes, Case 1 and Case 2 are sibling scopes sharing the same parent scope.
    case2_scope = ctx.line_to_scope.get(line_k)
    case1_scope = ctx.line_to_scope.get(line_j)

    if case2_scope is None:
        raise VerificationError(
            f"OrCases: Case 2 conclusion line {line_k} has no associated scope",
            line.number,
        )

    if case1_scope is None:
        raise VerificationError(
            f"OrCases: Case 1 conclusion line {line_j} has no associated scope",
            line.number,
        )

    if (
        case2_scope.parent is None
        or case1_scope.parent != case2_scope.parent
        or case2_scope.parent != ctx.current_scope.parent
    ):
        raise VerificationError(
            "OrCases: Case 1 and Case 2 must be sibling scopes sharing the same parent scope",
            line.number,
        )

    # Verify that the scopes correspond to the expected lines
    if ctx.line_to_scope.get(line_k) != case2_scope:
        raise VerificationError(
            f"OrCases: Case 2 conclusion line {line_k} is not in the innermost scope",
            line.number,
        )
    if ctx.line_to_scope.get(line_j) != case1_scope:
        raise VerificationError(
            f"OrCases: Case 1 conclusion line {line_j} is not in the Case 1 scope",
            line.number,
        )

    # Verify assumptions of the two scopes
    # Case 2 assumption (right disjunct Q)
    if case2_scope.id not in ctx.assumptions:
        raise VerificationError(
            "OrCases: Case 2 scope was not opened by an assumption",
            line.number,
        )
    q_assumed = ctx.assumptions[case2_scope.id]

    # Case 1 assumption (left disjunct P)
    if case1_scope.id not in ctx.assumptions:
        raise VerificationError(
            "OrCases: Case 1 scope was not opened by an assumption",
            line.number,
        )
    p_assumed = ctx.assumptions[case1_scope.id]

    if disjunction.left != p_assumed:
        raise VerificationError(
            f"OrCases: Case 1 assumption '{p_assumed}' does not match left disjunct '{disjunction.left}'",
            line.number,
        )
    if disjunction.right != q_assumed:
        raise VerificationError(
            f"OrCases: Case 2 assumption '{q_assumed}' does not match right disjunct '{disjunction.right}'",
            line.number,
        )

    # Verify conclusions
    conclusion_j = ctx.get_line(line_j)
    conclusion_k = ctx.get_line(line_k)

    if conclusion_j != conclusion_k:
        raise VerificationError(
            f"OrCases: Case 1 conclusion '{conclusion_j}' does not match Case 2 conclusion '{conclusion_k}'",
            line.number,
        )

    if line.formula is not None and conclusion_j != line.formula:
        raise VerificationError(
            f"OrCases: derived conclusion '{conclusion_j}' does not match claimed formula '{line.formula}'",
            line.number,
        )

    # Close Case 2's scope by popping to its parent (since Case 1 was already popped)
    ctx.current_scope = case2_scope.parent

    return conclusion_j
