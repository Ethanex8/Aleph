"""Section representation encapsulating logical section source, line mapping, and metadata.

Centralises all conversions between dot-separated logical names
(``SetTheory.Extensionality``) and filesystem paths
(``SetTheory/Extensionality.md``), eliminating scattered path
manipulation logic throughout the verifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SectionName:
    """A dot-separated logical section name, e.g. ``'SetTheory.Extensionality'``.

    Frozen and hashable — safe for use as dict keys and in sets.
    """

    name: str  # e.g. "SetTheory.Extensionality"

    @staticmethod
    def from_path(path: str) -> SectionName:
        r"""Build a ``SectionName`` from a relative file path.

        Example:
            ``"SetTheory/Extensionality.md"`` → ``SectionName("SetTheory.Extensionality")``

        Args:
            path: A relative filesystem path (e.g., from `rglob`).

        Returns:
            A `SectionName` instance corresponding to the logical path.

        Note:
            Handles both ``/`` and ``\\`` separators and strips the ``.md``
            extension.
        """
        # Normalise separators
        normalised = path.replace("\\", "/")
        # Strip .md extension
        if normalised.endswith(".md"):
            normalised = normalised[:-3]
        # Replace path separators with dots
        return SectionName(name=normalised.replace("/", "."))

    @staticmethod
    def parse_qualified_import(qualified_name: str) -> tuple[str, str]:
        """Parse a fully qualified import into (section_prefix, identifier).

        ``"SetTheory.Axioms.Pairing"`` → ``("SetTheory.Axioms", "Pairing")``

        Raises ``ValueError`` if the name has fewer than 2 segments.
        """
        last_dot = qualified_name.rfind(".")
        if last_dot == -1:
            raise ValueError(
                f"Invalid qualified import '{qualified_name}': "
                f"expected format 'Section.Path.Identifier'"
            )
        return qualified_name[:last_dot], qualified_name[last_dot + 1 :]

    def to_path(self) -> str:
        """Convert the logical section name back into a relative filesystem path.

        Example:
            ``SectionName("SetTheory.Extensionality")`` → ``"SetTheory/Extensionality.md"``

        Returns:
            A POSIX-style path string with the ``.md`` suffix.
        """
        return self.name.replace(".", "/") + ".md"

    def __str__(self) -> str:
        """Return the logical section name."""
        return self.name

    def __repr__(self) -> str:
        """Return a string representation of the SectionName."""
        return f"SectionName({self.name!r})"


@dataclass
class Section:
    """Represents a mathematical section loaded for verification.

    Contains the logical name, source code (combined from logical blocks),
    line mapping, and the optional physical path.
    """

    name: SectionName
    source: str
    line_map: list[int]
    path: Path | None = None

    @classmethod
    def from_file(cls, name: SectionName, file_path: Path) -> Section:
        """Load a section from a file, extracting its logical first-order logic blocks."""
        from tools.parser.extractor import extract_and_combine_fol_blocks_from_file

        combined_source, line_map = extract_and_combine_fol_blocks_from_file(file_path)
        return cls(name=name, source=combined_source, line_map=line_map, path=file_path)
