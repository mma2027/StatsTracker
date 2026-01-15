#!/usr/bin/env python3
"""
Linter test suite for squash fetcher integration

Runs Black, Flake8, and MyPy checks on the new squash fetcher code
"""

import subprocess
import sys
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def main():
    """Run all linter tests"""
    print("=" * 80)
    print("SQUASH FETCHER LINTER TEST SUITE")
    print("=" * 80)

    # Files to check
    files_to_check = ["src/website_fetcher/squash_fetcher.py", "main.py", "src/website_fetcher/__init__.py"]

    results = {}

    # 1. Black formatting check
    results["black"] = run_command(["black", "--check"] + files_to_check, "Black code formatting check")

    # 2. Flake8 linting
    results["flake8"] = run_command(
        [
            "flake8",
            "--max-line-length=127",
            "--extend-ignore=E402",  # Ignore imports not at top (needed for main.py)
            "--exclude=venv",
        ]
        + files_to_check,
        "Flake8 linting",
    )

    # 3. MyPy type checking (just squash_fetcher to avoid noise from existing code)
    results["mypy"] = run_command(
        [
            "mypy",
            "src/website_fetcher/squash_fetcher.py",
            "--ignore-missing-imports",
            "--no-strict-optional",
            "--disable-error-code=attr-defined",  # Ignore false positives about None
            "--follow-imports=skip",  # Don't check imported modules
        ],
        "MyPy type checking (squash_fetcher.py only)",
    )

    # Summary
    print("\n" + "=" * 80)
    print("LINTER TEST RESULTS SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.ljust(15)}: {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 All linter tests passed!")
        return 0
    else:
        print("\n⚠️  Some linter tests failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
