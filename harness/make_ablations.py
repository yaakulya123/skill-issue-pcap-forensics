#!/usr/bin/env python3
"""Generate ablation skill variants by removing exactly one marked SECTION from the
custom skill. Keeps each ablation an exact single-component removal so the C-vs-D
comparison isolates that component's contribution."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUSTOM = ROOT / "skills" / "custom" / "SKILL.md"
ABL = ROOT / "skills" / "ablations"

# variant -> section name to strip
VARIANTS = {
    "D1-no-workflow": "WORKFLOW",
    "D2-no-recipes": "RECIPES",
    "D3-no-schema": "SCHEMA",
}


def strip_section(text: str, name: str) -> str:
    pattern = re.compile(
        r"\n?<!-- SECTION:" + re.escape(name) + r" -->.*?<!-- /SECTION:" + re.escape(name) + r" -->\n?",
        re.DOTALL,
    )
    new, n = pattern.subn("\n", text)
    if n != 1:
        sys.exit(f"ERROR: expected exactly 1 {name} block, found {n}")
    return new


def clean_markers(text: str) -> str:
    # remove the remaining SECTION comment markers so variants read as normal skills
    return re.sub(r"<!-- /?SECTION:[A-Z]+ -->\n?", "", text)


def main():
    src = CUSTOM.read_text()
    for variant, section in VARIANTS.items():
        out_dir = ABL / variant
        out_dir.mkdir(parents=True, exist_ok=True)
        stripped = clean_markers(strip_section(src, section))
        (out_dir / "SKILL.md").write_text(stripped)
        print(f"{variant}: removed {section}, wrote {out_dir/'SKILL.md'} "
              f"({len(stripped.splitlines())} lines)")
    # also write a marker-free copy of the full custom skill for clean use
    (CUSTOM.parent / "SKILL.clean.md").write_text(clean_markers(src))
    print("custom clean copy written")


if __name__ == "__main__":
    main()
