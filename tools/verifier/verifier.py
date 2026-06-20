"""Verifier loop.

The main loop that ties together parsing, extraction, inference rules, and DAG resolution.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from tools.context import ProofContext, Scope, VerificationError
from tools.inference import apply_rule
from tools.parser.ast_nodes import (
    AxiomDecl,
    DefinitionDecl,
    Formula,
    InfixPredicate,
    SchemaDecl,
    SymbolDecl,
    TheoremDecl,
)
from tools.parser.ast_utils import (
    build_req_existence,
    build_req_uniqueness,
    get_free_vars,
    unwrap_forall,
    wrap_forall,
)
from tools.parser.fol_parser import parse_fol
from tools.verifier.manifest import Manifest, ManifestError, validate_completeness, validate_exports
from tools.verifier.section import Section, SectionName


def _verify_section(
    section: Section,
    ctx: ProofContext,
) -> tuple[bool, list[str]]:
    """Verify all First-Order Logic blocks within a Section abstraction.

    Args:
        section: The Section object containing logical content.
        ctx: The proof context (shared across the entire build).

    Returns:
        A tuple of (success, list of actual exported symbol names).
    """
    success = True
    actual_exports: list[str] = []

    if not section.source.strip():
        return success, actual_exports

    try:
        declarations = parse_fol(section.source)
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, "line") and e.line is not None:
            err_line = int(e.line)
            if 1 <= err_line <= len(section.line_map):
                orig_line = section.line_map[err_line - 1]
                err_msg = f"at line {orig_line} (col {getattr(e, 'column', '?')}): {e}"
        print(f"    Error: Parse error: {err_msg}")
        return False, actual_exports

    for decl in declarations:
        try:
            name = _process_declaration(decl, ctx)
            if name:
                actual_exports.append(name)
        except VerificationError as e:
            success = False
            print(f"    Error: {e}")
        except Exception as e:
            success = False
            print(f"    Error: Internal error processing {type(decl).__name__}: {e}")

    return success, actual_exports


DECL_HANDLERS: dict[type, Callable[..., str | None]] = {}


def declaration_handler(
    cls: type,
) -> Callable[[Callable[..., str | None]], Callable[..., str | None]]:
    """Decorator to register a handler for a specific declaration type."""

    def decorator(func: Callable[..., str | None]) -> Callable[..., str | None]:
        DECL_HANDLERS[cls] = func
        return func

    return decorator


def _process_declaration(
    decl: AxiomDecl | SchemaDecl | DefinitionDecl | TheoremDecl | SymbolDecl,
    ctx: ProofContext,
) -> str | None:
    """Process a single top-level declaration using the registered handler."""
    handler = DECL_HANDLERS.get(type(decl))
    if handler:
        return handler(decl, ctx)
    else:
        raise VerificationError(f"Unknown declaration type: {type(decl)}")


@declaration_handler(AxiomDecl)
def _handle_axiom(decl: AxiomDecl, ctx: ProofContext) -> str:
    ctx.register_axiom(decl.name, decl.formula)
    print(f"  [OK] Axiom: {decl.name}")
    return decl.name


@declaration_handler(SchemaDecl)
def _handle_schema(decl: SchemaDecl, ctx: ProofContext) -> str:
    ctx.register_schema(decl)
    print(f"  [OK] Schema: {decl.name}")
    return decl.name


@declaration_handler(DefinitionDecl)
def _handle_definition(decl: DefinitionDecl, ctx: ProofContext) -> str:
    from tools.parser.ast_nodes import Biconditional

    f, _ = unwrap_forall(decl.formula)

    if not isinstance(f, Biconditional) and not (
        isinstance(f, InfixPredicate) and f.operator == "="
    ):
        raise VerificationError(
            f"Definition '{decl.name}' underlying formula is not a biconditional or equality."
        )

    lhs_vars = get_free_vars(f.left)  # type: ignore[arg-type]
    rhs_vars = get_free_vars(f.right)  # type: ignore[arg-type]

    # Remove known symbols and definitions from the free variables
    known_symbols = set(ctx.symbols.keys()) | set(ctx.definitions.keys())
    lhs_vars = {v for v in lhs_vars if v not in known_symbols}
    rhs_vars = {v for v in rhs_vars if v not in known_symbols}

    if lhs_vars != rhs_vars:
        raise VerificationError(
            f"Definition '{decl.name}' has mismatched free variables.\n"
            f"  LHS free variables: {sorted(lhs_vars)}\n"
            f"  RHS free variables: {sorted(rhs_vars)}"
        )

    ctx.register_definition(decl.name, decl.formula)
    print(f"  [OK] Definition: {decl.name}")
    return decl.name


@declaration_handler(TheoremDecl)
def _handle_theorem(decl: TheoremDecl, ctx: ProofContext) -> str:
    return _verify_theorem(decl, ctx)


@declaration_handler(SymbolDecl)
def _handle_symbol(decl: SymbolDecl, ctx: ProofContext) -> str:
    vars_in_formula = get_free_vars(decl.formula)
    known_symbols = set(ctx.symbols.keys()) | set(ctx.definitions.keys())
    vars_in_formula = {v for v in vars_in_formula if v not in known_symbols and v != decl.name}

    if vars_in_formula != set(decl.params):
        raise VerificationError(
            f"Symbol '{decl.name}' free variables do not match parameters.\n"
            f"  Expected: {sorted(set(decl.params))}\n"
            f"  Found:    {sorted(vars_in_formula)}"
        )

    _verify_defined_symbol(
        decl.name, decl.params, decl.formula, decl.existence_proof, decl.uniqueness_proof, ctx
    )
    print(f"  [OK] Symbol rigorously verified: {decl.name}")
    return decl.name


def _verify_defined_symbol(
    name: str,
    params: tuple[str, ...],
    formula: Formula,
    existence_proof: str,
    uniqueness_proof: str,
    ctx: ProofContext,
) -> None:
    """Unifies verification of existence and uniqueness proofs for defined symbols."""
    from tools.inference.references import _try_match

    req_existence = build_req_existence(name, params, formula)
    req_uniqueness = build_req_uniqueness(name, params, formula)

    for proof_name, req_form, label in [
        (existence_proof, req_existence, "existence"),
        (uniqueness_proof, req_uniqueness, "uniqueness"),
    ]:
        thm = ctx.proven_theorems.get(proof_name) or ctx.axioms.get(proof_name)
        if not thm:
            raise VerificationError(f"Symbol '{name}': {label} proof '{proof_name}' not found.")

        if _try_match(req_form, thm, []) is None and _try_match(thm, req_form, []) is None:
            raise VerificationError(
                f"Symbol '{name}': {label} proof '{proof_name}' does not match required form.\n"
                f"  Required: {req_form}\n"
                f"  Provided: {thm}"
            )

    # Registration
    if not params:
        ctx.register_symbol(name, formula)
    else:
        op_formula = wrap_forall(formula, params)
        ctx.register_symbol(name, op_formula)


def _verify_proof_lines(
    theorem: TheoremDecl,
    ctx: ProofContext,
) -> None:
    """Iterate over each proof step in a theorem.

    Dispatches to inference rules to derive conclusions and verifying that they match the
    claimed formulas.
    """
    for line in theorem.proof_lines:
        # Align scope depth for scope openers if starting a sibling or shallower scope
        if line.is_let or line.is_assume:
            while ctx.current_scope.depth > line.depth:
                if ctx.current_scope.parent is None:
                    break
                ctx.current_scope = ctx.current_scope.parent

        # 1. Visibility Check: verify all cited premise lines are visible in current scope
        just = line.justification
        premises = [arg for arg in just.args if isinstance(arg, int)]
        for idx, p in enumerate(premises):
            if p not in ctx.line_to_scope:
                raise VerificationError(
                    f"Reference to line {p} which is not yet established",
                    line.number,
                )
            # For OrCases, the second and third arguments (case conclusions)
            # are allowed to be in sibling/closed scopes that share the same parent scope.
            if just.rule_name == "OrCases" and idx in (1, 2):
                continue
            if not ctx.line_to_scope[p].is_ancestor_of(ctx.current_scope):
                raise VerificationError(
                    f"Reference to line {p} which is in a closed scope",
                    line.number,
                )

        try:
            derived = apply_rule(ctx, line)
        except VerificationError as e:
            raise VerificationError(f"Theorem '{theorem.name}', step {line.number}: {e}") from e

        if derived is not None:
            # Verify the derived formula matches what the proof claims
            if line.formula is not None and derived != line.formula:
                raise VerificationError(
                    f"Theorem '{theorem.name}', step {line.number}: "
                    f"derived formula does not match claimed formula.\n"
                    f"  Derived:  {derived}\n"
                    f"  Claimed:  {line.formula}",
                    line.number,
                )

            ctx.proof_lines[line.number] = derived

            print(f"    {line.number}. {derived}  [{line.justification}]")

            # Manage Scope lifecycle
            if line.is_assume:
                # Open a new assumption scope
                new_scope = Scope(
                    id=line.number, parent=ctx.current_scope, assumptions={line.number}
                )
                ctx.current_scope = new_scope
                ctx.line_to_scope[line.number] = new_scope
            else:
                # Register in current scope (which may have been exited/updated by a scope-closing rule)
                ctx.current_scope.derived_lines.add(line.number)
                ctx.line_to_scope[line.number] = ctx.current_scope
        else:
            # Let statement — no formula, just log
            if line.is_let:
                # Open ONE scope level for all variables in line.let_vars
                new_scope = Scope(
                    id=line.number, parent=ctx.current_scope, free_vars=set(line.let_vars)
                )
                ctx.current_scope = new_scope
                ctx.line_to_scope[line.number] = ctx.current_scope
                print(
                    f"    {line.number}. Let {', '.join(line.let_vars)} be arbitrary  [{line.justification}]"
                )


def _verify_theorem(
    theorem: TheoremDecl,
    ctx: ProofContext,
) -> str:
    """Verify a theorem by walking its proof lines.

    Applies inference rules and checks that the final result matches the claimed statement.
    """
    print(f"  >> Verifying theorem: {theorem.name}")
    print(f"    Claim: {theorem.formula}")

    ctx.reset_proof()

    _verify_proof_lines(theorem, ctx)

    # Check that the last proof line matches the theorem's claimed formula
    if theorem.proof_lines:
        last_line = theorem.proof_lines[-1]
        last_num = last_line.number

        if last_num not in ctx.proof_lines:
            raise VerificationError(
                f"Theorem '{theorem.name}': last proof line ({last_num}) did not produce a formula"
            )

        final_formula = ctx.proof_lines[last_num]
        if final_formula != theorem.formula:
            raise VerificationError(
                f"Theorem '{theorem.name}': final proof step does not match "
                f"the theorem statement.\n"
                f"  Final step: {final_formula}\n"
                f"  Theorem:    {theorem.formula}"
            )

        # Verify that all assumptions and free variables have been discharged
        if ctx.current_scope != ctx.root_scope:
            curr: Scope | None = ctx.current_scope
            open_assumptions: list[int] = []
            open_variables: list[str] = []
            while curr is not ctx.root_scope and curr is not None:
                open_assumptions.extend(curr.assumptions)
                open_variables.extend(curr.free_vars)
                curr = curr.parent

            errs = []
            if open_assumptions:
                undischarged_lines = ", ".join(
                    str(line_num) for line_num in sorted(open_assumptions)
                )
                errs.append(f"undischarged assumptions at line(s): {undischarged_lines}")
            if open_variables:
                undischarged_vars = ", ".join(sorted(open_variables))
                errs.append(f"undischarged free variables: {undischarged_vars}")

            raise VerificationError(f"Theorem '{theorem.name}': proof has " + " and ".join(errs))

    ctx.register_theorem(theorem.name, theorem.formula)
    print(f"  [OK] Theorem verified: {theorem.name}")
    return theorem.name


def _load_and_validate_manifest(
    manifest_path: Path,
) -> Manifest | None:
    """Helper to load the manifest and validate its completeness."""
    try:
        book_dir = manifest_path.parent
        manifest = Manifest.load(manifest_path)
        validate_completeness(book_dir, manifest.sections)
        return manifest
    except ManifestError as e:
        print(f"  Manifest error: {e}")
        return None


def _verify_section_in_manifest(
    section_name: SectionName,
    manifest: Manifest,
) -> bool:
    """Helper to verify a single section during book verification."""
    sec_info = manifest.sections[section_name]
    full_path = manifest.book_dir / section_name.to_path()

    ctx = ProofContext()

    # Populate context ONLY from explicit imports
    success, err_msg = manifest.populate_context_from_imports(sec_info, ctx)
    if not success:
        print(f"--- {section_name} ---")
        print("  [FAIL] FAILED")
        print(f"    Error: {err_msg}")
        return False

    print(f"--- {section_name} ---")

    try:
        section = Section.from_file(section_name, full_path)
    except Exception as e:
        print("  [FAIL] FAILED")
        print(f"    Error: Failed to read file: {e}")
        return False

    # Verify the section content
    success, actual_exports = _verify_section(section, ctx)

    if not success:
        print("  [FAIL] FAILED")
        return False

    # Validate exports match Manifest.md declaration
    try:
        validate_exports(sec_info, actual_exports)
    except ManifestError as e:
        print(f"  [FAIL] Export validation failed: {e}")
        return False

    # Record exports into global registries
    manifest.record_global_exports(sec_info, actual_exports, ctx)

    print("  [OK] OK\n")
    return True


def verify_book(
    manifest_path: Path,
    target_section: SectionName | None = None,
    target_files: list[Path] | None = None,
) -> bool:
    """Execute the full verification pipeline for the entire mathematical book.

    1. Loads and validates the manifest (`Manifest.md`).
    2. Iteratively verifies each section in topological order.
    3. Caches exported symbols in the global registry for other sections.

    Args:
        manifest_path: Path to the `Manifest.md` manifest.
        target_section: If provided, stops verification after this section.
        target_files: If provided, only verify these specific files.

    Returns:
        A boolean indicating whether the verification was fully successful.
    """
    manifest_path = Path(manifest_path)

    manifest = _load_and_validate_manifest(manifest_path)
    if not manifest:
        print("=== BOOK VERIFICATION FAILED ===")
        return False

    target_sections = None
    if target_files is not None:
        target_sections = set()
        resolved_book_dir = manifest.book_dir.resolve()
        for f in target_files:
            try:
                resolved_file = f.resolve()
                rel_path = resolved_file.relative_to(resolved_book_dir)
                sec_name = SectionName.from_path(str(rel_path))
                target_sections.add(sec_name)
            except ValueError:
                pass

    print(f"Build order: {' -> '.join(str(m) for m in manifest.order)}\n")

    all_success = True
    verified_any = False
    for section_name in manifest.order:
        if target_sections is not None and section_name not in target_sections:
            continue

        verified_any = True
        section_success = _verify_section_in_manifest(section_name, manifest)
        if not section_success:
            all_success = False
            # We no longer stop on first failure

        if target_section is not None and section_name == target_section:
            break

    print("")
    if not verified_any and target_sections is not None:
        print("No matching sections found to verify.")
        return False

    if all_success:
        print("=== BOOK VERIFIED ===")
    else:
        print("=== BOOK VERIFICATION FAILED ===")

    return all_success
