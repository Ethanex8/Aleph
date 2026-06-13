"""End-to-end tests — verify the full pipeline works."""

from pathlib import Path

from tools.context import ProofContext
from tools.verifier.section import Section, SectionName
from tools.verifier.verifier import _verify_section, verify_book

BOOK_DIR = Path(__file__).parent.parent / "book"
TOC_PATH = BOOK_DIR / "Manifest.md"


def _verify_file_helper(file_path: Path, ctx: ProofContext):
    """Helper used to replace the now-removed verify_file for testing."""
    section_name = SectionName.from_path(file_path.name)
    section = Section.from_file(section_name, file_path)
    success, actual_exports = _verify_section(section, ctx)
    return success, actual_exports, ctx


class TestEndToEnd:
    """Verify the full pipeline against the actual book content."""

    def test_verify_full_book(self):
        """The critical test: build the full DAG and verify all files."""
        success = verify_book(TOC_PATH)
        assert success, "Verification failed"

    def test_verify_subset_book(self):
        """Verify we can verify a single file in the book."""
        success = verify_book(TOC_PATH, target_files=[BOOK_DIR / "SetTheory" / "Extensionality.md"])
        assert success

    def test_subset_transitivity_verified(self):
        """Verify SubsetTransitivity is in the proven theorems."""
        success = verify_book(TOC_PATH)
        assert success

    def test_verify_extensionality_subsets_and_empty_set_standalone(self):
        """Verify the files load correctly into the same context sequentially."""
        ctx = ProofContext()
        success1, exports1, ctx = _verify_file_helper(
            BOOK_DIR / "SetTheory" / "Extensionality.md", ctx
        )
        assert success1
        assert "Extensionality" in exports1

        success2, _exports2, ctx = _verify_file_helper(BOOK_DIR / "SetTheory" / "Subset.md", ctx)
        assert success2

        success3, exports3, ctx = _verify_file_helper(BOOK_DIR / "SetTheory" / "EmptySet.md", ctx)

        assert success3
        assert "EmptySetExistence" in exports3
        assert "∅" in exports3
        assert "EmptySetUniqueness" in exports3

    def test_broken_proof_fails(self, tmp_path):
        """A proof with an incorrect step should fail verification."""
        broken_md = tmp_path / "Broken.md"
        broken_md.write_text(
            "```fol\n"
            "theorem BrokenTheorem:\n"
            "    ∀x (x ∈ A ⟹ x ∈ B)\n"
            "proof:\n"
            "    1. Let x be arbitrary                [Hypothesis]\n"
            "        2. Assume x ∈ A                      [Hypothesis]\n"
            "            3. x ∈ B                             [MP 1, 2]\n"
            "        4. ∀x (x ∈ A ⟹ x ∈ B)              [UG 3, x]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(broken_md, ctx)
        assert not success

    def test_undischarged_assumption_fails(self, tmp_path):
        """A proof with an undischarged assumption must fail verification."""
        md = tmp_path / "Undischarged.md"
        md.write_text(
            "```fol\n"
            "theorem UndischargedTheorem:\n"
            "    x ∈ A ∧ ¬(x ∈ A)\n"
            "proof:\n"
            "    1. Assume x ∈ A ∧ ¬(x ∈ A)      [Hypothesis]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(md, ctx)
        assert not success

    def test_leak_discharged_assumption_fails(self, tmp_path):
        """A proof referencing a line that belongs to a closed scope must fail."""
        md = tmp_path / "LeakDischarged.md"
        md.write_text(
            "```fol\n"
            "theorem LeakDischarged:\n"
            "    (x ∈ A ⟹ x ∈ A) ∧ x ∈ A\n"
            "proof:\n"
            "    1. Assume x ∈ A                      [Hypothesis]\n"
            "    2. x ∈ A ⟹ x ∈ A                    [ImplIntro 1, 1]\n"
            "    3. (x ∈ A ⟹ x ∈ A) ∧ x ∈ A          [AndIntro 2, 1]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(md, ctx)
        assert not success

    def test_ug_free_in_assumption_fails(self, tmp_path):
        """UG cannot generalize over a variable free in active assumptions."""
        md = tmp_path / "UgFree.md"
        md.write_text(
            "```fol\n"
            "axiom Reflexivity:\n"
            "    ∀x (x = x)\n\n"
            "theorem GeneralizeFree:\n"
            "    (x ∈ A ⟹ ∀x (x = x))\n"
            "proof:\n"
            "    1. Assume x ∈ A                      [Hypothesis]\n"
            "        2. Let x be arbitrary                [Hypothesis]\n"
            "            3. ∀x (x = x)                        [Axiom Reflexivity]\n"
            "            4. x = x                             [UI 3, x]\n"
            "        5. ∀x (x = x)                        [UG 4, x]\n"
            "    6. x ∈ A ⟹ ∀x (x = x)                [ImplIntro 1, 5]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(md, ctx)
        assert not success

    def test_exists_elim_witness_leak_fails(self, tmp_path):
        """ExistsElim witness variable must not leak into the conclusion."""
        md = tmp_path / "ExistsLeak.md"
        md.write_text(
            "```fol\n"
            "theorem LeakWitness:\n"
            "    (∃x (x ∈ A) ⟹ ∀c (c ∈ A))\n"
            "proof:\n"
            "    1. Assume ∃x (x ∈ A)                 [Hypothesis]\n"
            "        2. Let c be arbitrary                [Hypothesis]\n"
            "            3. Assume c ∈ A                      [Hypothesis]\n"
            "            4. c ∈ A ⟹ c ∈ A                    [ImplIntro 3, 3]\n"
            "        5. c ∈ A                             [ExistsElim 1, 4, c]\n"
            "    6. ∀c (c ∈ A)                        [UG 5, c]\n"
            "7. ∃x (x ∈ A) ⟹ ∀c (c ∈ A)          [ImplIntro 1, 6]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(md, ctx)
        assert not success

    def test_wrong_indentation_fails(self, tmp_path):
        """A proof with incorrect indentation should fail verification."""
        md = tmp_path / "WrongIndent.md"
        md.write_text(
            "```fol\n"
            "theorem WrongIndent:\n"
            "    ∀x (x = x)\n"
            "proof:\n"
            "    1. Let x be arbitrary                [Hypothesis]\n"
            "    2. x = x                             [Hypothesis]\n"
            "    3. ∀x (x = x)                        [UG 2, x]\n"
            "qed\n"
            "```\n",
            encoding="utf-8",
        )
        ctx = ProofContext()
        success, _exports, ctx = _verify_file_helper(md, ctx)
        assert not success

    def test_verification_output(self, capsys):
        """Verify verification produces output."""
        success = verify_book(TOC_PATH)
        assert success
        captured = capsys.readouterr()
        assert "SubsetTransitivity" in captured.out
        assert "[OK]" in captured.out

    def test_verify_section_in_memory(self):
        """Verify we can verify a section completely in memory without files."""
        from tools.verifier.section import SectionName

        source = "axiom Reflexivity:\n    ∀x (x = x)\n"
        section = Section(
            name=SectionName("Test.Reflexivity"),
            source=source,
            line_map=[2, 3],
        )
        ctx = ProofContext()
        success, exports = _verify_section(section, ctx)
        assert success
        assert "Reflexivity" in exports
