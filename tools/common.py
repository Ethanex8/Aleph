"""Common utilities for Aleph tools."""

import re
from collections.abc import Generator
from pathlib import Path

OPEN_FENCE_PAT = re.compile(r"^```fol\s*$")
CLOSE_FENCE_PAT = re.compile(r"^```\s*$")


def get_target_files(target_path: Path) -> list[Path]:
    """Recursively find all target markdown files to process.

    Skips hidden files/directories and Manifest.md. If target_path is a file, returns a
    list containing only that file if it's a markdown file.
    """
    if target_path.is_file():
        if target_path.suffix == ".md" and target_path.name != "Manifest.md":
            return [target_path]
        return []

    files: list[Path] = []
    for path in target_path.rglob("*.md"):
        if path.name == "Manifest.md":
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def iter_fol_lines(markdown_text: str) -> Generator[tuple[int, str, bool, str], None, None]:
    """Yields (line_number_1_indexed, stripped_line_text, is_inside_fol, line_ending) for every line."""
    inside_fol = False
    for idx, line in enumerate(markdown_text.splitlines(keepends=True)):
        stripped = line.rstrip("\r\n")
        ending = line[len(stripped) :]

        # Handle fence changes
        if not inside_fol:
            if OPEN_FENCE_PAT.match(stripped):
                inside_fol = True
            yield idx + 1, stripped, False, ending
        else:
            if CLOSE_FENCE_PAT.match(stripped):
                inside_fol = False
                yield idx + 1, stripped, False, ending
            else:
                yield idx + 1, stripped, True, ending
