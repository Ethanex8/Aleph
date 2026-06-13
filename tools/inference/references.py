"""Helper functions for resolving references and substitutions."""

from __future__ import annotations

from typing import cast

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.inference.core import inference_rule
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
    ProofLine,
    SchemaApp,
    Term,
    Variable,
)
from tools.parser.ast_utils import substitute, substitute_schema


def _try_match(
    template: Node,
    target: Node,
    vars_to_bind: list[str],
) -> dict[str, Term] | None:
    """Try to match ``target`` against ``template``.

    Finds bindings for the variables in ``vars_to_bind``. Returns a dict of bindings, or
    None if matching fails.
    """
    bindings: dict[str, Term] = {}

    def match_inner(tmpl: Node, tgt: Node) -> bool:
        if isinstance(tmpl, Variable) and tmpl.name in vars_to_bind:
            if tmpl.name in bindings:
                return bindings[tmpl.name] == tgt
            else:
                if isinstance(tgt, Variable | FuncApp | InfixTerm):
                    bindings[tmpl.name] = tgt
                    return True
                return False

        match tmpl, tgt:
            case Variable(name=n1), Variable(name=n2):
                return n1 == n2

            case FuncApp(name=n1, args=a1), FuncApp(name=n2, args=a2):
                return (
                    n1 == n2
                    and len(a1) == len(a2)
                    and all(match_inner(ta, ga) for ta, ga in zip(a1, a2, strict=True))
                )

            case InfixTerm(left=l1, operator=op1, right=r1), InfixTerm(
                left=l2, operator=op2, right=r2
            ):
                return op1 == op2 and match_inner(l1, l2) and match_inner(r1, r2)

            case Predicate(name=n1, args=a1), Predicate(name=n2, args=a2):
                return (
                    n1 == n2
                    and len(a1) == len(a2)
                    and all(match_inner(ta, ga) for ta, ga in zip(a1, a2, strict=True))
                )

            case SchemaApp(name=n1, args=a1), SchemaApp(name=n2, args=a2):
                return (
                    n1 == n2
                    and len(a1) == len(a2)
                    and all(match_inner(ta, ga) for ta, ga in zip(a1, a2, strict=True))
                )

            case Membership(element=e1, set_=s1), Membership(element=e2, set_=s2):
                return match_inner(e1, e2) and match_inner(s1, s2)

            case InfixPredicate(left=l1, operator=op1, right=r1), InfixPredicate(
                left=l2, operator=op2, right=r2
            ):
                return op1 == op2 and match_inner(l1, l2) and match_inner(r1, r2)

            case Equality(left=l1, right=r1), Equality(left=l2, right=r2):
                return match_inner(l1, l2) and match_inner(r1, r2)

            case Not(operand=o1), Not(operand=o2):
                return match_inner(o1, o2)

            case And(left=l1, right=r1), And(left=l2, right=r2):
                return match_inner(l1, l2) and match_inner(r1, r2)

            case Or(left=l1, right=r1), Or(left=l2, right=r2):
                return match_inner(l1, l2) and match_inner(r1, r2)

            case Implies(antecedent=a1, consequent=c1), Implies(antecedent=a2, consequent=c2):
                return match_inner(a1, a2) and match_inner(c1, c2)

            case Biconditional(left=l1, right=r1), Biconditional(left=l2, right=r2):
                return match_inner(l1, l2) and match_inner(r1, r2)

            case ForAll(variable=v1, body=b1), ForAll(variable=v2, body=b2):
                if v1 == v2:
                    return match_inner(b1, b2)
                # Alpha-rename: substitute target's bound var with template's
                # bound var in the target body, then compare
                if v1 not in vars_to_bind:
                    renamed_body = substitute(b2, v2, Variable(name=v1))
                    return match_inner(b1, renamed_body)
                return False

            case Exists(variable=v1, body=b1), Exists(variable=v2, body=b2):
                if v1 == v2:
                    return match_inner(b1, b2)
                if v1 not in vars_to_bind:
                    renamed_body = substitute(b2, v2, Variable(name=v1))
                    return match_inner(b1, renamed_body)
                return False

            case _:
                return False

    if match_inner(template, target):
        return bindings
    return None


def _apply_bindings(formula: Node, bindings: dict[str, Term]) -> Node:
    """Apply variable bindings to a template formula.

    Uses simultaneous substitution. Uses a two-phase approach to avoid capture when
    template variables overlap with replacement terms.

    Phase 1: Rename all bound template vars to fresh temporaries.
    Phase 2: Replace temporaries with actual target terms.
    """
    if not bindings:
        return formula

    # Phase 1: Replace template vars with unique temporaries
    temp_bindings: dict[str, Variable] = {}
    for var_name in bindings:
        temp_name = f"__tmp_{var_name}__"
        temp_bindings[var_name] = Variable(name=temp_name)

    result = formula
    for var_name, temp_var in temp_bindings.items():
        result = substitute(result, var_name, temp_var)

    # Phase 2: Replace temporaries with actual target terms
    for var_name, term in bindings.items():
        temp_name = f"__tmp_{var_name}__"
        result = substitute(result, temp_name, term)

    return result


def _apply_composite_citation(
    ctx: ProofContext,
    line: ProofLine,
    base_formula: Formula,
    rule_name: str,
) -> Formula:
    """Helper to apply optional UI and MP.

    Applies Universal Instantiation (UI) and Modus Ponens (MP) to a base formula
    (Axiom, Theorem, Constant, or Operation).
    """
    rule_args = line.justification.args
    # rule_args[0] is the name. The rest are terms or line references.
    current_formula = base_formula

    for arg in rule_args[1:]:
        if isinstance(arg, int):
            # Modus Ponens
            line_ref = arg
            formula_ref = ctx.get_line(line_ref)
            if isinstance(current_formula, Implies) and current_formula.antecedent == formula_ref:
                current_formula = current_formula.consequent
            else:
                raise VerificationError(
                    f"{rule_name} composite error: cannot apply MP with line {line_ref}. "
                    f"Need {current_formula.antecedent if isinstance(current_formula, Implies) else 'an implication'}.",
                    line.number,
                )
        elif isinstance(arg, Variable | FuncApp | InfixTerm):
            # Universal Instantiation
            if isinstance(current_formula, ForAll):
                current_formula = cast(
                    Formula, substitute(current_formula.body, current_formula.variable, arg)
                )
            else:
                raise VerificationError(
                    f"{rule_name} composite error: cannot apply UI with term {arg}. "
                    f"Current formula is not universally quantified: {current_formula}",
                    line.number,
                )
        else:
            raise VerificationError(
                f"{rule_name} composite error: unexpected argument type: {type(arg)}", line.number
            )

    return current_formula


def _apply_citation_rule(
    ctx: ProofContext,
    line: ProofLine,
    rule_name: str,
    registry: dict[str, Formula],
) -> Formula:
    rule_args = line.justification.args
    step_number = line.number
    if len(rule_args) < 1:
        raise VerificationError(
            f"{rule_name} requires at least 1 argument (the name), got {len(rule_args)}",
            step_number,
        )

    name = str(rule_args[0]).strip()
    if name not in registry:
        raise VerificationError(f"{rule_name}: unknown {rule_name.lower()} '{name}'", step_number)

    base_formula = registry[name]
    return _apply_composite_citation(ctx, line, base_formula, rule_name)


@inference_rule("Axiom")
def apply_axiom_ref(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Axiom Name, (Term|LineRef), ...] — Axiom Reference.

    Cites a loaded axiom by name and optionally applies UI and MP.
    """
    return _apply_citation_rule(ctx, line, "Axiom", ctx.axioms)


@inference_rule("Operation")
def apply_operation_ref(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Operation Name, (Term|LineRef), ...] — Operation Reference.

    Cites a loaded operation by name and optionally applies UI and MP.
    """
    return _apply_citation_rule(ctx, line, "Operation", ctx.operations)


@inference_rule("Theorem")
def apply_theorem_ref(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Theorem Name, (Term|LineRef), ...] — Theorem Reference (opaque).

    Cites a previously proven theorem by name and optionally applies UI and MP.
    """
    return _apply_citation_rule(ctx, line, "Theorem", ctx.proven_theorems)


@inference_rule("Constant")
def apply_constant_ref(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Constant Name, (Term|LineRef), ...] — Constant Reference.

    Cites a loaded constant by name and optionally applies UI and MP.
    """
    return _apply_citation_rule(ctx, line, "Constant", ctx.constants)


@inference_rule("Schema")
def apply_schema_instantiation(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula:
    """[Schema Name, φ := concrete_formula] — Schema Instantiation.

    Instantiates an axiom schema by substituting a concrete formula
    for the schema placeholder.
    """
    rule_args = line.justification.args
    step_number = line.number
    if len(rule_args) < 2:
        raise VerificationError(
            "Schema requires a name and at least one substitution (φ := ...)",
            step_number,
        )

    schema_name = str(rule_args[0]).strip()
    if schema_name not in ctx.schemas:
        raise VerificationError(f"Schema: unknown schema '{schema_name}'", step_number)

    schema = ctx.schemas[schema_name]

    subst = rule_args[1]
    if not isinstance(subst, tuple) or len(subst) != 2:
        raise VerificationError(
            "Schema: substitution must be a tuple of (placeholder, formula)", step_number
        )
    placeholder_name = str(subst[0])
    concrete: Formula = subst[1]

    # Find the matching schema parameter
    target_param = None
    for param in schema.params:
        if param.name == placeholder_name:
            target_param = param
            break

    if target_param is None:
        raise VerificationError(
            f"Schema: '{placeholder_name}' is not a parameter of schema '{schema_name}'",
            step_number,
        )

    # Perform second-order substitution on the schema body
    return cast(
        Formula,
        substitute_schema(
            schema.formula,
            target_param.name,
            target_param.variables,
            concrete,
        ),
    )
