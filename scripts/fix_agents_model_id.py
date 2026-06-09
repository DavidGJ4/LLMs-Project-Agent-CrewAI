"""Ensure agents YAML uses NVIDIA-valid model id (minimax-m2.7, not minimax-m2)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

VALID = "openai/minimaxai/minimax-m2.7"
BAD = re.compile(r"openai/minimaxai/minimax-m2(?!\.7)")


def fix_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text, n = BAD.subn(VALID, text)
    if n:
        path.write_text(new_text, encoding="utf-8")
        print(f"Fixed {n} llm line(s) in {path}")
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    paths = [Path(p) for p in (argv or sys.argv[1:])]
    if not paths:
        paths = [
            root / "config" / "agents.yaml",
            root / "lab_submission" / "best_program.yaml",
            root / "config" / "openevolve_output" / "best" / "best_program.yaml",
        ]
    changed = any(fix_file(p) for p in paths if p.exists())
    return 0 if changed or not paths else 0


if __name__ == "__main__":
    raise SystemExit(main())
