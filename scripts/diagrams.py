"""Architecture diagrams: one source per diagram, embedded into Markdown.

Sources live in ``docs/diagrams/<name>.mmd``. Markdown files embed them
between markers:

    <!-- diagram: containers -->
    ...generated mermaid block...
    <!-- /diagram -->

Usage:
    python3 scripts/diagrams.py            # sync embedded copies from sources
    python3 scripts/diagrams.py --check    # fail if out of sync, unused, or contradicting code
    python3 scripts/diagrams.py --render [--out DIR]
                                           # render every source with mermaid-cli (syntax check);
                                           # SVGs go to DIR, or a temp dir that is discarded

See .claude/skills/architecture-diagrams/SKILL.md for the update workflow.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "docs" / "diagrams"
API_SRC = ROOT / "apps" / "api" / "src"
COMPOSE_DIR = ROOT / "deploy" / "compose"
EMBEDDING_FILES = [
    "README.md",
    "README.zh-TW.md",
    "docs/architecture.md",
    "docs/architecture.zh-TW.md",
]
BLOCK = re.compile(r"(<!-- diagram: (?P<name>[\w-]+) -->\n)(?P<body>.*?)(<!-- /diagram -->)", re.S)
ROUTER_PREFIX = re.compile(r'APIRouter\(\s*prefix="(/[\w-]+)"')
COMPOSE_SERVICE = re.compile(r"^  ([a-z][\w-]*):\s*$", re.M)


def sources() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8").rstrip() + "\n" for p in sorted(SOURCES.glob("*.mmd"))}


def embedded(source: str) -> str:
    return f"```mermaid\n{source}```\n"


def sync(check: bool) -> list[str]:
    """Rewrite (or, with ``check``, compare) every embedded block."""
    diagrams = sources()
    problems: list[str] = []
    used: set[str] = set()
    for rel in EMBEDDING_FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str], rel: str = rel) -> str:
            name = match["name"]
            if name not in diagrams:
                problems.append(f"{rel}: unknown diagram '{name}'")
                return match[0]
            used.add(name)
            return f"{match[1]}{embedded(diagrams[name])}{match[4]}"

        updated = BLOCK.sub(replace, text)
        if updated != text:
            if check:
                problems.append(f"{rel}: embedded diagram out of sync (run: make diagrams)")
            else:
                path.write_text(updated, encoding="utf-8")
                print(f"updated {rel}")
    for name in sorted(set(diagrams) - used):
        problems.append(f"docs/diagrams/{name}.mmd: not embedded in any document")
    return problems


def code_facts() -> list[str]:
    """Cheap guards that diagrams name what the code actually has."""
    diagrams = sources()
    problems: list[str] = []
    components = diagrams.get("api-components", "")
    for path in sorted(API_SRC.rglob("*.py")):
        for prefix in ROUTER_PREFIX.findall(path.read_text(encoding="utf-8")):
            if prefix not in components:
                rel = path.relative_to(ROOT)
                problems.append(f"api-components.mmd: router '{prefix}' ({rel}) is missing")
    containers = diagrams.get("containers", "").lower()
    for path in sorted(COMPOSE_DIR.glob("compose*.yml")):
        services = path.read_text(encoding="utf-8").split("\nservices:\n", 1)[-1].split("\nvolumes:", 1)[0]
        for service in COMPOSE_SERVICE.findall(services):
            if service not in containers:
                rel = path.relative_to(ROOT)
                problems.append(f"containers.mmd: compose service '{service}' ({rel}) is missing")
    return problems


def render(out: Path | None) -> list[str]:
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        target = out or Path(tmp)
        target.mkdir(parents=True, exist_ok=True)
        config = Path(tmp) / "puppeteer.json"
        config.write_text(json.dumps({"args": ["--no-sandbox"]}))
        for path in sorted(SOURCES.glob("*.mmd")):
            result = subprocess.run(  # noqa: S603 - fixed command, repo-controlled inputs
                ["pnpm", "exec", "mmdc", "-q", "-p", str(config), "-i", str(path),  # noqa: S607
                 "-o", str(target / f"{path.stem}.svg")],
                cwd=ROOT, capture_output=True, text=True, env=os.environ, check=False,
            )
            if result.returncode != 0:
                problems.append(f"{path.relative_to(ROOT)}: render failed\n{result.stderr.strip()}")
            else:
                print(f"rendered {path.name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify only; change nothing")
    parser.add_argument("--render", action="store_true", help="render sources with mermaid-cli")
    parser.add_argument("--out", type=Path, help="keep rendered SVGs in this directory")
    args = parser.parse_args()

    problems = sync(check=args.check) + code_facts()
    if args.render:
        problems += render(args.out)
    for problem in problems:
        print(problem)
    print(f"diagrams: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
