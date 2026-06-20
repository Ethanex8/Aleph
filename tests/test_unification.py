import pytest

from tools.context import ProofContext, VerificationError
from tools.parser.ast_nodes import InfixPredicate, Variable
from tools.parser.fol_parser import parse_formula


def test_equality_is_infix_predicate():
    f = parse_formula("x = y")
    assert isinstance(f, InfixPredicate)
    assert f.operator == "="
    assert f.left == Variable("x")
    assert f.right == Variable("y")


def test_membership_is_infix_predicate():
    f = parse_formula("x ∈ A")
    assert isinstance(f, InfixPredicate)
    assert f.operator == "∈"
    assert f.left == Variable("x")
    assert f.right == Variable("A")


def test_prohibit_redefinition_equality():
    ctx = ProofContext()
    with pytest.raises(VerificationError, match="Cannot redefine primitive symbol: ="):
        ctx.register_definition("=", parse_formula("∀x ∀y (x = y ⟺ y = x)"))


def test_prohibit_redefinition_membership():
    ctx = ProofContext()
    with pytest.raises(VerificationError, match="Cannot redefine primitive symbol: ∈"):
        ctx.register_definition("∈", parse_formula("∀x ∀A (x ∈ A ⟺ x ∈ A)"))


def test_prohibit_redefinition_equality_symbol():
    ctx = ProofContext()
    with pytest.raises(VerificationError, match="Cannot redefine primitive symbol: ="):
        ctx.register_symbol("=", parse_formula("∀x ∀y (x = y)"))


def test_prohibit_redefinition_membership_symbol():
    ctx = ProofContext()
    with pytest.raises(VerificationError, match="Cannot redefine primitive symbol: ∈"):
        ctx.register_symbol("∈", parse_formula("∀x ∀A (x ∈ A)"))
