"""Load/sanitize OpenEvolve-mutated agents YAML."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def normalize_evolved_agents_yaml(raw: str) -> str:
    """Fix common LLM mutations that break PyYAML."""
    raw = raw.strip()

    fence = re.search(r"```(?:yaml|yml|text)?\s*\n(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    elif raw.startswith("```"):
        raw = re.sub(r"^```(?:yaml|yml|text)?\s*\n?", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\n?```\s*$", "", raw).strip()

    lines = raw.splitlines()
    if lines and lines[0].strip().lower() in {"yaml", "yml", "text"}:
        lines = lines[1:]
    raw = "\n".join(lines).strip()

    # Windows OpenEvolve writes checkpoints with default cp1252; strip fancy Unicode.
    replacements = {
        "\u2192": "->",
        "\u2014": "-",
        "\u2013": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)

    fixed_lines: list[str] = []
    for line in lines:
        m = re.match(r"^(\s+(?:role|goal|backstory):\s+)(.+)$", line)
        if m and "{" in m.group(2) and ">" not in m.group(2):
            val = m.group(2).replace("\\", "\\\\").replace('"', '\\"')
            fixed_lines.append(f'{m.group(1)}"{val}"')
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines).strip() + "\n"


def load_agents_yaml(path: str | Path) -> dict:
    raw = Path(path).read_text(encoding="utf-8")
    normalized = normalize_evolved_agents_yaml(raw)
    config = yaml.safe_load(normalized)
    if not isinstance(config, dict):
        raise ValueError(f"Agents config at {path} must be a YAML mapping, got {type(config)}")
    return config


def repair_agents_yaml_file(path: str | Path) -> None:
    """Rewrite a temp/program YAML file in place so downstream loaders succeed."""
    p = Path(path)
    normalized = normalize_evolved_agents_yaml(p.read_text(encoding="utf-8"))
    yaml.safe_load(normalized)  # validate before write
    p.write_text(normalized, encoding="utf-8")
