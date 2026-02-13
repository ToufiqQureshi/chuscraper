#!/usr/bin/env -S uv run
"""
Copy README.md to docs homepage at docs/index.md.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README_MD = REPO_ROOT / "README.md"
INDEX_MD = REPO_ROOT / "docs" / "index.md"


def main() -> None:
    readme_content = README_MD.read_text()
    INDEX_MD.write_text(readme_content)
    print("Successfully generated index.md!")


if __name__ == "__main__":
    main()
