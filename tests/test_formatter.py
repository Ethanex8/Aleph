"""Tests for the FOL block formatter."""

from tools.formatter import format_content, format_file


class TestFormatter:
    """Test FOL formatter functionality."""

    def test_format_content_spacing_one(self):
        content = (
            "# Header\n"
            "```fol\n"
            "theorem Test:\n"
            "    P\n"
            "proof:\n"
            "    1. Assume P        [Hypothesis]\n"
            "    2. P    [Hypothesis]\n"
            "qed\n"
            "```\n"
        )
        formatted, is_changed = format_content(content, spacing=1)
        assert is_changed
        expected = (
            "# Header\n"
            "```fol\n"
            "theorem Test:\n"
            "    P\n"
            "proof:\n"
            "    1. Assume P [Hypothesis]\n"
            "    2. P [Hypothesis]\n"
            "qed\n"
            "```\n"
        )
        assert formatted == expected

    def test_format_content_spacing_custom(self):
        content = "```fol\n    1. Assume P   [Hypothesis]\n```\n"
        formatted, is_changed = format_content(content, spacing=3)
        assert not is_changed
        expected = "```fol\n    1. Assume P   [Hypothesis]\n```\n"
        assert formatted == expected

        # Change to spacing=2
        formatted, is_changed = format_content(content, spacing=2)
        assert is_changed
        expected_2 = "```fol\n    1. Assume P  [Hypothesis]\n```\n"
        assert formatted == expected_2

    def test_no_change_outside_fol(self):
        content = (
            "This is prose 1. Assume P   [Hypothesis]\n"
            "```text\n"
            "1. Assume P      [Hypothesis]\n"
            "```\n"
        )
        formatted, is_changed = format_content(content, spacing=1)
        assert not is_changed
        assert formatted == content

    def test_complex_justifications(self):
        content = (
            "```fol\n"
            "    1. P ∨ Q                             [OrIntro 2, Left]\n"
            "    2. φ(x) ⟹ ψ(y)                    [ImplIntro 3, 4]\n"
            "```\n"
        )
        formatted, is_changed = format_content(content, spacing=1)
        assert is_changed
        expected = (
            "```fol\n    1. P ∨ Q [OrIntro 2, Left]\n    2. φ(x) ⟹ ψ(y) [ImplIntro 3, 4]\n```\n"
        )
        assert formatted == expected

    def test_format_file_check_mode(self, tmp_path):
        test_file = tmp_path / "test.md"
        content = "```fol\n    1. P      [Hypothesis]\n```\n"
        test_file.write_text(content, encoding="utf-8")

        # In check mode, should return True (needs formatting) and not modify file
        needs_formatting = format_file(test_file, spacing=1, check=True)
        assert needs_formatting
        assert test_file.read_text(encoding="utf-8") == content

        # In write mode, should return True (changes written) and modify file
        changes_written = format_file(test_file, spacing=1, check=False)
        assert changes_written
        expected = "```fol\n    1. P [Hypothesis]\n```\n"
        assert test_file.read_text(encoding="utf-8") == expected

        # Running again should return False (already formatted)
        assert not format_file(test_file, spacing=1, check=False)
