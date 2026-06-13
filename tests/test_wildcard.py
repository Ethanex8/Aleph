# Unit tests for wildcard imports.
from pathlib import Path
from typing import ClassVar

import pytest

from tools.context import ProofContext
from tools.verifier.manifest import CachedSymbol, Manifest
from tools.verifier.section import SectionName


@pytest.fixture
def book_dir_with_wildcard(tmp_path):
    """Create a temporary book directory with some files for wildcard testing."""
    sets = tmp_path / "SetTheory"
    sets.mkdir()
    (sets / "Axioms.md").write_text("# Axioms\n", encoding="utf-8")
    (sets / "Subset.md").write_text("# Subset\n", encoding="utf-8")

    return tmp_path


def test_wildcard_manifest_resolution(book_dir_with_wildcard):
    manifest = book_dir_with_wildcard / "Manifest.md"
    manifest.write_text(
        "```yaml\nsections:\n"
        "  - name: SetTheory.Axioms\n"
        "    imports: []\n"
        "    exports: [Axiom1, Axiom2]\n"
        "  - name: SetTheory.Subset\n"
        "    imports:\n"
        "      - SetTheory.Axioms.*\n"
        "    exports: []\n```\n",
        encoding="utf-8",
    )
    manifest = Manifest.load(manifest)
    assert isinstance(manifest, Manifest)
    assert manifest.order.index(SectionName("SetTheory.Axioms")) < manifest.order.index(
        SectionName("SetTheory.Subset")
    )


def test_wildcard_context_population():
    # Setup global registries with dummy formulas
    manifest = Manifest(
        order=[], sections={}, book_dir=Path("."), export_index={}, prefix_to_name={}
    )
    manifest.cache = {
        "SetTheory.Axioms.Axiom1": CachedSymbol("axiom", "formula1"),
        "SetTheory.Axioms.Axiom2": CachedSymbol("axiom", "formula2"),
    }

    class DummySecInfo:
        imports: ClassVar[list[tuple[str, str]]] = [("SetTheory.Axioms.*", "*")]

    ctx = ProofContext()
    success, _err = manifest.populate_context_from_imports(
        DummySecInfo(),
        ctx,
    )
    assert success
    assert ctx.axioms["Axiom1"] == "formula1"
    assert ctx.axioms["Axiom2"] == "formula2"
    assert ctx.axioms["SetTheory.Axioms.Axiom1"] == "formula1"
    assert ctx.axioms["SetTheory.Axioms.Axiom2"] == "formula2"
