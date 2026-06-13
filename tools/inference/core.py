"""Core inference rule registry and dispatcher."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.context import (
    ProofContext,
    VerificationError,
)
from tools.parser.ast_nodes import (
    Formula,
    ProofLine,
)

"""
Inference Rules — hardcoded evaluation functions for each rule of inference.

Each rule function validates that the cited premises support the conclusion,
then returns the derived formula. Raises ``VerificationError`` on failure.
"""

RULE_REGISTRY: dict[str, Callable[..., Formula | None]] = {}


def inference_rule(
    name: str,
) -> Callable[[Callable[..., Formula | None]], Callable[..., Formula | None]]:
    """Decorator to register an inference rule."""

    def decorator(func: Callable[..., Formula | None]) -> Callable[..., Formula | None]:
        RULE_REGISTRY[name] = func
        return func

    return decorator


def _get_line_ref(arg: Any) -> int:
    """Normalize a justification argument into an integer line reference, raising a TypeError if it is invalid."""
    if isinstance(arg, int):
        return arg
    raise TypeError(f"Expected integer line reference, got {type(arg)}")


def extract_line_refs(
    rule_name: str,
    args: tuple[Any, ...],
    expected_len: int,
    line_num: int,
) -> list[int]:
    """Verify argument count and extract safe integer line references."""
    if len(args) != expected_len:
        raise VerificationError(
            f"{rule_name} requires exactly {expected_len} line references, got {len(args)}",
            line_num,
        )
    refs = []
    for idx, arg in enumerate(args):
        try:
            refs.append(_get_line_ref(arg))
        except TypeError:
            raise VerificationError(
                f"{rule_name}: expected line reference at position {idx + 1}, got {type(arg).__name__}",
                line_num,
            ) from None
    return refs


def apply_rule(
    ctx: ProofContext,
    line: ProofLine,
) -> Formula | None:
    """Dispatch a proof line to its corresponding inference rule evaluator.

    Validates the justification tag (e.g., "MP", "UI", "Axiom") and
    executes the appropriate logic to derive a formula.

    Args:
        ctx: Current proof context (containing proven lines and global state).
        line: The proof line object to evaluate.

    Returns:
        The derived `Formula` AST node, or `None` for structural steps (like `Let`).

    Raises:
        VerificationError: If the rule arguments are invalid or the logic fails.
    """
    rule_name = line.justification.rule_name

    if rule_name in RULE_REGISTRY:
        result: Formula | None = RULE_REGISTRY[rule_name](ctx, line)
        return result

    raise VerificationError(f"Unknown inference rule: '{rule_name}'", line.number)
