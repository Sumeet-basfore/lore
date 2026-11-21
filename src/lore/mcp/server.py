"""Model Context Protocol (MCP) stdio server for Lore.

Compatible with Claude Desktop, Cursor, Windsurf, and Antigravity.
Implements the JSON-RPC 2.0 stdio transport per the MCP specification (2024-11-05).
"""

import io
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, TextIO

from lore import __version__
from lore.config import load_config
from lore.core.database import Database
from lore.core.models import AtomType, Draft, DraftStatus, Platform, Project
from lore.extraction.atom_extractor import AtomExtractor
from lore.generation.humanizer import Humanizer
from lore.generation.router import LLMRouter
from lore.intelligence.angle_finder import AngleFinder
from lore.scanner.git_scanner import GitScanner
from lore.visual.card_generator import generate_diff_card


class LoreMCPServer:
    """Stdio JSON-RPC MCP server providing Lore tools to AI IDEs."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.config = load_config()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions for all registered Lore MCP tools."""
        return [
            {
                "name": "lore_scan",
                "description": "Scans git repository history and extracts high-potential Content Atoms.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to git repository (defaults to current working directory).",
                        },
                        "since": {
                            "type": "string",
                            "description": "Time range to scan (e.g. '14 days ago', '7 days ago').",
                            "default": "14 days ago",
                        },
                        "include_wip": {
                            "type": "boolean",
                            "description": "Include WIP and low-entropy commits.",
                            "default": False,
                        },
                    },
                },
            },
            {
                "name": "lore_list_atoms",
                "description": "Lists extracted Content Atoms (engineering accomplishments) with scores and diff sizes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Filter by project ID."},
                        "status": {
                            "type": "string",
                            "enum": ["unprocessed", "drafted", "archived", "all"],
                            "default": "all",
                        },
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            },
            {
                "name": "lore_draft",
                "description": "Generates a humanized, anti-slop post or article draft from a Content Atom.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "atom_id": {"type": "string", "description": "Target Content Atom ID."},
                        "platform": {
                            "type": "string",
                            "enum": ["twitter", "thread", "linkedin", "blog", "changelog"],
                            "default": "twitter",
                        },
                        "model": {"type": "string", "description": "Override LLM model name."},
                    },
                    "required": ["atom_id"],
                },
            },
            {
                "name": "lore_render_card",
                "description": "Renders a syntax-highlighted code diff card as SVG by default, or PNG when requested.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "diff_text": {"type": "string", "description": "Git diff text to render."},
                        "file_label": {"type": "string", "description": "Filename to display on window header."},
                        "theme": {
                            "type": "string",
                            "enum": ["tokyo_night", "catppuccin_mocha", "one_dark"],
                            "default": "tokyo_night",
                        },
                        "aspect_ratio": {
                            "type": "string",
                            "enum": ["16:9", "1:1"],
                            "default": "16:9",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["svg", "png"],
                            "default": "svg",
                            "description": "SVG is the default and editable; PNG requires an available local rasterizer.",
                        },
                    },
                    "required": ["diff_text"],
                },
            },
            {
                "name": "lore_approve",
                "description": "Approves a content draft and marks it ready for publication.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string", "description": "Draft ID to approve."},
                    },
                    "required": ["draft_id"],
                },
            },
        ]

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Executes the requested tool and returns a textual response."""
        if name == "lore_scan":
            repo_path = Path(arguments.get("project_path") or Path.cwd()).resolve()
            since = arguments.get("since", "14 days ago")
            include_wip = arguments.get("include_wip", False)

            proj_id = f"proj_{repo_path.name.lower()}"
            if not self.db.get_project(proj_id):
                self.db.add_project(Project(id=proj_id, name=repo_path.name, path=str(repo_path)))

            scanner = GitScanner(repo_path)
            commits = scanner.scan_commits(since=since, include_wip=include_wip)
            tags = scanner.get_tags()
            atoms = AtomExtractor.extract_atoms(
                project_id=proj_id,
                commits=commits,
                tags=tags,
            )
            for atom in atoms:
                self.db.save_atom(atom)
            return f"Scanned {len(commits)} commits. Extracted and saved {len(atoms)} Content Atoms."

        elif name == "lore_list_atoms":
            proj_id = arguments.get("project_id")
            status = arguments.get("status", "all")
            limit = arguments.get("limit", 20)
            st_filter = None if status == "all" else status
            atoms = self.db.list_atoms(project_id=proj_id, status=st_filter)
            selected = atoms[:limit]
            summary = [
                {
                    "id": a.id,
                    "type": a.atom_type.value,
                    "title": a.title,
                    "score": round(a.potential_score, 2),
                    "status": a.status,
                    "diff": f"+{a.evidence.insertions}/-{a.evidence.deletions}",
                    "files": a.evidence.key_files[:3],
                }
                for a in selected
            ]
            return json.dumps(summary, indent=2)

        elif name == "lore_draft":
            atom_id = arguments["atom_id"]
            atom = self.db.get_atom(atom_id)
            if not atom:
                return f"Error: Content Atom '{atom_id}' not found."

            plat = Platform(arguments.get("platform", "twitter"))
            router = LLMRouter(self.config)
            angles = AngleFinder.find_angles(atom)
            chosen_angle = next((ang for ang in angles if plat in ang.best_platforms), angles[0] if angles else None)
            prompt = router.render_prompt(
                platform=plat,
                project_name="Project",
                atom=atom,
                angle=chosen_angle,
            )
            model_override = arguments.get("model")
            raw_output = router.generate(prompt=prompt, model=model_override)
            humanized, audit = Humanizer.humanize(raw_output)

            draft_id = f"draft_{atom.id[:6]}"
            draft = Draft(
                id=draft_id,
                atom_id=atom.id,
                project_id=atom.project_id,
                platform=plat,
                title=f"{plat.value.capitalize()}: {atom.title}",
                raw_content=raw_output,
                humanized_content=humanized,
                humanizer_audit=audit,
                status=DraftStatus.DRAFTED,
            )
            self.db.save_draft(draft)
            self.db.update_atom_status(atom.id, "drafted")
            return f"Draft created [{draft_id}] ({plat.value.upper()}):\n\n{humanized}"

        elif name == "lore_render_card":
            diff_text = arguments["diff_text"]
            file_label = arguments.get("file_label")
            theme = arguments.get("theme", "tokyo_night")
            ratio = arguments.get("aspect_ratio", "16:9")
            output_format = arguments.get("format", "svg")

            path = generate_diff_card(
                diff_text=diff_text,
                theme_name=theme,
                aspect_ratio=ratio,
                file_label=file_label,
                output_format=output_format,
            )
            return f"Rendered diff card saved to: {path}"

        elif name == "lore_approve":
            draft_id = arguments["draft_id"]
            draft = self.db.get_draft(draft_id)
            if not draft:
                return f"Error: Draft '{draft_id}' not found."
            self.db.update_draft_status(draft_id, DraftStatus.APPROVED)
            return f"Draft '{draft_id}' successfully marked as APPROVED."

        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes a single JSON-RPC 2.0 request and returns the JSON-RPC response."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "lore-mcp", "version": "2.0.0"},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tool_definitions()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                res_text = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": res_text}],
                        "isError": False,
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }

    def run_stdio(self, in_stream: Optional[TextIO] = None, out_stream: Optional[TextIO] = None) -> None:
        """Reads JSON-RPC lines from in_stream and writes responses to out_stream."""
        reader = in_stream or sys.stdin
        writer = out_stream or sys.stdout

        for line in reader:
            clean = line.strip()
            if not clean:
                continue
            try:
                req = json.loads(clean)
                resp = self.handle_request(req)
                if resp is not None:
                    writer.write(json.dumps(resp) + "\n")
                    writer.flush()
            except Exception as err:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(err)}"},
                }
                writer.write(json.dumps(err_resp) + "\n")
                writer.flush()


def run_stdio_server(in_stream: Optional[TextIO] = None, out_stream: Optional[TextIO] = None) -> None:
    """Convenience entry point for running the stdio MCP server."""
    server = LoreMCPServer()
    server.run_stdio(in_stream=in_stream, out_stream=out_stream)
