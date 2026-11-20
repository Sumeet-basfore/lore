"""Project directory inspection, tech stack detection, and documentation parser."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProjectWalker:
    """Inspects a project repository structure to discover languages, frameworks, and summary."""

    @staticmethod
    def inspect(project_path: Path) -> Dict[str, Any]:
        path = Path(project_path).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Project directory not found: {path}")

        tech_stack = ProjectWalker.detect_tech_stack(path)
        readme_info = ProjectWalker.parse_readme(path)

        return {
            "path": str(path),
            "name": path.name,
            "tech_stack": tech_stack,
            "readme_title": readme_info.get("title"),
            "readme_description": readme_info.get("description"),
            "has_git": (path / ".git").is_dir(),
        }

    @staticmethod
    def detect_tech_stack(path: Path) -> List[str]:
        """Infers the programming languages, libraries, and frameworks used in the project."""
        stack = set()

        # JavaScript / TypeScript / Node.js
        pkg_json = path / "package.json"
        if pkg_json.is_file():
            stack.add("Node.js")
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if (path / "tsconfig.json").exists() or "typescript" in deps:
                    stack.add("TypeScript")
                else:
                    stack.add("JavaScript")

                if "react" in deps:
                    stack.add("React")
                if "next" in deps:
                    stack.add("Next.js")
                if "vue" in deps:
                    stack.add("Vue")
                if "svelte" in deps:
                    stack.add("Svelte")
                if "tailwindcss" in deps or (path / "tailwind.config.js").exists():
                    stack.add("TailwindCSS")
                if "vite" in deps:
                    stack.add("Vite")
                if "express" in deps:
                    stack.add("Express")
                if "fastify" in deps:
                    stack.add("Fastify")
            except Exception:
                pass

        # Python
        if (
            (path / "pyproject.toml").is_file()
            or (path / "requirements.txt").is_file()
            or (path / "setup.py").is_file()
            or (path / "Pipfile").is_file()
        ):
            stack.add("Python")
            pyproject = path / "pyproject.toml"
            if pyproject.is_file():
                try:
                    content = pyproject.read_text(encoding="utf-8")
                    if "fastapi" in content.lower():
                        stack.add("FastAPI")
                    if "django" in content.lower():
                        stack.add("Django")
                    if "flask" in content.lower():
                        stack.add("Flask")
                    if "click" in content.lower():
                        stack.add("Click")
                    if "pydantic" in content.lower():
                        stack.add("Pydantic")
                except Exception:
                    pass

        # Rust
        if (path / "Cargo.toml").is_file():
            stack.add("Rust")

        # Go
        if (path / "go.mod").is_file():
            stack.add("Go")

        # Docker
        if (path / "Dockerfile").is_file() or (path / "compose.yaml").is_file() or (path / "docker-compose.yml").is_file():
            stack.add("Docker")

        # SQL / Database
        if list(path.glob("**/*.sql")) or "sqlite" in [s.lower() for s in stack]:
            stack.add("SQL")

        return sorted(list(stack))

    @staticmethod
    def parse_readme(path: Path) -> Dict[str, Optional[str]]:
        """Extracts the title and introductory summary from README.md if present."""
        readme_candidates = ["README.md", "readme.md", "README", "readme.markdown"]
        readme_path: Optional[Path] = None
        for candidate in readme_candidates:
            p = path / candidate
            if p.is_file():
                readme_path = p
                break

        if not readme_path:
            return {"title": None, "description": None}

        try:
            content = readme_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            title = None
            description = None

            for i, line in enumerate(lines):
                line = line.strip()
                if not title and line.startswith("# "):
                    title = line.lstrip("# ").strip()
                    # Look ahead for a blockquote or first substantive paragraph
                    for next_line in lines[i + 1 : i + 10]:
                        next_line = next_line.strip()
                        if next_line.startswith(">"):
                            description = next_line.lstrip("> ").strip()
                            break
                        elif next_line and not next_line.startswith("#"):
                            description = next_line
                            break
                    break

            return {"title": title, "description": description}
        except Exception:
            return {"title": None, "description": None}
