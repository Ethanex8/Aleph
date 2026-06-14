"""Aleph Tools — centralized CLI for Aleph development utilities.

Usage::

    python -m tools <subcommand>
"""

import argparse
import sys
from pathlib import Path

from tools.verifier.verifier import verify_book


def _find_manifest(start_path: Path) -> Path | None:
    """Search for Manifest.md starting from start_path and walking up to the root, or check default 'book' directory."""
    curr = start_path.resolve()
    if curr.is_file():
        curr = curr.parent
    while True:
        candidate = curr / "Manifest.md"
        if candidate.exists():
            return candidate
        parent = curr.parent
        if parent == curr:
            break
        curr = parent

    default_candidate = Path("book/Manifest.md").resolve()
    if default_candidate.exists():
        return default_candidate
    return None


def _setup_stdout() -> None:
    """Ensure stdout can handle Unicode (formula symbols like ∀, ∃, ∈)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    """Root entry point for Aleph tools.

    Dispatches to various subcommands.
    """
    _setup_stdout()

    parser = argparse.ArgumentParser(
        prog="aleph-tools",
        description="Aleph development and verification tools.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # verify subcommand
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify the mathematical book for logical consistency.",
    )
    verify_parser.add_argument(
        "path",
        nargs="?",
        default="book",
        help="File or directory to verify (default: 'book')",
    )

    # format subcommand
    format_parser = subparsers.add_parser(
        "format",
        help="Format the mathematical book or a specific file.",
    )
    format_parser.add_argument(
        "path",
        nargs="?",
        default="book",
        help="File or directory to format (default: 'book')",
    )
    format_parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting without modifying files.",
    )
    format_parser.add_argument(
        "--spacing",
        type=int,
        default=1,
        help="Number of spaces before justifications (default: 1).",
    )

    args = parser.parse_args()

    if args.subcommand == "verify":
        from tools.common import get_target_files

        target = Path(args.path)
        if not target.exists():
            print(f"Error: Path '{args.path}' does not exist.")
            sys.exit(1)

        manifest_path = _find_manifest(target)
        if manifest_path is None:
            print(f"Error: No Manifest.md found for path '{args.path}'")
            sys.exit(1)

        target_files = get_target_files(target)
        if not target_files:
            print(f"Error: No markdown files found to verify at '{args.path}'")
            sys.exit(1)

        success = verify_book(manifest_path, target_files=target_files)
        sys.exit(0 if success else 1)
    elif args.subcommand == "format":
        from tools.formatter import format_directory, format_file

        target_path = Path(args.path)
        if not target_path.exists():
            print(f"Error: Path '{args.path}' does not exist.")
            sys.exit(1)

        if target_path.is_file():
            changed = format_file(target_path, spacing=args.spacing, check=args.check)
            if changed:
                if args.check:
                    print(f"[FAIL] {target_path} needs formatting.")
                    sys.exit(1)
                else:
                    print(f"[FORMATTED] {target_path}")
            else:
                if args.check:
                    print(f"[PASS] {target_path} is correctly formatted.")
                else:
                    print(f"[UNCHANGED] {target_path}")
            sys.exit(0)
        else:
            modified, unchanged = format_directory(
                target_path, spacing=args.spacing, check=args.check
            )
            if args.check:
                if modified:
                    print("\nThe following files need formatting:")
                    for p in modified:
                        print(f"  {p}")
                    sys.exit(1)
                else:
                    print("\nAll files are correctly formatted.")
                    sys.exit(0)
            else:
                if modified:
                    print("\nFormatted files:")
                    for p in modified:
                        print(f"  {p}")
                print(f"\nDone: formatted {len(modified)} files, {len(unchanged)} files unchanged.")
                sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
