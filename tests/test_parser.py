"""Tests for the FOL parser and grammar."""

from tools.parser.ast_nodes import (
    And,
    AxiomDecl,
    Biconditional,
    DefinitionDecl,
    Exists,
    ForAll,
    Implies,
    InfixPredicate,
    Not,
    Or,
    Predicate,
    SchemaApp,
    SchemaDecl,
    TheoremDecl,
    Variable,
)
from tools.parser.fol_parser import parse_fol, parse_formula


class TestFormulaParser:
    """Test parsing individual formulas."""

    def test_simple_membership(self):
        f = parse_formula("x ∈ A")
        assert f == InfixPredicate(left=Variable("x"), operator="∈", right=Variable("A"))

    def test_subset(self):
        f = parse_formula("A ⊆ B")
        assert f == InfixPredicate(left=Variable("A"), operator="⊆", right=Variable("B"))

    def test_equality(self):
        f = parse_formula("x = y")
        assert f == InfixPredicate(left=Variable("x"), operator="=", right=Variable("y"))

    def test_negation(self):
        f = parse_formula("¬(x ∈ A)")
        assert f == Not(
            operand=InfixPredicate(left=Variable("x"), operator="∈", right=Variable("A"))
        )

    def test_notin(self):
        f = parse_formula("x ∉ A")
        assert f == InfixPredicate(left=Variable("x"), operator="∉", right=Variable("A"))

    def test_conjunction(self):
        f = parse_formula("x ∈ A ∧ y ∈ B")
        assert isinstance(f, And)
        assert f.left == InfixPredicate(left=Variable("x"), operator="∈", right=Variable("A"))
        assert f.right == InfixPredicate(left=Variable("y"), operator="∈", right=Variable("B"))

    def test_disjunction(self):
        f = parse_formula("x = A ∨ x = B")
        assert isinstance(f, Or)

    def test_implication(self):
        f = parse_formula("x ∈ A ⟹ x ∈ B")
        assert isinstance(f, Implies)
        assert f.antecedent == InfixPredicate(left=Variable("x"), operator="∈", right=Variable("A"))
        assert f.consequent == InfixPredicate(left=Variable("x"), operator="∈", right=Variable("B"))

    def test_biconditional(self):
        f = parse_formula("x ∈ A ⟺ x ∈ B")
        assert isinstance(f, Biconditional)

    def test_universal_quantifier(self):
        f = parse_formula("∀x (x ∈ A)")
        assert isinstance(f, ForAll)
        assert f.variable == "x"
        assert f.body == InfixPredicate(left=Variable("x"), operator="∈", right=Variable("A"))

    def test_existential_quantifier(self):
        f = parse_formula("∃x (x ∈ A)")
        assert isinstance(f, Exists)
        assert f.variable == "x"

    def test_nested_quantifiers(self):
        f = parse_formula("∀x ∀y (x ∈ y ⟹ y ∈ x)")
        assert isinstance(f, ForAll)
        assert isinstance(f.body, ForAll)
        assert isinstance(f.body.body, Implies)

    def test_quantifier_negation(self):
        """Ensure ∀x ¬(P) parses correctly (the grammar bug we fixed)."""
        f = parse_formula("∀x ¬(x ∈ A)")
        assert isinstance(f, ForAll)
        assert isinstance(f.body, Not)

    def test_predicate(self):
        f = parse_formula("P(x, y)")
        assert f == Predicate(name="P", args=(Variable("x"), Variable("y")))

    def test_schema_app(self):
        f = parse_formula("φ(x)")
        assert f == SchemaApp(name="φ", args=(Variable("x"),))

    def test_operator_precedence_and_over_or(self):
        """∧ binds tighter than ∨."""
        f = parse_formula("A ⊆ B ∨ B ⊆ C ∧ C ⊆ D")
        # Should parse as (A ⊆ B) ∨ ((B ⊆ C) ∧ (C ⊆ D))
        assert isinstance(f, Or)
        assert isinstance(f.right, And)

    def test_operator_precedence_implies(self):
        """⟹ binds looser than ∨."""
        f = parse_formula("A ⊆ B ∨ B ⊆ C ⟹ C ⊆ D")
        # Should parse as ((A ⊆ B) ∨ (B ⊆ C)) ⟹ (C ⊆ D)
        assert isinstance(f, Implies)
        assert isinstance(f.antecedent, Or)

    def test_extensionality_axiom_formula(self):
        f = parse_formula("∀x ∀y (∀z (z ∈ x ⟺ z ∈ y) ⟹ x = y)")
        assert isinstance(f, ForAll)
        assert f.variable == "x"
        assert isinstance(f.body, ForAll)
        assert isinstance(f.body.body, Implies)
        assert isinstance(f.body.body.antecedent, ForAll)
        assert isinstance(f.body.body.antecedent.body, Biconditional)


class TestDeclarationParser:
    """Test parsing top-level declarations."""

    def test_axiom(self):
        decls = parse_fol("axiom Test:\n    ∀x (x = x)\n")
        assert len(decls) == 1
        assert isinstance(decls[0], AxiomDecl)
        assert decls[0].name == "Test"
        assert isinstance(decls[0].formula, ForAll)

    def test_definition_signature(self):
        decls = parse_fol("definition A ⊆ B:\n    ∀x (x ∈ A ⟹ x ∈ B)\n")
        assert len(decls) == 1
        assert isinstance(decls[0], DefinitionDecl)
        assert decls[0].name == "⊆"

        # It should auto-construct the biconditional
        formula = decls[0].formula
        assert isinstance(formula, ForAll)
        assert formula.variable == "A"
        assert isinstance(formula.body, ForAll)
        assert formula.body.variable == "B"
        assert isinstance(formula.body.body, Biconditional)
        assert isinstance(formula.body.body.left, InfixPredicate)
        assert formula.body.body.left.operator == "⊆"

    def test_schema(self):
        decls = parse_fol("schema Spec(φ(x)):\n    ∀A ∃B ∀x (x ∈ B ⟺ (x ∈ A ∧ φ(x)))\n")
        assert len(decls) == 1
        assert isinstance(decls[0], SchemaDecl)
        assert decls[0].name == "Spec"
        assert len(decls[0].params) == 1
        assert decls[0].params[0].name == "φ"
        assert decls[0].params[0].variables == ("x",)

    def test_schema_multi_param(self):
        decls = parse_fol("schema Repl(φ(x, y)):\n    ∀A ∃B (A ∈ B)\n")
        assert len(decls) == 1
        assert decls[0].params[0].variables == ("x", "y")

    def test_theorem_with_proof(self):
        src = (
            "theorem Test:\n"
            "    ∀x (x = x)\n"
            "proof:\n"
            "    1. Let x be arbitrary                [Hypothesis]\n"
            "        2. x = x                             [Hypothesis]\n"
            "    3. ∀x (x = x)                        [UG 2, x]\n"
            "qed\n"
        )
        decls = parse_fol(src)
        assert len(decls) == 1
        thm = decls[0]
        assert isinstance(thm, TheoremDecl)
        assert thm.name == "Test"
        assert len(thm.proof_lines) == 3

        # Check Let line
        assert thm.proof_lines[0].is_let
        assert thm.proof_lines[0].let_vars == ("x",)

        # Check regular formula line
        assert thm.proof_lines[1].formula == InfixPredicate(Variable("x"), "=", Variable("x"))

    def test_multiple_declarations(self):
        src = "axiom A1:\n    x = x\n\naxiom A2:\n    y = y\n"
        decls = parse_fol(src)
        assert len(decls) == 2
        assert isinstance(decls[0], AxiomDecl)
        assert isinstance(decls[1], AxiomDecl)
