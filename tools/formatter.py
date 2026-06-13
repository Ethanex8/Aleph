"""FOL Formatter — standardizes the spacing of justifications `[...]` in `fol` blocks."""

from __future__ import annotations

import re
from pathlib import Path

# Regex to match a proof line inside a `fol` block.
# Group 1: Leading indentation
# Group 2: Line number and following space (e.g., "1. ")
# Group 3: Formula or statement
# Group 4: Spacer whitespace
# Group 5: Justification bracket "[...]"
PROOF_LINE_PAT = re.compile(r"^(\s*)(\d+\.\s*)(.*?)(\s*)(\[[^\]]+\])\s*$")


def format_fol_line(line: str, spacing: int = 1) -> str:
    """Format a single line if it is a proof line. Otherwise, return it unchanged."""
    match = PROOF_LINE_PAT.match(line)
    if not match:
        return line
    indent, num_prefix, formula, _, justification = match.groups()
    spacer = " " * spacing
    return f"{indent}{num_prefix}{formula}{spacer}{justification}"


def format_content(content: str, spacing: int = 1) -> tuple[str, bool]:
    """Format all `fol` blocks in the given markdown content.

    Returns a tuple (formatted_content, is_changed).
    """
    from tools.common import iter_fol_lines

    formatted_lines: list[str] = []
    is_changed = False

    for _orig_line_num, stripped, is_inside_fol, ending in iter_fol_lines(content):
        line = stripped + ending
        if not is_inside_fol:
            formatted_lines.append(line)
        else:
            formatted_line_body = format_fol_line(stripped, spacing=spacing)
            new_line = formatted_line_body + ending
            if new_line != line:
                is_changed = True
            formatted_lines.append(new_line)

    return "".join(formatted_lines), is_changed


def format_file(file_path: Path, spacing: int = 1, check: bool = False) -> bool:
    """Format the specified markdown file.

    If check is True, does not modify the file; returns True if formatting changes are needed.
    If check is False, writes the formatted content back; returns True if changes were written.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    formatted, is_changed = format_content(content, spacing=spacing)

    if is_changed:
        if not check:
            try:
                file_path.write_text(formatted, encoding="utf-8")
            except Exception as e:
                print(f"Error writing to {file_path}: {e}")
                return False
        return True

    return False


def format_directory(
    dir_path: Path, spacing: int = 1, check: bool = False
) -> tuple[list[Path], list[Path]]:
    """Recursively find all markdown files in dir_path and format them.

    Returns a tuple of (modified_files, unchanged_files).
    """
    from tools.common import get_target_files

    modified: list[Path] = []
    unchanged: list[Path] = []

    for path in get_target_files(dir_path):
        has_changed = format_file(path, spacing=spacing, check=check)
        if has_changed:
            modified.append(path)
        else:
            unchanged.append(path)

    return modified, unchanged
