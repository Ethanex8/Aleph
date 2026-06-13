"""Manifest Loader.

Loads ``Manifest.md``, resolves qualified imports against
declared exports, derives the dependency graph, validates completeness,
and produces a topologically sorted execution order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from graphlib import CycleError as GraphCycleError
from graphlib import TopologicalSorter
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.context import ProofContext

import re

import yaml

from tools.verifier.section import SectionName


class ManifestError(Exception):
    """Raised for manifest-related errors (cycles, missing files, bad YAML)."""

    pass


@dataclass
class SectionManifest:
    """Metadata for a single section in the manifest."""

    name: SectionName  # e.g. SectionName("SetTheory.Extensionality")
    imports: list[
        tuple[str, str]
    ]  # qualified_name, local_name: [("SetTheory.Axioms.Pairing", "Pairing")]
    exports: list[str]  # bare: ["Pairing", "Union"]


@dataclass
class CachedSymbol:
    """A single cached mathematical symbol with its category and logical value."""

    category: str  # "axiom", "schema", "definition", "constant", "operation", "theorem"
    value: Any


@dataclass
class Manifest:
    """Complete manifest information returned by ``load_manifest``."""

    order: list[SectionName]  # topologically sorted section names
    sections: dict[SectionName, SectionManifest]  # name → section info
    book_dir: Path
    export_index: dict[str, SectionName]
    prefix_to_name: dict[str, SectionName]

    # Global cache for verified symbols: qualified_name -> CachedSymbol
    cache: dict[str, CachedSymbol] = field(default_factory=dict)

    loaded_sections: set[SectionName] = field(default_factory=set)

    @classmethod
    def _read_yaml(cls, manifest_path: Path) -> dict[str, Any]:
        """Read the manifest file, extracting the YAML manifest data.

        If the file has a `.md` extension, extracts the YAML block inside ` ```yaml ` fences.
        Otherwise, parses the file directly as YAML.
        """
        text = manifest_path.read_text(encoding="utf-8")

        if manifest_path.suffix == ".md":
            data: dict[str, list[dict[str, str]]] = {"sections": []}
            # Match yml or yaml code blocks in markdown
            pattern = re.compile(r"^```(?:yaml|yml)\n(.*?)\n```", re.MULTILINE | re.DOTALL)
            blocks = pattern.findall(text)

            if not blocks:
                raise ManifestError(f"No yaml code block found in manifest: {manifest_path}")

            for block in blocks:
                parsed = yaml.safe_load(block)
                if (
                    parsed
                    and isinstance(parsed, dict)
                    and "sections" in parsed
                    and isinstance(parsed["sections"], list)
                ):
                    data["sections"].extend(parsed["sections"])
        else:
            data = yaml.safe_load(text)

        # Validate that we successfully loaded a sections list
        if not isinstance(data, dict) or "sections" not in data:
            raise ManifestError("Malformed manifest: expected a dict with a 'sections' key")
        return data

    @classmethod
    def _parse_sections(
        cls, sections_list: list[Any], book_dir: Path
    ) -> dict[SectionName, SectionManifest]:
        """Parse a raw sections list from YAML into a dictionary of SectionManifest objects.

        Validates syntax, files, and imports.
        """
        if not isinstance(sections_list, list):
            raise ManifestError("Malformed manifest: 'sections' must be a list")

        sections: dict[SectionName, SectionManifest] = {}
        for entry in sections_list:
            if not isinstance(entry, dict) or "name" not in entry:
                raise ManifestError(
                    f"Malformed section entry: expected dict with 'name', got {entry}"
                )

            section_name = SectionName(entry["name"])
            imports_raw = entry.get("imports", [])
            exports = entry.get("exports", [])

            if not isinstance(imports_raw, list):
                raise ManifestError(f"Section '{section_name}': 'imports' must be a list")

            imports: list[tuple[str, str]] = []
            for imp in imports_raw:
                if not isinstance(imp, str):
                    raise ManifestError(f"Section '{section_name}': import must be a string")
                parts = imp.split(" as ")
                if len(parts) == 2:
                    # Handle 'ImportName as AliasName' syntax
                    qualified_name = parts[0].strip()
                    local_name = parts[1].strip()
                elif len(parts) == 1:
                    # Handle standard 'ImportName' syntax (local name inferred from last segment)
                    qualified_name = imp.strip()
                    try:
                        _, local_name = SectionName.parse_qualified_import(qualified_name)
                    except ValueError:
                        raise ManifestError(
                            f"Section '{section_name}': invalid import '{qualified_name}' — "
                            f"expected format 'Section.Path.Identifier'"
                        ) from None
                else:
                    raise ManifestError(f"Section '{section_name}': invalid import syntax '{imp}'")
                imports.append((qualified_name, local_name))
            if not isinstance(exports, list):
                raise ManifestError(f"Section '{section_name}': 'exports' must be a list")

            # Validate that the actual section file exists on disk
            full_path = book_dir / section_name.to_path()
            if not full_path.exists():
                raise ManifestError(f"Section file not found: {full_path}")

            sections[section_name] = SectionManifest(
                name=section_name,
                imports=imports,
                exports=exports,
            )
        return sections

    @classmethod
    def _build_export_index(
        cls, sections: dict[SectionName, SectionManifest]
    ) -> tuple[dict[str, SectionName], dict[str, SectionName]]:
        """Build lookup maps for exports.

        Returns a tuple of:
        1. export_index: mapping from qualified export name to the SectionName that defines it.
        2. prefix_to_name: mapping from section qualified prefixes to their SectionName values.
        """
        export_index: dict[str, SectionName] = {}
        prefix_to_name: dict[str, SectionName] = {}

        for sec_name, sec in sections.items():
            prefix_to_name[sec.name.name] = sec_name

            # Ensure no two sections export the exact same qualified symbol
            for export_name in sec.exports:
                qualified_export = f"{sec.name.name}.{export_name}"
                if qualified_export in export_index:
                    raise ManifestError(
                        f"Duplicate export '{qualified_export}': declared by both "
                        f"'{export_index[qualified_export]}' and '{sec_name}'"
                    )
                export_index[qualified_export] = sec_name

        return export_index, prefix_to_name

    @classmethod
    def _build_dependency_graph(
        cls,
        sections: dict[SectionName, SectionManifest],
        export_index: dict[str, SectionName],
        prefix_to_name: dict[str, SectionName],
    ) -> list[SectionName]:
        """Resolve each section's qualified imports to their defining exporter section.

        Constructs a dependency graph, checks for cycles, and returns a topologically sorted
        section list.
        """
        # graph: maps each SectionName to the set of SectionNames it depends on
        graph: dict[SectionName, set[SectionName]] = {name: set() for name in sections}

        for sec_name, sec in sections.items():
            for qualified_import, _ in sec.imports:
                try:
                    import_prefix, import_id = SectionName.parse_qualified_import(qualified_import)
                except ValueError:
                    raise ManifestError(
                        f"Section '{sec_name}': invalid import '{qualified_import}' — "
                        f"expected format 'Section.Path.Identifier'"
                    ) from None

                # Ensure the imported qualified name actually exists in the exported symbols list
                if qualified_import not in export_index:
                    if import_id == "*":
                        if import_prefix in prefix_to_name:
                            exporter_name = prefix_to_name[import_prefix]
                            if exporter_name != sec_name:
                                graph[sec_name].add(exporter_name)
                            continue
                        else:
                            raise ManifestError(
                                f"Section '{sec_name}': import '{qualified_import}' references "
                                f"unknown section '{import_prefix}'"
                            )

                    if import_prefix in prefix_to_name:
                        target_name = prefix_to_name[import_prefix]
                        available = sections[target_name].exports
                        raise ManifestError(
                            f"Section '{sec_name}': import '{qualified_import}' not found. "
                            f"Section '{import_prefix}' exports: {available}"
                        )
                    else:
                        raise ManifestError(
                            f"Section '{sec_name}': import '{qualified_import}' references "
                            f"unknown section '{import_prefix}'"
                        )

                exporter_name = export_index[qualified_import]

                # If a section imports from itself, ignore to avoid trivial cycle errors
                if exporter_name != sec_name:
                    graph[sec_name].add(exporter_name)

        # Perform topological sort on the graph using standard library TopologicalSorter
        try:
            sorter = TopologicalSorter(graph)
            order = list(sorter.static_order())
        except GraphCycleError as e:
            raise ManifestError(f"Dependency cycle detected: {e}") from e

        return order

    @classmethod
    def load(cls, manifest_path: Path) -> Manifest:
        """Load the book's manifest and construct the dependency graph.

        Parses the `Manifest.md` manifest, resolves qualified imports against
        declared exports across all sections, and performs a topological sort
        to determine the safe verification order.
        """
        manifest_path = Path(manifest_path)
        if not manifest_path.exists():
            raise ManifestError(f"Manifest file not found: {manifest_path}")

        data = cls._read_yaml(manifest_path)
        book_dir = manifest_path.parent

        sections = cls._parse_sections(data["sections"], book_dir)
        export_index, prefix_to_name = cls._build_export_index(sections)
        order = cls._build_dependency_graph(sections, export_index, prefix_to_name)

        return cls(
            order=order,
            sections=sections,
            book_dir=book_dir,
            export_index=export_index,
            prefix_to_name=prefix_to_name,
        )

    def ensure_section_loaded(self, sec_name: SectionName) -> None:
        """Ensure that the symbols from a given section are loaded into the global registries.

        If not already loaded, it parses the section file and populates the cache.
        """
        if sec_name in self.loaded_sections:
            return

        # Avoid circular imports by importing parser tools here
        from tools.parser.ast_nodes import (
            AxiomDecl,
            ConstantDecl,
            DefinitionDecl,
            ForAll,
            OperationDecl,
            SchemaDecl,
            TheoremDecl,
        )
        from tools.parser.extractor import extract_and_combine_fol_blocks_from_file
        from tools.parser.fol_parser import parse_fol

        full_path = self.book_dir / sec_name.to_path()
        try:
            combined_source, _ = extract_and_combine_fol_blocks_from_file(full_path)
        except Exception:
            # If we can't read the file, we can't load it.
            # In verify_manifest, this will be caught later, but here we just stop.
            return

        if not combined_source.strip():
            self.loaded_sections.add(sec_name)
            return

        try:
            declarations = parse_fol(combined_source)
        except Exception:
            # If parsing fails, we skip lazy loading for this file.
            return

        prefix = sec_name.name
        for decl in declarations:
            qualified_name = f"{prefix}.{decl.name}"
            if isinstance(decl, AxiomDecl):
                self.cache[qualified_name] = CachedSymbol("axiom", decl.formula)
            elif isinstance(decl, SchemaDecl):
                self.cache[qualified_name] = CachedSymbol("schema", decl)
            elif isinstance(decl, DefinitionDecl):
                self.cache[qualified_name] = CachedSymbol("definition", decl.formula)
            elif isinstance(decl, ConstantDecl):
                self.cache[qualified_name] = CachedSymbol("constant", decl.formula)
            elif isinstance(decl, OperationDecl):
                op_formula = decl.formula
                for p in reversed(decl.params):
                    op_formula = ForAll(variable=p, body=op_formula)
                self.cache[qualified_name] = CachedSymbol("operation", op_formula)
            elif isinstance(decl, TheoremDecl):
                self.cache[qualified_name] = CachedSymbol("theorem", decl.formula)

        self.loaded_sections.add(sec_name)

    def populate_context_from_imports(
        self, sec_info: SectionManifest, ctx: ProofContext
    ) -> tuple[bool, str | None]:
        """Populate a file's fresh ProofContext with imported symbols from the global registries.

        Validates that imports exist and do not cause local name collisions.
        """
        expanded_imports = []
        for qualified_import, local_name in sec_info.imports:
            if local_name == "*":
                prefix = qualified_import[:-2]  # removes ".*"
                # Lazy load the section if it's not already in cache
                if prefix in self.prefix_to_name:
                    self.ensure_section_loaded(self.prefix_to_name[prefix])

                for key, _symbol in self.cache.items():
                    if key.startswith(f"{prefix}."):
                        item_local = key.split(".")[-1]
                        if (key, item_local) not in expanded_imports:
                            expanded_imports.append((key, item_local))
            else:
                # Lazy load the section if the specific symbol is not in cache
                if qualified_import in self.export_index:
                    self.ensure_section_loaded(self.export_index[qualified_import])

                expanded_imports.append((qualified_import, local_name))

        for qualified_import, local_name in expanded_imports:
            # Check for collision on local_name
            if (
                local_name in ctx.axioms
                or local_name in ctx.schemas
                or local_name in ctx.definitions
                or local_name in ctx.constants
                or local_name in ctx.operations
                or local_name in ctx.proven_theorems
            ):
                return (
                    False,
                    f"Import collision: local name '{local_name}' is already imported or defined.",
                )

            if qualified_import not in self.cache:
                return False, f"Import '{qualified_import}' not found in global registry."

            symbol = self.cache[qualified_import]

            # Dispatch based on category to ProofContext registries
            if symbol.category == "axiom":
                ctx.axioms[local_name] = symbol.value
                ctx.axioms[qualified_import] = symbol.value
            elif symbol.category == "schema":
                ctx.schemas[local_name] = symbol.value
                ctx.schemas[qualified_import] = symbol.value
            elif symbol.category == "definition":
                ctx.definitions[local_name] = symbol.value
                ctx.definitions[qualified_import] = symbol.value
            elif symbol.category == "constant":
                ctx.constants[local_name] = symbol.value
                ctx.constants[qualified_import] = symbol.value
            elif symbol.category == "operation":
                ctx.operations[local_name] = symbol.value
                ctx.operations[qualified_import] = symbol.value
            elif symbol.category == "theorem":
                ctx.proven_theorems[local_name] = symbol.value
                ctx.proven_theorems[qualified_import] = symbol.value
            else:
                return (
                    False,
                    f"Unknown symbol category '{symbol.category}' for '{qualified_import}'.",
                )

        return True, None

    def record_global_exports(
        self, sec_info: SectionManifest, actual_exports: list[str], ctx: ProofContext
    ) -> None:
        """Record newly verified symbols into the global registries.

        Symbols are recorded under their qualified names (prefix.symbol_name), making them available
        for other sections to import.
        """
        prefix = sec_info.name.name

        # Helper to avoid repeating prefix concatenation
        def cache_item(name: str, category: str, source_dict: dict[str, Any]) -> None:
            self.cache[f"{prefix}.{name}"] = CachedSymbol(category, source_dict[name])

        for name in actual_exports:
            if name in ctx.axioms:
                cache_item(name, "axiom", ctx.axioms)
            elif name in ctx.schemas:
                cache_item(name, "schema", ctx.schemas)
            elif name in ctx.definitions:
                cache_item(name, "definition", ctx.definitions)
            elif name in ctx.constants:
                cache_item(name, "constant", ctx.constants)
            elif name in ctx.operations:
                cache_item(name, "operation", ctx.operations)
            elif name in ctx.proven_theorems:
                cache_item(name, "theorem", ctx.proven_theorems)

        self.loaded_sections.add(sec_info.name)


def validate_completeness(
    book_dir: str | Path, sections: dict[SectionName, SectionManifest]
) -> None:
    """Walk the book directory and ensure every ``.md`` file is registered in ``Manifest.md``.

    Raises ``ManifestError`` if any orphaned files are found.
    """
    book_dir = Path(book_dir)
    registered_names = set(sections.keys())
    orphaned: list[str] = []

    for md_file in book_dir.rglob("*.md"):
        relative = str(md_file.relative_to(book_dir)).replace("\\", "/")
        if relative == "Manifest.md":
            continue
        file_name = SectionName.from_path(relative)
        if file_name not in registered_names:
            orphaned.append(str(file_name))

    if orphaned:
        raise ManifestError(f"Orphaned .md files not registered in manifest: {orphaned}")


def validate_exports(section_info: SectionManifest, actual_exports: list[str]) -> None:
    """Compare declared exports against actual verification results.

    Raises ``ManifestError`` on mismatch.
    """
    actual = set(actual_exports)
    declared = set(section_info.exports)

    missing = declared - actual
    undeclared = actual - declared

    errors: list[str] = []
    if missing:
        errors.append(f"Declared exports not produced: {sorted(missing)}")
    if undeclared:
        errors.append(f"Undeclared exports produced: {sorted(undeclared)}")

    if errors:
        raise ManifestError(f"Export mismatch for '{section_info.name}': " + "; ".join(errors))
