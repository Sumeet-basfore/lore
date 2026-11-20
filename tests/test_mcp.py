"""Tests for Lore Model Context Protocol (MCP) Server."""

import io
import json
from pathlib import Path
import tempfile
import pytest

from lore.core.database import Database
from lore.core.models import AtomType, ContentAtom, Draft, DraftStatus, EvidenceRecord, Platform, Project
from lore.mcp.server import LoreMCPServer


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        db = Database(db_path=Path(f.name))
        db.add_project(Project(id="proj_mcp", name="MCP Project", path="/tmp"))
        atom = ContentAtom(
            id="atom_mcp_1",
            project_id="proj_mcp",
            atom_type=AtomType.FEATURE,
            title="Distributed Raft Lock",
            summary="Implemented distributed consensus lock",
            evidence=EvidenceRecord(
                commits=["c1"],
                files_changed=2,
                insertions=40,
                deletions=5,
                key_files=["lock.py"],
            ),
            potential_score=0.9,
        )
        db.save_atom(atom)

        draft = Draft(
            id="draft_mcp_1",
            atom_id="atom_mcp_1",
            project_id="proj_mcp",
            platform=Platform.TWITTER,
            title="Consensus Lock Post",
            raw_content="Shipped raft lock",
            humanized_content="We shipped distributed consensus locking today.",
            status=DraftStatus.DRAFTED,
        )
        db.save_draft(draft)
        yield db


def test_mcp_initialize(test_db):
    server = LoreMCPServer(db=test_db)
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    resp = server.handle_request(req)

    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "lore-mcp"
    assert "tools" in resp["result"]["capabilities"]


def test_mcp_tools_list(test_db):
    server = LoreMCPServer(db=test_db)
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = server.handle_request(req)

    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "lore_scan" in tool_names
    assert "lore_list_atoms" in tool_names
    assert "lore_draft" in tool_names
    assert "lore_render_card" in tool_names
    assert "lore_approve" in tool_names


def test_mcp_tool_call_list_atoms(test_db):
    server = LoreMCPServer(db=test_db)
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "lore_list_atoms", "arguments": {"status": "all"}},
    }
    resp = server.handle_request(req)

    assert resp["result"]["isError"] is False
    content = resp["result"]["content"][0]["text"]
    data = json.loads(content)
    assert len(data) >= 1
    assert data[0]["id"] == "atom_mcp_1"


def test_mcp_tool_call_render_card(test_db):
    server = LoreMCPServer(db=test_db)
    sample_diff = "@@ -1,1 +1,2 @@\n-old\n+new"
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "lore_render_card", "arguments": {"diff_text": sample_diff}},
    }
    resp = server.handle_request(req)
    assert resp["result"]["isError"] is False
    assert "Rendered diff card saved to" in resp["result"]["content"][0]["text"]


def test_mcp_tool_call_approve(test_db):
    server = LoreMCPServer(db=test_db)
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "lore_approve", "arguments": {"draft_id": "draft_mcp_1"}},
    }
    resp = server.handle_request(req)
    assert resp["result"]["isError"] is False

    updated = test_db.get_draft("draft_mcp_1")
    assert updated.status == DraftStatus.APPROVED


def test_mcp_stdio_stream(test_db):
    server = LoreMCPServer(db=test_db)
    in_buf = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 99, "method": "ping", "params": {}}) + "\n")
    out_buf = io.StringIO()

    server.run_stdio(in_stream=in_buf, out_stream=out_buf)
    out_val = out_buf.getvalue()
    resp = json.loads(out_val.strip())
    assert resp["id"] == 99
    assert resp["result"] == {}
