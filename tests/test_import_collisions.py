"""Tests for import collision detection and aliasing."""

from pathlib import Path

import yaml

from tools.verifier.verifier import verify_book


def test_import_collision_detected(tmp_path: Path):
    """Test that a name collision raises an error."""
    mod_a = tmp_path / "ModA.md"
    mod_a.write_text("```fol\naxiom Exists:\n    A = A\n```\n", encoding="utf-8")

    mod_b = tmp_path / "ModB.md"
    mod_b.write_text("```fol\naxiom Exists:\n    B = B\n```\n", encoding="utf-8")

    mod_main = tmp_path / "Main.md"
    mod_main.write_text("```fol\naxiom Dummy:\n    C = C\n```\n", encoding="utf-8")

    index = tmp_path / "Manifest.md"
    manifest = {
        "sections": [
            {"name": "ModA", "imports": [], "exports": ["Exists"]},
            {"name": "ModB", "imports": [], "exports": ["Exists"]},
            {"name": "Main", "imports": ["ModA.Exists", "ModB.Exists"], "exports": ["Dummy"]},
        ]
    }
    index.write_text(f"```yaml\n{yaml.dump(manifest)}\n```", encoding="utf-8")

    success = verify_book(index)
    assert not success
    pass


def test_import_aliasing_resolves_collision(tmp_path: Path):
    """Test that using 'as' resolves the collision."""
    mod_a = tmp_path / "ModA.md"
    mod_a.write_text("```fol\naxiom Exists:\n    A = A\n```\n", encoding="utf-8")

    mod_b = tmp_path / "ModB.md"
    mod_b.write_text("```fol\naxiom Exists:\n    B = B\n```\n", encoding="utf-8")

    mod_main = tmp_path / "Main.md"
    # Use the aliased names in a proof
    mod_main.write_text(
        "```fol\n"
        "theorem Test:\n"
        "    A = A ∧ B = B\n"
        "proof:\n"
        "    1. A = A  [Axiom ExistsA]\n"
        "    2. B = B  [Axiom ExistsB]\n"
        "    3. A = A ∧ B = B  [AndIntro 1, 2]\n"
        "qed\n"
        "```\n",
        encoding="utf-8",
    )

    index = tmp_path / "Manifest.md"
    manifest = {
        "sections": [
            {"name": "ModA", "imports": [], "exports": ["Exists"]},
            {"name": "ModB", "imports": [], "exports": ["Exists"]},
            {
                "name": "Main",
                "imports": ["ModA.Exists as ExistsA", "ModB.Exists as ExistsB"],
                "exports": ["Test"],
            },
        ]
    }
    index.write_text(f"```yaml\n{yaml.dump(manifest)}\n```", encoding="utf-8")

    success = verify_book(index)
    assert success


def test_fully_qualified_references(tmp_path: Path):
    """Test that fully qualified references can be used."""
    mod_a = tmp_path / "ModA.md"
    mod_a.write_text("```fol\naxiom Exists:\n    A = A\n```\n", encoding="utf-8")

    mod_main = tmp_path / "Main.md"
    # Use fully qualified name in proof
    mod_main.write_text(
        "```fol\ntheorem Test:\n    A = A\nproof:\n    1. A = A  [Axiom ModA.Exists]\nqed\n```\n",
        encoding="utf-8",
    )

    index = tmp_path / "Manifest.md"
    manifest = {
        "sections": [
            {"name": "ModA", "imports": [], "exports": ["Exists"]},
            {"name": "Main", "imports": ["ModA.Exists"], "exports": ["Test"]},
        ]
    }
    index.write_text(f"```yaml\n{yaml.dump(manifest)}\n```", encoding="utf-8")

    success = verify_book(index)
    assert success
