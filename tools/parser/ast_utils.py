"""AST Utilities — Pure mathematical and structural operations on FOL formulas and terms."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from tools.parser.ast_nodes import (
    And,
    Biconditional,
    Equality,
    Exists,
    ForAll,
    Formula,
    FuncApp,
    Implies,
    InfixPredicate,
    InfixTerm,
    Membership,
    Node,
    Not,
    Or,
    Predicate,
    SchemaApp,
    Term,
    Variable,
)
from tools.parser.ast_transformer import FormulaTransformer


def wrap_forall(formula: Formula, variables: Iterable[str]) -> Formula:
    """Wrap a formula in nested ForAll quantifiers in reversed order of variables."""
    result = formula
    for var in reversed(list(variables)):
        result = ForAll(variable=var, body=result)
    return result


def unwrap_forall(formula: Formula) -> tuple[Formula, list[str]]:
    """Unwrap all leading ForAll quantifiers, returning the core body and bound variables."""
    body = formula
    vars_unwrapped = []
    while isinstance(body, ForAll):
        vars_unwrapped.append(body.variable)
        body = body.body
    return body, vars_unwrapped


def build_req_existence(name: str, params: tuple[str, ...], formula: Formula) -> Formula:
    """Construct the required existence formula for a defined symbol."""
    phi_c = _substitute_c(formula, name, params, Variable("__c"))
    req = Exists(variable="__c", body=phi_c)
    return wrap_forall(req, params)


def build_req_uniqueness(name: str, params: tuple[str, ...], formula: Formula) -> Formula:
    """Construct the required uniqueness formula for a defined symbol."""
    phi_c = _substitute_c(formula, name, params, Variable("__c"))
    phi_d = _substitute_c(formula, name, params, Variable("__d"))

    req = ForAll(
        variable="__c",
        body=ForAll(
            variable="__d",
            body=Implies(
                antecedent=And(left=phi_c, right=phi_d),
                consequent=Equality(left=Variable("__c"), right=Variable("__d")),
            ),
        ),
    )
    return wrap_forall(req, params)


def _substitute_c(formula: Formula, name: str, params: tuple[str, ...], var_c: Variable) -> Formula:
    """Helper to substitute the defined symbol (constant or operation) with a variable in a formula."""
    if not params:
        return cast(Formula, substitute(formula, name, var_c))

    if name in ["∪", "∩", "∖"]:
        target: Term = InfixTerm(left=Variable(params[0]), operator=name, right=Variable(params[1]))
    else:
        target = FuncApp(name=name, args=tuple(Variable(p) for p in params))
    return cast(Formula, substitute_term(formula, target, var_c))


def substitute(formula: Node, var_name: str, replacement: Term) -> Node:
    """Substitute all free occurrences of variable `var_name` with `replacement` in `formula`.

    Examples:
        `substitute(∀x (x = y), 'y', 'z')` → `∀x (x = z)`
        `substitute(∀x (x = y), 'x', 'z')` → `∀x (x = y)` (since x is bound)
    """

    def transform(node: Node) -> Node | None:
        if isinstance(node, Variable) and node.name == var_name:
            return replacement
        if isinstance(node, (ForAll, Exists)) and node.variable == var_name:
            return node  # var is re-bound; do not enter scope
        return None

    return FormulaTransformer(transform).transform(formula)


def substitute_term(formula: Node, target: Term, replacement: Term) -> Node:
    """Substitute all occurrences of ``target`` term with ``replacement`` term."""

    def transform(node: Node) -> Node | None:
        if node == target:
            return replacement
        return None

    return FormulaTransformer(transform).transform(formula)


def substitute_equality(formula: Node, target: Term, replacement: Term, claimed: Node) -> bool:
    """Check if `claimed` can be derived from `formula`.

    Replaces exactly ONE occurrence of `target` with `replacement`.
    """
    skip = 0
    while True:
        matches_seen = 0

        def transform(node: Node, _skip: int = skip) -> Node | None:
            nonlocal matches_seen
            if node == target:
                if matches_seen == _skip:
                    matches_seen += 1
                    return replacement
                matches_seen += 1
            return None

        new_f = FormulaTransformer(transform).transform(formula)
        if matches_seen <= skip:
            break
        if new_f == claimed:
            return True
        skip += 1
    return False


def substitute_schema(
    formula: Node,
    schema_var_name: str,
    schema_var_params: tuple[str, ...],
    concrete_formula: Node,
) -> Node:
    """Perform second-order substitution for schema instantiation."""

    def transform(node: Node) -> Node | None:
        if isinstance(node, SchemaApp) and node.name == schema_var_name:
            result = concrete_formula
            for param_var, actual_arg in zip(schema_var_params, node.args, strict=True):
                result = substitute(result, param_var, actual_arg)
            return result
        # Predicates and FuncApps don't contain schema apps in our use
        if isinstance(node, (Predicate, FuncApp)):
            return node
        return None

    return FormulaTransformer(transform).transform(formula)


def get_free_vars(formula: Formula) -> set[str]:
    """Retrieve the set of all free variables in the given formula or term."""
    free_vars: set[str] = set()
    bound_vars: set[str] = set()

    def visit(node: Formula | Term) -> None:
        if node is None:
            return
        match node:
            case Variable(name=name):
                if name not in bound_vars:
                    free_vars.add(name)
            case FuncApp(args=args) | Predicate(args=args) | SchemaApp(args=args):
                for arg in args:
                    visit(arg)
            case (
                InfixTerm(left=l, right=r)
                | InfixPredicate(left=l, right=r)
                | Equality(left=l, right=r)
                | Membership(element=l, set_=r)
                | And(left=l, right=r)
                | Or(left=l, right=r)
                | Implies(antecedent=l, consequent=r)
                | Biconditional(left=l, right=r)
            ):
                visit(l)
                visit(r)
            case Not(operand=o):
                visit(o)
            case ForAll(variable=v, body=b) | Exists(variable=v, body=b):
                was_bound = v in bound_vars
                bound_vars.add(v)
                visit(b)
                if not was_bound:
                    bound_vars.remove(v)

    visit(formula)
    return free_vars
