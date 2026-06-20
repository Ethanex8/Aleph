"""FOL Parser — transforms Lark parse trees into Aleph AST nodes.

Usage::

    from tools.parser.fol_parser import parse_fol
    declarations = parse_fol(fol_source_text)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lark import Lark, Token, Transformer, v_args

from tools.parser.ast_nodes import (
    And,
    AxiomDecl,
    Biconditional,
    DefinitionDecl,
    Exists,
    ForAll,
    Formula,
    FuncApp,
    Implies,
    InfixPredicate,
    InfixTerm,
    Justification,
    Not,
    SymbolDecl,
    Or,
    Predicate,
    ProofLine,
    SchemaApp,
    SchemaDecl,
    SchemaParam,
    Term,
    TheoremDecl,
    Variable,
)
from tools.parser.ast_utils import wrap_forall

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"


def _build_parser() -> Lark:
    """Build and return the Lark parser (cached at module level)."""
    return Lark(
        _GRAMMAR_PATH.read_text(encoding="utf-8"),
        start="start",
        parser="earley",
        ambiguity="resolve",
    )


_parser: Lark | None = None


def _get_parser() -> Lark:
    """Retrieve the cached Lark parser, constructing it on the first call."""
    global _parser
    if _parser is None:
        _parser = _build_parser()
    return _parser


@v_args(inline=True)
class FolTransformer(Transformer):  # type: ignore[type-arg]
    """Convert Lark parse tree into Aleph AST nodes."""

    def start(self, *statements: Any) -> list[Any]:
        """Assemble all top-level statements, filtering out any empty/None entries."""
        return [s for s in statements if s is not None]

    def axiom_decl(self, name: Token, formula: Formula) -> AxiomDecl:
        """Construct an AxiomDecl AST node from parsed name and formula."""
        return AxiomDecl(name=str(name), formula=formula)

    def schema_decl(self, name: Token, params: Any, formula: Formula) -> SchemaDecl:
        """Construct a SchemaDecl AST node containing parameters and the schema body."""
        return SchemaDecl(name=str(name), params=tuple(params), formula=formula)

    def schema_params(self, *params: Any) -> list[Any]:
        """Collect schema parameter placeholder declarations into a list."""
        return list(params)

    def schema_param(self, name: Token, param_vars: Any) -> SchemaParam:
        """Create a SchemaParam object mapping a schema variable name to its variables."""
        return SchemaParam(name=str(name), variables=tuple(param_vars))

    def param_vars(self, *names: Any) -> list[str]:
        """Map parameter token names to a list of strings."""
        return [str(n) for n in names]

    def sig_infix(self, left: Token, op: Token, right: Token) -> tuple[str, tuple[str, ...]]:
        """Produce signature for infix notation."""
        return (str(op), (str(left), str(right)))

    def sig_prefix(self, name: Token, var_list: Any = None) -> tuple[str, tuple[str, ...]]:
        """Produce signature for standard prefix notation."""
        return (str(name), tuple(var_list) if var_list is not None else ())

    def sig_set_enum(self, param_vars: Any) -> tuple[str, tuple[str, ...]]:
        """Return set enum signature: ('{,,}', parameter tuple)."""
        commas = "," * (len(param_vars) - 1)
        name = f"{{{commas}}}"
        return (name, tuple(param_vars))

    def definition_decl(self, signature: Any, formula: Formula) -> DefinitionDecl:
        """Construct a DefinitionDecl AST node for a formula definition.

        Converts LHS <=> RHS into a universally quantified formula.
        """
        name, params = signature
        # Reconstruct LHS formula
        lhs: Formula
        if name in {"⊆", "⊂", "≈", "≅", "∼", "≃", "≤", "≥", "<", ">", "∉", "≠", "=", "∈"}:
            lhs = InfixPredicate(left=Variable(params[0]), operator=name, right=Variable(params[1]))
        else:
            lhs = Predicate(name=name, args=tuple(Variable(p) for p in params))

        full_formula: Formula = Biconditional(left=lhs, right=formula)
        full_formula = wrap_forall(full_formula, list(params))

        return DefinitionDecl(name=name, formula=full_formula)

    def term_definition_decl(self, signature: Any, term: Term) -> DefinitionDecl:
        """Construct a DefinitionDecl for a term definition.

        Converts LHS = RHS into a universally quantified formula.
        """
        name, params = signature
        # Reconstruct LHS term
        lhs: Term
        if name in {"∪", "∩", "∖"}:
            lhs = InfixTerm(left=Variable(params[0]), operator=name, right=Variable(params[1]))
        else:
            lhs = FuncApp(name=name, args=tuple(Variable(p) for p in params))

        full_formula: Formula = InfixPredicate(left=lhs, operator="=", right=term)
        full_formula = wrap_forall(full_formula, list(params))

        return DefinitionDecl(name=name, formula=full_formula)

    def symbol_decl(
        self,
        sig: Any,
        formula: Formula,
        ex_proof: Token,
        un_proof: Token,
    ) -> SymbolDecl:
        """Construct a SymbolDecl rigorously backed by existence and uniqueness proofs."""
        name, params = sig
        return SymbolDecl(
            name=name,
            params=params,
            formula=formula,
            existence_proof=str(ex_proof),
            uniqueness_proof=str(un_proof),
        )

    def theorem_decl(self, name: Token, formula: Formula, proof_body: Any) -> TheoremDecl:
        """Construct a TheoremDecl grouping name, claimed formula, and proof steps."""
        return TheoremDecl(
            name=str(name),
            formula=formula,
            proof_lines=tuple(proof_body),
        )

    def proof_body(self, *lines: Any) -> list[Any]:
        """Assemble all proof lines inside a proof body, ignoring empty lines."""
        return [line for line in lines if line is not None]

    def proof_line(self, number: Token, content: Any, justification: Justification) -> ProofLine:
        """Create a ProofLine AST node.

        Handles either structural statements (Let/Assume, which return dicts) or standard
        formula lines.
        """
        num = int(str(number))
        actual_indent = (number.column or 1) - 1
        if isinstance(content, dict):
            # If content is a dictionary, it represents a 'let' or 'assume' structural step
            return ProofLine(
                number=num,
                formula=content.get("formula"),
                justification=justification,
                is_let=content.get("is_let", False),
                let_vars=content.get("let_vars", ()),
                is_assume=content.get("is_assume", False),
                actual_indent=actual_indent,
            )
        else:
            # Otherwise, it's a standard logical step asserting a formula
            return ProofLine(
                number=num,
                formula=content,
                justification=justification,
                actual_indent=actual_indent,
            )

    def let_stmt(self, var_list: Any) -> dict[str, Any]:
        """Construct a 'let' statement dictionary containing free variables to bind."""
        return {"is_let": True, "let_vars": tuple(var_list), "formula": None}

    def var_list(self, *names: Any) -> list[str]:
        """Convert list of variable tokens to list of strings."""
        return [str(n) for n in names]

    def assume_stmt(self, formula: Formula) -> dict[str, Any]:
        """Construct an 'assume' statement dictionary containing the assumed formula."""
        return {"is_assume": True, "formula": formula}

    def justification(self, rule_name: str, arg_list: Any = None) -> Justification:
        """Create a Justification object mapping a rule name to its arguments."""
        return Justification(
            rule_name=rule_name, args=tuple(arg_list) if arg_list is not None else ()
        )

    def rule_name(self, name: Token) -> str:
        """Convert a rule name token to string."""
        return str(name)

    def just_arg_list(self, *args: Any) -> list[Any]:
        """Assemble arguments for a justification into a list."""
        return list(args)

    def just_line(self, num: Token) -> int:
        """Parse justification line reference token to integer."""
        return int(str(num))

    def just_word(self, name: Token) -> str:
        """Convert justification symbolic name token to string."""
        return str(name)

    def schema_subst(self, var: Token, formula: Formula) -> tuple[str, Formula]:
        """Produce schema substitution tuple: (placeholder_variable, concrete_formula)."""
        return (str(var), formula)

    def bicond(self, left: Formula, _op: Any, right: Formula) -> Biconditional:
        """Construct a Biconditional (left <=> right) formula node."""
        return Biconditional(left=left, right=right)

    def implies(self, left: Formula, _op: Any, right: Formula) -> Implies:
        """Construct an Implies (left => right) formula node."""
        return Implies(antecedent=left, consequent=right)

    def or_(self, left: Formula, _op: Any, right: Formula) -> Or:
        r"""Construct an Or (left \/ right) formula node."""
        return Or(left=left, right=right)

    def and_(self, left: Formula, _op: Any, right: Formula) -> And:
        r"""Construct an And (left /\ right) formula node."""
        return And(left=left, right=right)

    def not_(self, _op: Any, operand: Formula) -> Not:
        """Construct a Not (~operand) formula node."""
        return Not(operand=operand)

    def forall(self, _op: Any, var: Token, body: Formula) -> ForAll:
        """Construct a universal quantifier ForAll (forall x, body) formula node."""
        return ForAll(variable=str(var), body=body)

    def exists(self, _op: Any, var: Token, body: Formula) -> Exists:
        """Construct an existential quantifier Exists (exists x, body) formula node."""
        return Exists(variable=str(var), body=body)

    def predicate(self, name: Token, term_list: Any = None) -> Predicate:
        """Construct a standard Predicate application node over terms."""
        return Predicate(name=str(name), args=tuple(term_list) if term_list is not None else ())

    def schema_app(self, name: Token, term_list: Any) -> SchemaApp:
        """Construct a SchemaApp application node over terms."""
        return SchemaApp(name=str(name), args=tuple(term_list))

    def infix_predicate(self, left: Term, op: Token, right: Term) -> InfixPredicate:
        """Construct an InfixPredicate formula node (e.g. left subsetEq right)."""
        return InfixPredicate(left=left, operator=str(op), right=right)

    def term_list(self, *terms: Any) -> list[Any]:
        """Assemble terms into a list."""
        return list(terms)

    def variable(self, name: Token) -> Variable:
        """Construct a Variable term node."""
        return Variable(name=str(name))

    def func_app(self, name: Token, term_list: Any) -> FuncApp:
        """Construct a function application FuncApp node over terms."""
        return FuncApp(name=str(name), args=tuple(term_list))

    def infix_term(self, left: Term, op: Token, right: Term) -> InfixTerm:
        """Construct an InfixTerm node (e.g., left + right)."""
        return InfixTerm(left=left, operator=str(op), right=right)

    def set_enum(self, term_list: Any) -> FuncApp:
        """Construct a set enumeration node as a standard FuncApp with a symbolic name."""
        commas = "," * (len(term_list) - 1)
        name = f"{{{commas}}}"
        return FuncApp(name=name, args=tuple(term_list))


# Rules that close an assumption scope (opened by Assume)
_ASSUMPTION_CLOSERS = {"ImplIntro"}

# Rules that close a variable scope (opened by Let)
_VARIABLE_CLOSERS = {"UG", "ExistsElim"}

_INDENT_UNIT = 4  # spaces per scope level


def _expected_indent(depth: int) -> int:
    """Return the expected leading-space count for a line at the given scope depth."""
    return depth * _INDENT_UNIT


def _validate_proof_indentation(
    source: str,
    declarations: list[Any],
) -> None:
    """Verify proof line indentation.

    Walks every TheoremDecl in ``declarations`` and verify that each proof
    line's leading whitespace matches the expected scope depth.

    Indentation convention
    ----------------------
    - The first proof line starts at depth 1 (four spaces).
    - ``Let`` / ``Assume`` lines sit at depth N and open a child scope;
      lines *inside* that scope are at depth N + 1.
    - Scope-closing lines (``ImplIntro``, ``UG``, ``ExistsElim``) first pop
      the scope stack and then sit at the resulting depth — making the opener
      and its closer share the same column.
    - Regular lines sit at the current depth.

    Raises ``VerificationError`` on the first mismatch found.
    """
    import re

    from tools.context import VerificationError
    from tools.parser.ast_nodes import TheoremDecl

    # Split combined source into lines for per-theorem scanning
    source_lines = source.splitlines()
    proof_line_re = re.compile(r"^( *)(\d+)\. ")

    # 1. Enforce 0-indent for headers and 4-indent for non-proof bodies
    header_keywords = {
        "axiom",
        "schema",
        "definition",
        "theorem",
        "symbol",
        "proof:",
        "qed",
        "existence:",
        "uniqueness:",
    }

    for line_idx, raw_line in enumerate(source_lines):
        if not raw_line.strip() or raw_line.strip().startswith("//"):
            continue

        m_proof = proof_line_re.match(raw_line)
        if m_proof:
            continue

        indent = len(raw_line) - len(raw_line.lstrip())
        stripped = raw_line.strip()
        # Some headers might be followed by other text, e.g., "theorem Name:"
        is_header = any(stripped.startswith(kw) for kw in header_keywords)

        if is_header:
            if indent != 0:
                raise VerificationError(
                    f"Header '{stripped}' must have 0 indentation (found {indent} spaces).",
                    line_idx + 1,
                )
        else:
            # It's likely a formula in a declaration body (e.g., right after 'axiom Name:')
            if indent != 4:
                raise VerificationError(
                    f"Line '{stripped}' must have exactly 4 spaces of indentation (found {indent} spaces).",
                    line_idx + 1,
                )

    for decl in declarations:
        if not isinstance(decl, TheoremDecl):
            continue

        # depth tracks how many open scopes we are inside (starts at 1 because
        # the proof body itself is one level inside the theorem declaration).
        depth = 1

        for proof_line in decl.proof_lines:
            num = proof_line.number
            rule = proof_line.justification.rule_name

            # --- Compute expected indent, adjusting depth for closers first ---
            if rule == "OrCases":
                depth -= 1
            elif rule in _ASSUMPTION_CLOSERS:
                # Pop the innermost assumption scope before checking indent
                depth -= 1
            elif rule in _VARIABLE_CLOSERS:
                # Both UG and ExistsElim close one level of indentation
                depth -= 1

            expected = _expected_indent(depth)
            actual = proof_line.actual_indent

            # If actual indentation is shallower than expected, pop the depth/scope level to match.
            # This handles sibling scopes (like Case 2 starting after Case 1 ends).
            while expected > actual and depth > 1:
                depth -= 1
                expected = _expected_indent(depth)

            if actual != expected:
                raise VerificationError(
                    f"Theorem '{decl.name}': proof line {num} has "
                    f"{actual} leading spaces but expected {expected} "
                    f"(scope depth {depth}). "
                    f"Check that 'Let'/'Assume' blocks are indented by "
                    f"{_INDENT_UNIT} spaces and that their scope-closing "
                    f"rules (UG/ImplIntro/ExistsElim) are at the same "
                    f"column as the opener.",
                    num,
                )

            # Store the computed depth on the proof line object so the verifier can align scopes
            object.__setattr__(proof_line, "depth", depth)

            # --- After checking, push scope for openers ---
            if proof_line.is_assume:
                depth += 1
            elif proof_line.is_let:
                # Each 'Let' statement opens exactly one level of indentation
                depth += 1


_transformer = FolTransformer()


def parse_fol(source: str) -> list[Any]:
    """Parse a string of FOL source text into Aleph AST declarations.

    Processes top-level declarations such as Axioms, Schemas, Definitions,
    Constants, Operations, and Theorems.

    Args:
        source: The raw FOL source text extracted from Markdown blocks.

    Returns:
        A list of top-level declaration objects (e.g., `AxiomDecl`, `TheoremDecl`).

    Note:
        After a successful parse, this function validates that proof lines
        are indented consistently with the logical scope tree (4 spaces per
        scope level, with openers and closers sharing the same column).
    """
    tree = _get_parser().parse(source)
    declarations: list[Any] = _transformer.transform(tree)
    _validate_proof_indentation(source, declarations)
    return declarations


def parse_formula(source: str) -> Formula:
    """Parse a single standalone formula string.

    Useful for tests and programmatically creating formula AST nodes.
    Wraps the formula in a dummy axiom to reuse the main parser logic.

    Args:
        source: A string containing a valid First-Order Logic formula.

    Returns:
        A `Formula` AST node.
    """
    wrapper = f"axiom TmpTest:\n    {source}\n"
    decls = parse_fol(wrapper)
    if len(decls) != 1:
        msg = f"Expected 1 declaration, got {len(decls)}"
        raise ValueError(msg)
    if not isinstance(decls[0], AxiomDecl):
        msg = f"Expected AxiomDecl, got {type(decls[0]).__name__}"
        raise ValueError(msg)
    return decls[0].formula
