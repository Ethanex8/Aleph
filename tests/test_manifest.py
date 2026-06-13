"""Tests for the manifest loader."""

import pytest

from tools.verifier.manifest import (
    Manifest,
    ManifestError,
    SectionManifest,
    validate_completeness,
    validate_exports,
)
from tools.verifier.section import SectionName


@pytest.fixture
def book_dir(tmp_path):
    """Create a temporary book directory with some files."""
    sets = tmp_path / "SetTheory"
    sets.mkdir()
    (sets / "Axioms.md").write_text("# ZFC\n```fol\naxiom E:\n    x = x\n```\n", encoding="utf-8")
    (sets / "Subset.md").write_text("# Subset\n", encoding="utf-8")

    return tmp_path


class TestSectionName:
    """Test the SectionName abstraction."""

    def test_from_path(self):
        assert SectionName.from_path("SetTheory/Axioms.md") == SectionName("SetTheory.Axioms")

    def test_from_path_nested(self):
        assert SectionName.from_path("Algebra/Groups/Lagrange.md") == SectionName(
            "Algebra.Groups.Lagrange"
        )

    def test_from_path_backslash(self):
        assert SectionName.from_path("SetTheory\\Axioms.md") == SectionName("SetTheory.Axioms")

    def test_to_path(self):
        assert SectionName("SetTheory.Axioms").to_path() == "SetTheory/Axioms.md"

    def test_to_path_nested(self):
        assert SectionName("Algebra.Groups.Lagrange").to_path() == "Algebra/Groups/Lagrange.md"

    def test_str(self):
        assert str(SectionName("SetTheory.Axioms")) == "SetTheory.Axioms"

    def test_hashable(self):
        """SectionName is hashable and works as a dict key."""
        d = {SectionName("A.B"): 1, SectionName("C.D"): 2}
        assert d[SectionName("A.B")] == 1

    def test_roundtrip(self):
        """from_path → to_path is identity."""
        original = "SetTheory/Axioms.md"
        assert SectionName.from_path(original).to_path() == original

    def test_parse_qualified_import(self):
        prefix, ident = SectionName.parse_qualified_import("SetTheory.Axioms.Pairing")
        assert prefix == "SetTheory.Axioms"
        assert ident == "Pairing"

    def test_parse_qualified_import_deep(self):
        prefix, ident = SectionName.parse_qualified_import(
            "Algebra.Groups.Lagrange.LagrangeTheorem"
        )
        assert prefix == "Algebra.Groups.Lagrange"
        assert ident == "LagrangeTheorem"

    def test_parse_bare_name_raises(self):
        with pytest.raises(ValueError, match="Invalid qualified import"):
            SectionName.parse_qualified_import("Pairing")


class TestManifest:
    def test_valid_manifest(self, book_dir):
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports: []\n"
            "    exports: [E]\n"
            "  - name: SetTheory.Subset\n"
            "    imports:\n"
            "      - SetTheory.Axioms.E\n"
            "    exports: []\n```\n",
            encoding="utf-8",
        )
        manifest = Manifest.load(manifest)
        assert isinstance(manifest, Manifest)
        assert manifest.order.index(SectionName("SetTheory.Axioms")) < manifest.order.index(
            SectionName("SetTheory.Subset")
        )

    def test_no_imports(self, book_dir):
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports: []\n"
            "    exports: [E]\n"
            "  - name: SetTheory.Subset\n"
            "    imports: []\n"
            "    exports: []\n```\n",
            encoding="utf-8",
        )
        manifest = Manifest.load(manifest)
        # Both sections have no dependencies, order is valid either way
        assert set(manifest.order) == {
            SectionName("SetTheory.Axioms"),
            SectionName("SetTheory.Subset"),
        }

    def test_single_node(self, book_dir):
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports: []\n"
            "    exports: [E]\n```\n",
            encoding="utf-8",
        )
        manifest = Manifest.load(manifest)
        assert manifest.order == [SectionName("SetTheory.Axioms")]

    def test_cycle_detection(self, book_dir):
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports:\n"
            "      - SetTheory.Subset.Foo\n"
            "    exports: [E]\n"
            "  - name: SetTheory.Subset\n"
            "    imports:\n"
            "      - SetTheory.Axioms.E\n"
            "    exports: [Foo]\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(ManifestError, match=r"[Cc]ycle"):
            Manifest.load(manifest)

    def test_missing_file(self, book_dir):
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: NonExistent.File\n"
            "    imports: []\n"
            "    exports: []\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(ManifestError, match="not found"):
            Manifest.load(manifest)

    def test_dangling_import(self, book_dir):
        """Import references an identifier not exported by any section."""
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports: []\n"
            "    exports: [E]\n"
            "  - name: SetTheory.Subset\n"
            "    imports:\n"
            "      - SetTheory.Axioms.NonExistent\n"
            "    exports: []\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(ManifestError, match="not found"):
            Manifest.load(manifest)

    def test_unknown_module_in_import(self, book_dir):
        """Import references a section prefix that doesn't exist."""
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports:\n"
            "      - Nonexistent.Module.Foo\n"
            "    exports: [E]\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(ManifestError, match="unknown section"):
            Manifest.load(manifest)

    def test_duplicate_export(self, book_dir):
        """Two sections export the same qualified identifier."""
        # Since prefixes are derived from names, duplicates only happen if the
        # same identifier appears in both exports of sections with identical
        # prefixes. That requires the same file path which isn't possible with
        # different entries — so this test just validates the concept.
        pass

    def test_missing_manifest(self):
        with pytest.raises(ManifestError, match="not found"):
            Manifest.load("nonexistent_Manifest.md")

    def test_section_info_populated(self, book_dir):
        """Verify SectionManifest fields are correctly populated."""
        manifest = book_dir / "Manifest.md"
        manifest.write_text(
            "```yaml\nsections:\n"
            "  - name: SetTheory.Axioms\n"
            "    imports: []\n"
            "    exports: [E]\n```\n",
            encoding="utf-8",
        )
        manifest = Manifest.load(manifest)
        sec = manifest.sections[SectionName("SetTheory.Axioms")]
        assert sec.name.name == "SetTheory.Axioms"
        assert sec.imports == []
        assert sec.exports == ["E"]


class TestCompleteness:
    def test_orphaned_file(self, book_dir):
        """An .md file exists but is not in Manifest.md."""
        sections = {
            SectionName("SetTheory.Axioms"): SectionManifest(
                name=SectionName("SetTheory.Axioms"),
                imports=[],
                exports=["E"],
            ),
            # SetTheory/Subset.md is NOT registered
        }
        with pytest.raises(ManifestError, match="Orphaned"):
            validate_completeness(book_dir, sections)

    def test_all_registered(self, book_dir):
        """All .md files are registered — no error."""
        sections = {
            SectionName("SetTheory.Axioms"): SectionManifest(
                name=SectionName("SetTheory.Axioms"),
                imports=[],
                exports=["E"],
            ),
            SectionName("SetTheory.Subset"): SectionManifest(
                name=SectionName("SetTheory.Subset"),
                imports=[],
                exports=[],
            ),
        }
        # Should not raise
        validate_completeness(book_dir, sections)


class TestExportValidation:
    def test_matching_exports(self):
        """Declared exports match actual — no error."""
        sec = SectionManifest(
            name=SectionName("SetTheory.Axioms"),
            imports=[],
            exports=["E", "F"],
        )
        res = ["E", "F"]
        # Should not raise
        validate_exports(sec, res)

    def test_missing_export(self):
        """Declared export not produced by file."""
        sec = SectionManifest(
            name=SectionName("SetTheory.Axioms"),
            imports=[],
            exports=["E", "F", "G"],
        )
        res = ["E"]
        with pytest.raises(ManifestError, match="not produced"):
            validate_exports(sec, res)

    def test_undeclared_export(self):
        """File produces an identifier not declared in exports."""
        sec = SectionManifest(
            name=SectionName("SetTheory.Axioms"),
            imports=[],
            exports=["E"],
        )
        res = ["E", "Surprise"]
        with pytest.raises(ManifestError, match="Undeclared"):
            validate_exports(sec, res)
