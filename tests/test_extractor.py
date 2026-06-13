"""Tests for the Markdown FOL block extractor."""

from tools.parser.extractor import extract_and_combine_fol_blocks


class TestExtractor:
    """Test FOL block extraction from Markdown."""

    def test_combine_blocks_with_line_map(self):
        md = (
            "line 1\n"
            "```fol\n"
            "axiom A:\n"  # Line 3
            "    x = x\n"  # Line 4
            "```\n"
            "some prose\n"
            "```fol\n"
            "theorem T:\n"  # Line 8
            "    x = y\n"  # Line 9
            "qed\n"  # Line 10
            "```\n"
        )
        combined, line_map = extract_and_combine_fol_blocks(md)
        expected = "axiom A:\n    x = x\ntheorem T:\n    x = y\nqed\n"
        assert combined == expected
        # Expected line map corresponds to each line of combined string (5 lines):
        # Line 1 ("axiom A:") -> original line 3
        # Line 2 ("    x = x") -> original line 4
        # Line 3 ("theorem T:") -> original line 8
        # Line 4 ("    x = y") -> original line 9
        # Line 5 ("qed") -> original line 10
        assert line_map == [3, 4, 8, 9, 10]
