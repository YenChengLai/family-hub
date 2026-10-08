"""Documentation consistency checks (see docs/contributing/documentation.md).

1. Every hand-written English doc has a ``.zh-TW.md`` translation.
2. Every translation starts with a valid ``translation-of`` header that
   points back to its English source.
3. Every relative Markdown link resolves to an existing file.

Exit code 1 if any check fails.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Files that are intentionally English-only.
ENGLISH_ONLY = {"CLAUDE.md", "apps/api/README.md", ".github/pull_request_template.md"}
SKIP_DIRS = {"node_modules", "dist", "dev-dist", "reference"}
HEADER = re.compile(r"^<!-- translation-of: (\S+) \| synced: \d{4}-\d{2}-\d{2} -->$")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def markdown_files() -> list[Path]:
    return sorted(
        p
        for p in ROOT.rglob("*.md")
        if not any(
            part in SKIP_DIRS or (part.startswith(".") and part != ".github")
            for part in p.relative_to(ROOT).parts
        )
    )


def main() -> int:
    problems: list[str] = []
    for path in markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")

        if rel.endswith(".zh-TW.md"):
            source = rel.removesuffix(".zh-TW.md") + ".md"
            first_line = text.splitlines()[0] if text else ""
            match = HEADER.match(first_line)
            if not match:
                problems.append(f"{rel}: missing or malformed translation header")
            elif match.group(1) != source:
                problems.append(f"{rel}: header points to {match.group(1)}, expected {source}")
        elif rel not in ENGLISH_ONLY:
            translation = path.with_name(path.name.removesuffix(".md") + ".zh-TW.md")
            if not translation.exists():
                problems.append(f"{rel}: missing translation {translation.name}")

        for link in LINK.findall(text):
            if re.match(r"^[a-z]+:", link):
                continue
            if not (path.parent / link).exists():
                problems.append(f"{rel}: broken link {link}")

    for problem in problems:
        print(problem)
    print(f"docs-check: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
