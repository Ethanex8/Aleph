"""Markdown FOL Extractor — extracts ``fol`` fenced code blocks from Markdown.

Returns raw text content with line offsets for error reporting.
"""

from __future__ import annotations

from pathlib import Path


def extract_and_combine_fol_blocks(markdown_text: str) -> tuple[str, list[int]]:
    """Extract all ``fol`` fenced code blocks and combine them into a single string.

    Returns a tuple ``(combined_fol_source, line_map)`` where:
    - ``combined_fol_source`` is the concatenated content of all blocks separated by newlines.
    - ``line_map`` is a list mapping each 0-indexed line of the combined string to its
      corresponding 1-based line number in the original Markdown text.
    """
    from tools.common import iter_fol_lines

    combined_lines: list[str] = []
    line_map: list[int] = []

    for orig_line_num, line, is_inside_fol, _ in iter_fol_lines(markdown_text):
        if is_inside_fol:
            combined_lines.append(line)
            line_map.append(orig_line_num)

    combined_fol_source = "\n".join(combined_lines) + ("\n" if combined_lines else "")
    return combined_fol_source, line_map


def extract_and_combine_fol_blocks_from_file(file_path: str | Path) -> tuple[str, list[int]]:
    """Read a Markdown file and extract and combine all ``fol`` code blocks.

    Returns a tuple ``(combined_fol_source, line_map)``.
    """
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    return extract_and_combine_fol_blocks(text)
