"""Recover best_program.yaml after OpenEvolve finishes (fixes Windows cp1252 crash)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.agents_yaml_io import normalize_evolved_agents_yaml

OUTPUT = ROOT / "config" / "openevolve_output"
CHECKPOINT = OUTPUT / "checkpoints" / "checkpoint_30"


def main() -> int:
    meta_path = CHECKPOINT / "metadata.json"
    if not meta_path.exists():
        print(f"Missing {meta_path}")
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    best_id = meta.get("best_program_id")
    if not best_id:
        print("No best_program_id in metadata")
        return 1

    prog_path = CHECKPOINT / "programs" / f"{best_id}.json"
    prog = json.loads(prog_path.read_text(encoding="utf-8"))
    code = normalize_evolved_agents_yaml(prog["code"])
    metrics = prog.get("metrics", {})

    targets = [
        CHECKPOINT / "best_program.yaml",
        CHECKPOINT / "best_program_info.json",
        OUTPUT / "best" / "best_program.yaml",
        OUTPUT / "best" / "best_program_info.json",
        ROOT / "lab_submission" / "best_program.yaml",
        ROOT / "lab_submission" / "best_program_info.json",
    ]

    info = {
        "id": best_id,
        "generation": prog.get("generation"),
        "iteration": prog.get("iteration_found"),
        "metrics": metrics,
        "language": prog.get("language"),
        "recovered_after_windows_encoding_error": True,
    }

    for p in targets:
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == ".yaml":
            p.write_text(code, encoding="utf-8")
        else:
            p.write_text(json.dumps(info, indent=2), encoding="utf-8")

    score = metrics.get("combined_score", 0)
    print(f"Recovered best program {best_id}")
    print(f"combined_score={score:.4f}")
    print(f"Wrote {len(targets)} files under config/openevolve_output and lab_submission/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
