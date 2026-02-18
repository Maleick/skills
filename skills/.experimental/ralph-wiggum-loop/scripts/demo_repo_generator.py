#!/usr/bin/env python3
"""Create an offline demo repository with a deterministic failing test."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CALCULATOR_PY = '''"""Demo target for Ralph loop."""


def add(a: int, b: int) -> int:
    """Return sum of two integers."""
    return a - b  # RALPH_FIXME:addition_bug
'''

TEST_PY = '''import unittest

from calculator import add


class CalculatorTests(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
'''

README_MD = '''# Ralph Demo Repo

This repository is intentionally broken.

- `calculator.py` contains a known bug marker: `RALPH_FIXME:addition_bug`
- `python3 -m unittest -q` fails before repair

Use it with `scripts/ralph_loop.py` for an offline end-to-end demo.
'''


def generate_demo_repo(output_dir: Path, force: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise SystemExit(
            f"Refusing to overwrite non-empty directory: {output_dir} (use --force)"
        )

    if output_dir.exists() and force:
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "calculator.py").write_text(CALCULATOR_PY, encoding="utf-8")
    (output_dir / "test_calculator.py").write_text(TEST_PY, encoding="utf-8")
    (output_dir / "README.md").write_text(README_MD, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="demo_repo",
        help="Output directory for the demo repository (default: ./demo_repo)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output directory if it already exists",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output).expanduser().resolve()
    generate_demo_repo(output_dir, force=args.force)

    print(f"Demo repo ready: {output_dir}")
    print("Baseline command (expected to fail):")
    print(f"  cd {output_dir} && python3 -m unittest -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
