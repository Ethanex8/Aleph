"""Tests for inference rules."""

import pytest

from tools.context import ProofContext, Scope, VerificationError
from tools.inference import (
    apply_and_elim,
    apply_and_intro,
    apply_iff_trans,
    apply_impl_intro,
    apply_modus_ponens,
    apply_rule,
    apply_universal_generalization,
    apply_universal_instantiation,
)
from tools.parser.ast_nodes import (
    And,
    Biconditional,
    ForAll,
    FuncApp,
    Implies,
    InfixPredicate,
    Justification,
    Not,
    Or,
    ProofLine,
    Variable,
)
from tools.parser.ast_utils import substitute


@pytest.fixture
def ctx():
    """Fresh proof context for each test."""
    return ProofContext()


class TestModusPonens:
    def test_valid_mp(self, ctx):
        # Establish: line 1 = P ⟹ Q, line 2 = P
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = Implies(antecedent=p, consequent=q)
        ctx.proof_lines[2] = p

        line = ProofLine(number=3, formula=q, justification=Justification("MP", (1, 2)))
        result = apply_modus_ponens(ctx, line)
        assert result == q

    def test_mp_reversed_order(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = p
        ctx.proof_lines[2] = Implies(antecedent=p, consequent=q)

        line = ProofLine(number=3, formula=q, justification=Justification("MP", (1, 2)))
        result = apply_modus_ponens(ctx, line)
        assert result == q

    def test_mp_wrong_antecedent(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        r = InfixPredicate(Variable("y"), "∈", Variable("C"))
        ctx.proof_lines[1] = Implies(antecedent=p, consequent=q)
        ctx.proof_lines[2] = r  # wrong antecedent

        line = ProofLine(number=3, formula=q, justification=Justification("MP", (1, 2)))
        with pytest.raises(VerificationError, match="MP failed"):
            apply_modus_ponens(ctx, line)


class TestAndElim:
    def test_elim_left(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = And(left=p, right=q)

        line = ProofLine(number=2, formula=p, justification=Justification("AndElim", (1, "Left")))
        result = apply_and_elim(ctx, line)
        assert result == p

    def test_elim_right(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = And(left=p, right=q)

        line = ProofLine(number=2, formula=q, justification=Justification("AndElim", (1, "Right")))
        result = apply_and_elim(ctx, line)
        assert result == q

    def test_elim_non_conjunction(self, ctx):
        ctx.proof_lines[1] = InfixPredicate(Variable("x"), "∈", Variable("A"))
        line = ProofLine(
            number=2, formula=None, justification=Justification("AndElim", (1, "Left"))
        )
        with pytest.raises(VerificationError, match="not a conjunction"):
            apply_and_elim(ctx, line)


class TestAndIntro:
    def test_valid(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = p
        ctx.proof_lines[2] = q

        line = ProofLine(
            number=3, formula=And(left=p, right=q), justification=Justification("AndIntro", (1, 2))
        )
        result = apply_and_intro(ctx, line)
        assert result == And(left=p, right=q)


class TestUniversalInstantiation:
    def test_valid_ui(self, ctx):
        # ∀x (x ∈ A) → substitute x with w → w ∈ A
        body = InfixPredicate(Variable("x"), "∈", Variable("A"))
        ctx.proof_lines[1] = ForAll(variable="x", body=body)

        line = ProofLine(
            number=2,
            formula=InfixPredicate(Variable("w"), "∈", Variable("A")),
            justification=Justification("UI", (1, Variable("w"))),
        )
        result = apply_universal_instantiation(ctx, line)
        assert result == InfixPredicate(Variable("w"), "∈", Variable("A"))

    def test_valid_multi_ui(self, ctx):
        # ∀x ∀y (x ∈ y) → substitute x with w, y with z → w ∈ z
        inner_body = InfixPredicate(Variable("x"), "∈", Variable("y"))
        body = ForAll(variable="y", body=inner_body)
        ctx.proof_lines[1] = ForAll(variable="x", body=body)

        line = ProofLine(
            number=2,
            formula=InfixPredicate(Variable("w"), "∈", Variable("z")),
            justification=Justification("UI", (1, Variable("w"), Variable("z"))),
        )
        result = apply_universal_instantiation(ctx, line)
        assert result == InfixPredicate(Variable("w"), "∈", Variable("z"))

    def test_ui_non_universal(self, ctx):
        ctx.proof_lines[1] = InfixPredicate(Variable("x"), "∈", Variable("A"))
        line = ProofLine(
            number=2, formula=None, justification=Justification("UI", (1, Variable("w")))
        )
        with pytest.raises(VerificationError, match="not a universal"):
            apply_universal_instantiation(ctx, line)

    def test_multi_ui_insufficient_quantifiers(self, ctx):
        body = InfixPredicate(Variable("x"), "∈", Variable("A"))
        ctx.proof_lines[1] = ForAll(variable="x", body=body)
        # Trying to instantiate two variables but we only have one quantifier
        line = ProofLine(
            number=2,
            formula=None,
            justification=Justification("UI", (1, Variable("w"), Variable("z"))),
        )
        with pytest.raises(VerificationError, match="not a universal quantification"):
            apply_universal_instantiation(ctx, line)


class TestUniversalGeneralization:
    def test_valid_ug(self, ctx):
        from tools.context import Scope

        ctx.current_scope = Scope(id=1, parent=ctx.root_scope, free_vars={"x"})
        ctx.line_to_scope[1] = ctx.current_scope
        ctx.free_vars.add("x")
        body = InfixPredicate(Variable("x"), "∈", Variable("A"))
        ctx.proof_lines[1] = body

        line = ProofLine(
            number=2,
            formula=ForAll(variable="x", body=body),
            justification=Justification("UG", (1, "x")),
        )
        result = apply_universal_generalization(ctx, line)
        assert result == ForAll(variable="x", body=body)

    def test_ug_multi_var(self, ctx):
        from tools.context import Scope

        scope_ab = Scope(id=1, parent=ctx.root_scope, free_vars={"A", "B"})
        ctx.current_scope = scope_ab
        ctx.line_to_scope[1] = scope_ab
        ctx.free_vars.update(["A", "B"])
        body = InfixPredicate(Variable("A"), "⊆", Variable("B"))
        ctx.proof_lines[1] = body

        line = ProofLine(
            number=2,
            formula=ForAll("A", ForAll("B", body)),
            justification=Justification("UG", (1, "A", "B")),
        )
        result = apply_universal_generalization(ctx, line)
        assert result == ForAll("A", ForAll("B", body))

    def test_ug_non_free_variable(self, ctx):
        body = InfixPredicate(Variable("x"), "∈", Variable("A"))
        ctx.proof_lines[1] = body
        # x is NOT a free variable
        line = ProofLine(number=2, formula=None, justification=Justification("UG", (1, "x")))
        with pytest.raises(
            VerificationError, match="do not match the innermost active free variables"
        ):
            apply_universal_generalization(ctx, line)


class TestImplIntro:
    def test_valid(self, ctx):
        from tools.context import Scope

        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        ctx.proof_lines[1] = p
        ctx.proof_lines[2] = q

        scope_i = Scope(id=1, parent=ctx.root_scope, assumptions={1})
        ctx.current_scope = scope_i
        ctx.line_to_scope[1] = scope_i
        ctx.line_to_scope[2] = scope_i

        line = ProofLine(
            number=3, formula=Implies(p, q), justification=Justification("ImplIntro", (1, 2))
        )
        result = apply_impl_intro(ctx, line)
        assert result == Implies(antecedent=p, consequent=q)
        assert ctx.current_scope == ctx.root_scope


class TestSubstitution:
    def test_simple(self):
        f = InfixPredicate(Variable("x"), "∈", Variable("A"))
        result = substitute(f, "x", Variable("w"))
        assert result == InfixPredicate(Variable("w"), "∈", Variable("A"))

    def test_respects_binding(self):
        # ∀x (x ∈ A) — substituting x should not enter the ∀x scope
        f = ForAll("x", InfixPredicate(Variable("x"), "∈", Variable("A")))
        result = substitute(f, "x", Variable("w"))
        # Should be unchanged — x is re-bound inside ∀x
        assert result == f

    def test_substitutes_free_only(self):
        # ∀y (x ∈ y) — x is free, y is bound
        f = ForAll("y", InfixPredicate(Variable("x"), "∈", Variable("y")))
        result = substitute(f, "x", Variable("w"))
        assert result == ForAll("y", InfixPredicate(Variable("w"), "∈", Variable("y")))


class TestHypothesis:
    def test_let_statement(self, ctx):
        line = ProofLine(
            number=1,
            formula=None,
            justification=Justification("Hypothesis", ()),
            is_let=True,
            let_vars=("x", "y"),
        )
        result = apply_rule(ctx, line)
        assert result is None
        assert "x" in ctx.free_vars
        assert "y" in ctx.free_vars

    def test_assume_statement(self, ctx):
        f = InfixPredicate(Variable("x"), "∈", Variable("A"))
        line = ProofLine(
            number=1,
            formula=f,
            justification=Justification("Hypothesis", ()),
            is_assume=True,
        )
        result = apply_rule(ctx, line)
        assert result == f
        assert 1 in ctx.assumptions


class TestIffTrans:
    def test_valid_iff_trans(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        r = InfixPredicate(Variable("x"), "∈", Variable("C"))

        ctx.proof_lines[1] = Biconditional(left=p, right=q)
        ctx.proof_lines[2] = Biconditional(left=r, right=q)

        # We want to derive p ⟺ r
        line = ProofLine(
            number=3,
            formula=Biconditional(left=p, right=r),
            justification=Justification("IffTrans", (1, 2)),
        )
        result = apply_iff_trans(ctx, line)
        assert result == Biconditional(left=p, right=r)

    def test_invalid_no_shared_side(self, ctx):
        p = InfixPredicate(Variable("x"), "∈", Variable("A"))
        q = InfixPredicate(Variable("x"), "∈", Variable("B"))
        r = InfixPredicate(Variable("x"), "∈", Variable("C"))
        s = InfixPredicate(Variable("x"), "∈", Variable("D"))

        ctx.proof_lines[1] = Biconditional(left=p, right=q)
        ctx.proof_lines[2] = Biconditional(left=r, right=s)

        line = ProofLine(
            number=3,
            formula=Biconditional(left=p, right=r),
            justification=Justification("IffTrans", (1, 2)),
        )
        with pytest.raises(VerificationError, match="IffTrans: cannot derive"):
            apply_iff_trans(ctx, line)


class TestNewInference:
    def test_mt(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Implies(p, q)
        ctx.proof_lines[2] = Not(q)
        line = ProofLine(3, Not(p), Justification("MT", (1, 2)))
        assert apply_rule(ctx, line) == Not(p)

    def test_ds(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Or(p, q)
        ctx.proof_lines[2] = Not(p)
        line = ProofLine(3, q, Justification("DS", (1, 2)))
        assert apply_rule(ctx, line) == q

        ctx.proof_lines[4] = Not(q)
        line2 = ProofLine(5, p, Justification("DS", (1, 4)))
        assert apply_rule(ctx, line2) == p

    def test_dne(self, ctx):
        p = Variable("P")
        ctx.proof_lines[1] = Not(Not(p))
        line = ProofLine(2, p, Justification("DNE", (1,)))
        assert apply_rule(ctx, line) == p

    def test_dni(self, ctx):
        p = Variable("P")
        ctx.proof_lines[1] = p
        line = ProofLine(2, Not(Not(p)), Justification("DNI", (1,)))
        assert apply_rule(ctx, line) == Not(Not(p))

    def test_raa(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Not(p)
        ctx.assumptions[1] = ctx.proof_lines[1]
        ctx.current_scope = Scope(id=1, parent=ctx.root_scope, assumptions={1})

        ctx.proof_lines[2] = q
        ctx.proof_lines[3] = Not(q)

        line = ProofLine(4, p, Justification("RAA", (1, 2, 3)))
        assert apply_rule(ctx, line) == p
        assert ctx.current_scope == ctx.root_scope

    def test_vacuous(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Not(p)
        line = ProofLine(2, Implies(p, q), Justification("Vacuous", (1,)))
        assert apply_rule(ctx, line) == Implies(p, q)

    def test_iff_mp(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Biconditional(p, q)
        ctx.proof_lines[2] = p
        line = ProofLine(3, q, Justification("IffMP", (1, 2)))
        assert apply_rule(ctx, line) == q

    def test_iff_mt(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        ctx.proof_lines[1] = Biconditional(p, q)
        ctx.proof_lines[2] = Not(p)
        line = ProofLine(3, Not(q), Justification("IffMT", (1, 2)))
        assert apply_rule(ctx, line) == Not(q)

    def test_eq_replace_all(self, ctx):
        x = Variable("x")
        y = Variable("y")
        # x = x -> y = y given x = y
        phi = InfixPredicate(x, "=", x)
        ctx.proof_lines[1] = phi
        ctx.proof_lines[2] = InfixPredicate(x, "=", y)

        line = ProofLine(3, InfixPredicate(y, "=", y), Justification("EqReplaceAll", (1, 2)))
        assert apply_rule(ctx, line) == InfixPredicate(y, "=", y)

    def test_composite_axiom(self, ctx):
        # axiom Trans: ∀x ∀y ∀z ((x=y ∧ y=z) ⟹ x=z)
        x, y, z = Variable("x"), Variable("y"), Variable("z")
        a, b, c = Variable("a"), Variable("b"), Variable("c")

        trans_formula = ForAll(
            "x",
            ForAll(
                "y",
                ForAll(
                    "z",
                    Implies(
                        And(
                            InfixPredicate(x, "=", y),
                            InfixPredicate(y, "=", z),
                        ),
                        InfixPredicate(x, "=", z),
                    ),
                ),
            ),
        )
        ctx.axioms["Trans"] = trans_formula

        ctx.proof_lines[1] = And(InfixPredicate(a, "=", b), InfixPredicate(b, "=", c))

        # Test UI + UI + UI + MP
        line = ProofLine(2, InfixPredicate(a, "=", c), Justification("Axiom", ("Trans", a, b, c, 1)))
        assert apply_rule(ctx, line) == InfixPredicate(a, "=", c)

    def test_composite_theorem(self, ctx):
        p = Variable("P")
        q = Variable("Q")
        # theorem Thm: P ⟹ Q
        ctx.proven_theorems["Thm"] = Implies(p, q)
        ctx.proof_lines[1] = p

        line = ProofLine(2, q, Justification("Theorem", ("Thm", 1)))
        assert apply_rule(ctx, line) == q

    def test_composite_constant(self, ctx):
        # constant Empty: ∀x ¬(x ∈ Empty)
        x = Variable("x")
        empty = Variable("Empty")
        formula = ForAll("x", Not(InfixPredicate(x, "∈", empty)))
        ctx.constants["Empty"] = formula

        line = ProofLine(
            1,
            Not(InfixPredicate(Variable("a"), "∈", empty)),
            Justification("Constant", ("Empty", Variable("a"))),
        )
        assert apply_rule(ctx, line) == Not(InfixPredicate(Variable("a"), "∈", empty))

    def test_composite_operation(self, ctx):
        # operation A ∪ B: ∀x (x ∈ A ∪ B ⟺ x ∈ A ∨ x ∈ B)
        x = Variable("x")
        a = Variable("A")
        b = Variable("B")
        union = FuncApp("Union", (a, b))
        formula = ForAll(
            "x",
            Biconditional(
                InfixPredicate(x, "∈", union),
                Or(
                    InfixPredicate(x, "∈", a),
                    InfixPredicate(x, "∈", b),
                ),
            ),
        )
        ctx.operations["Union"] = formula

        line = ProofLine(
            1,
            Biconditional(
                InfixPredicate(Variable("z"), "∈", union),
                Or(
                    InfixPredicate(Variable("z"), "∈", a),
                    InfixPredicate(Variable("z"), "∈", b),
                ),
            ),
            Justification("Operation", ("Union", Variable("z"))),
        )
        assert apply_rule(ctx, line) == Biconditional(
            InfixPredicate(Variable("z"), "∈", union),
            Or(
                InfixPredicate(Variable("z"), "∈", a),
                InfixPredicate(Variable("z"), "∈", b),
            ),
        )

    def test_composite_chain(self, ctx):
        # axiom A1: P ⟹ (Q ⟹ R)
        p = Variable("P")
        q = Variable("Q")
        r = Variable("R")
        ctx.axioms["A1"] = Implies(p, Implies(q, r))
        ctx.proof_lines[1] = p
        ctx.proof_lines[2] = q

        line = ProofLine(3, r, Justification("Axiom", ("A1", 1, 2)))
        assert apply_rule(ctx, line) == r

    def test_composite_mixed(self, ctx):
        # axiom A2: ∀x (P(x) ⟹ Q(x))
        x = Variable("x")
        a = Variable("a")
        px = FuncApp("P", (x,))
        qx = FuncApp("Q", (x,))
        pa = FuncApp("P", (a,))
        qa = FuncApp("Q", (a,))

        ctx.axioms["A2"] = ForAll("x", Implies(px, qx))
        ctx.proof_lines[1] = pa

        line = ProofLine(2, qa, Justification("Axiom", ("A2", a, 1)))
        assert apply_rule(ctx, line) == qa


class TestEqIntro:
    def test_valid_eq_intro(self, ctx):
        a = Variable("a")
        line = ProofLine(1, InfixPredicate(a, "=", a), Justification("EqIntro", ()))
        assert apply_rule(ctx, line) == InfixPredicate(a, "=", a)

    def test_invalid_eq_intro_arguments(self, ctx):
        a = Variable("a")
        line = ProofLine(1, InfixPredicate(a, "=", a), Justification("EqIntro", (1,)))
        with pytest.raises(VerificationError, match="EqIntro requires no arguments"):
            apply_rule(ctx, line)

    def test_invalid_eq_intro_not_equality(self, ctx):
        a = Variable("a")
        line = ProofLine(1, InfixPredicate(a, "∈", a), Justification("EqIntro", ()))
        with pytest.raises(
            VerificationError, match="EqIntro: claimed formula must be of the form t = t"
        ):
            apply_rule(ctx, line)

    def test_invalid_eq_intro_mismatched_terms(self, ctx):
        a = Variable("a")
        b = Variable("b")
        line = ProofLine(1, InfixPredicate(a, "=", b), Justification("EqIntro", ()))
        with pytest.raises(
            VerificationError, match="EqIntro: claimed formula must be of the form t = t"
        ):
            apply_rule(ctx, line)
