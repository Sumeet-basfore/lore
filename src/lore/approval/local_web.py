"""Zero-dependency local web review dashboard on 127.0.0.1:4748.

Features:
- ThreadingHTTPServer on 127.0.0.1:4748 with dynamic port fallback (4748..4755).
- Single-page dark UI strictly adhering to unslop principles (no fluff, high density).
- In-browser slide-over markdown editor with auto-save debouncing (prevents $EDITOR TTY crashes).
- Hotkeys: J/K navigation, A (approve), R (reject), E (edit), C (copy).
- Ephemeral session token for CSRF protection.
"""

import http.server
import json
from pathlib import Path
import secrets
import socket
import sys
import threading
import urllib.parse
import webbrowser
from typing import Optional, Tuple

from lore.core.database import Database
from lore.core.models import DraftStatus


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lore Review Gateway</title>
  <style>
    :root {
      --bg: #090D13;
      --card-bg: #161B22;
      --header-bg: #11141A;
      --border: #30363D;
      --text: #C9D1D9;
      --text-muted: #8B949E;
      --text-bold: #F0F6FC;
      --accent: #58A6FF;
      --green: #3FB950;
      --red: #F85149;
      --yellow: #D29922;
      --mono: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
      --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      font-size: 14px;
      line-height: 1.5;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }
    .logo {
      font-family: var(--mono);
      font-weight: 700;
      font-size: 15px;
      color: var(--text-bold);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-badge {
      background: var(--border);
      color: var(--accent);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 11px;
    }
    .hotkey-hints {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      gap: 14px;
    }
    .kbd {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 1px 5px;
      border-radius: 3px;
      color: var(--text-bold);
    }
    .main-layout {
      display: flex;
      flex: 1;
      overflow: hidden;
      position: relative;
    }
    /* Left Sidebar: Draft List */
    .sidebar {
      width: 320px;
      background: var(--card-bg);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      flex-shrink: 0;
    }
    .sidebar-header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
    }
    .draft-item {
      padding: 12px 16px;
      border-bottom: 1px solid rgba(48, 54, 61, 0.5);
      cursor: pointer;
      transition: background 0.1s ease;
    }
    .draft-item:hover { background: rgba(88, 166, 255, 0.08); }
    .draft-item.active {
      background: rgba(88, 166, 255, 0.15);
      border-left: 3px solid var(--accent);
    }
    .draft-title {
      font-weight: 600;
      color: var(--text-bold);
      margin-bottom: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .draft-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-muted);
    }
    .badge {
      font-family: var(--mono);
      font-size: 10px;
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 3px;
      text-transform: uppercase;
    }
    .badge-drafted { background: #382c16; color: var(--yellow); }
    .badge-approved { background: #13382c; color: var(--green); }
    .badge-rejected { background: #3d1e28; color: var(--red); }
    /* Content Area */
    .content-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      padding: 24px;
      gap: 20px;
    }
    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px 16px;
    }
    .action-group {
      display: flex;
      gap: 10px;
    }
    .btn {
      font-family: var(--mono);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 4px;
      border: 1px solid var(--border);
      cursor: pointer;
      background: var(--card-bg);
      color: var(--text-bold);
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn:hover { background: var(--border); }
    .btn-green { background: #1a442a; border-color: var(--green); color: #fff; }
    .btn-green:hover { background: #235c39; }
    .btn-red { background: #4a1d24; border-color: var(--red); color: #fff; }
    .btn-red:hover { background: #632731; }
    .btn-accent { background: #1f3552; border-color: var(--accent); color: #fff; }
    .btn-accent:hover { background: #2b4970; }
    /* Review Grid */
    .review-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      flex: 1;
    }
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .panel-header {
      background: var(--header-bg);
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      font-family: var(--mono);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-bold);
      display: flex;
      justify-content: space-between;
    }
    .panel-body {
      padding: 16px;
      overflow-y: auto;
      flex: 1;
    }
    .post-content {
      font-family: var(--sans);
      font-size: 15px;
      line-height: 1.6;
      color: var(--text-bold);
      white-space: pre-wrap;
      word-break: break-word;
    }
    .evidence-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid rgba(48, 54, 61, 0.4);
      font-family: var(--mono);
      font-size: 12px;
    }
    .evidence-label { color: var(--text-muted); }
    .evidence-val { color: var(--text-bold); }
    .card-preview {
      width: 100%;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #000;
      object-fit: contain;
    }
    /* Slide-over Editor */
    .slide-over {
      position: absolute;
      top: 0;
      right: -600px;
      width: 580px;
      height: 100%;
      background: var(--card-bg);
      border-left: 1px solid var(--border);
      box-shadow: -8px 0 24px rgba(0, 0, 0, 0.6);
      transition: right 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      z-index: 100;
    }
    .slide-over.open { right: 0; }
    .editor-header {
      padding: 12px 16px;
      background: var(--header-bg);
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .editor-textarea {
      flex: 1;
      background: var(--bg);
      color: var(--text-bold);
      border: none;
      padding: 16px;
      font-family: var(--mono);
      font-size: 13px;
      line-height: 1.6;
      resize: none;
      outline: none;
    }
    .save-indicator {
      font-family: var(--mono);
      font-size: 11px;
      color: var(--green);
    }
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--header-bg);
      border: 1px solid var(--accent);
      color: var(--text-bold);
      padding: 10px 18px;
      border-radius: 6px;
      font-family: var(--mono);
      font-size: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.2s ease;
      pointer-events: none;
      z-index: 200;
    }
    .toast.show { opacity: 1; transform: translateY(0); }
  </style>
</head>
<body>
  <header>
    <div class="logo">
      <span>LORE REVIEW GATEWAY</span>
      <span class="logo-badge">v2.0</span>
    </div>
    <div class="hotkey-hints">
      <span><span class="kbd">J</span> / <span class="kbd">K</span> Navigate</span>
      <span><span class="kbd">A</span> Approve</span>
      <span><span class="kbd">R</span> Reject</span>
      <span><span class="kbd">E</span> Slide-over Edit</span>
      <span><span class="kbd">C</span> Copy</span>
    </div>
  </header>

  <div class="main-layout">
    <div class="sidebar">
      <div class="sidebar-header">
        <span>Drafts Queue</span>
        <span id="queue-count">0</span>
      </div>
      <div id="draft-list"></div>
    </div>

    <div class="content-area">
      <div class="action-bar">
        <div>
          <span id="active-platform" class="badge" style="margin-right: 8px;">TWITTER</span>
          <span id="active-title" style="font-weight: 600; color: var(--text-bold);">Select a draft</span>
        </div>
        <div class="action-group">
          <button id="btn-copy" class="btn"><span class="kbd">C</span> Copy</button>
          <button id="btn-edit" class="btn btn-accent"><span class="kbd">E</span> Edit</button>
          <button id="btn-reject" class="btn btn-red"><span class="kbd">R</span> Reject</button>
          <button id="btn-approve" class="btn btn-green"><span class="kbd">A</span> Approve</button>
        </div>
      </div>

      <div class="review-grid">
        <div class="panel">
          <div class="panel-header">
            <span>DRAFT CONTENT</span>
            <span id="char-count">0 chars</span>
          </div>
          <div class="panel-body">
            <div id="post-body" class="post-content">Select a draft from the left queue to inspect.</div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <span>EVIDENCE & DIFF CARD</span>
            <span id="evidence-summary">--</span>
          </div>
          <div class="panel-body">
            <div id="evidence-box"></div>
            <div style="margin-top: 16px;">
              <img id="card-img" class="card-preview" style="display: none;" alt="Diff Card" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Slide-over Editor -->
    <div id="slide-over" class="slide-over">
      <div class="editor-header">
        <span style="font-family: var(--mono); font-weight: 600;">IN-BROWSER EDITOR</span>
        <div style="display: flex; align-items: center; gap: 12px;">
          <span id="save-status" class="save-indicator">Saved</span>
          <button id="btn-close-editor" class="btn" style="padding: 2px 8px;">Close (Esc)</button>
        </div>
      </div>
      <textarea id="editor-text" class="editor-textarea" placeholder="Edit markdown draft..."></textarea>
    </div>
  </div>

  <div id="toast" class="toast">Action completed</div>

  <script>
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token') || '';

    let drafts = [];
    let activeIndex = 0;
    let saveTimeout = null;

    async function loadDrafts() {
      try {
        const res = await fetch(`/api/drafts?token=${token}`);
        if (!res.ok) throw new Error("Unauthorized or server error");
        drafts = await res.json();
        document.getElementById('queue-count').innerText = drafts.length;
        renderSidebar();
        if (drafts.length > 0) {
          selectDraft(0);
        }
      } catch (err) {
        showToast("Error loading drafts: " + err.message);
      }
    }

    function renderSidebar() {
      const container = document.getElementById('draft-list');
      container.innerHTML = '';
      drafts.forEach((d, idx) => {
        const div = document.createElement('div');
        div.className = `draft-item ${idx === activeIndex ? 'active' : ''}`;
        div.onclick = () => selectDraft(idx);
        div.innerHTML = `
          <div class="draft-title">${escapeHtml(d.title || 'Untitled Draft')}</div>
          <div class="draft-meta">
            <span class="badge badge-${d.status}">${d.status}</span>
            <span>${d.platform.toUpperCase()}</span>
          </div>
        `;
        container.appendChild(div);
      });
    }

    async function selectDraft(idx) {
      if (idx < 0 || idx >= drafts.length) return;
      activeIndex = idx;
      renderSidebar();

      const d = drafts[idx];
      document.getElementById('active-title').innerText = d.title || 'Untitled';
      const platBadge = document.getElementById('active-platform');
      platBadge.innerText = d.platform.toUpperCase();

      document.getElementById('post-body').innerText = d.humanized_content || d.raw_content || '';
      document.getElementById('editor-text').value = d.humanized_content || d.raw_content || '';
      document.getElementById('char-count').innerText = (d.humanized_content || '').length + ' chars';

      // Load evidence
      const evBox = document.getElementById('evidence-box');
      evBox.innerHTML = `
        <div class="evidence-row"><span class="evidence-label">Draft ID</span><span class="evidence-val">${d.id}</span></div>
        <div class="evidence-row"><span class="evidence-label">Platform</span><span class="evidence-val">${d.platform}</span></div>
        <div class="evidence-row"><span class="evidence-label">Status</span><span class="evidence-val">${d.status}</span></div>
      `;

      // Card image
      const cardImg = document.getElementById('card-img');
      if (d.card_image_path) {
        cardImg.src = `/api/drafts/${d.id}/card?token=${token}&t=${Date.now()}`;
        cardImg.style.display = 'block';
      } else {
        cardImg.style.display = 'none';
      }
    }

    async function updateStatus(status) {
      if (drafts.length === 0) return;
      const d = drafts[activeIndex];
      try {
        const res = await fetch(`/api/drafts/${d.id}/${status}?token=${token}`, { method: 'POST' });
        if (res.ok) {
          d.status = status;
          showToast(`Draft marked as ${status.toUpperCase()}`);
          renderSidebar();
          // advance
          if (activeIndex < drafts.length - 1) {
            selectDraft(activeIndex + 1);
          }
        }
      } catch (err) {
        showToast("Action failed: " + err.message);
      }
    }

    function toggleEditor(open) {
      const editor = document.getElementById('slide-over');
      if (open === undefined) {
        editor.classList.toggle('open');
      } else if (open) {
        editor.classList.add('open');
        document.getElementById('editor-text').focus();
      } else {
        editor.classList.remove('open');
      }
    }

    // Auto-save logic
    document.getElementById('editor-text').addEventListener('input', (e) => {
      const text = e.target.value;
      document.getElementById('post-body').innerText = text;
      document.getElementById('char-count').innerText = text.length + ' chars';
      document.getElementById('save-status').innerText = 'Saving...';
      document.getElementById('save-status').style.color = 'var(--yellow)';

      clearTimeout(saveTimeout);
      saveTimeout = setTimeout(async () => {
        if (drafts.length === 0) return;
        const d = drafts[activeIndex];
        try {
          await fetch(`/api/drafts/${d.id}/update?token=${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
          });
          d.humanized_content = text;
          document.getElementById('save-status').innerText = 'Saved';
          document.getElementById('save-status').style.color = 'var(--green)';
        } catch (err) {
          document.getElementById('save-status').innerText = 'Save failed';
          document.getElementById('save-status').style.color = 'var(--red)';
        }
      }, 500);
    });

    async function copyToClipboard() {
      if (drafts.length === 0) return;
      const d = drafts[activeIndex];
      const text = d.humanized_content || d.raw_content || '';
      try {
        await navigator.clipboard.writeText(text);
        showToast("Copied draft text to clipboard");
      } catch (err) {
        showToast("Clipboard copy failed");
      }
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.innerText = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2000);
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Hotkey listener
    window.addEventListener('keydown', (e) => {
      const isEditing = document.activeElement === document.getElementById('editor-text');
      if (e.key === 'Escape') {
        toggleEditor(false);
        return;
      }
      if (isEditing) return; // Don't trigger hotkeys while typing in editor

      switch (e.key.toLowerCase()) {
        case 'j':
        case 'arrowdown':
          if (activeIndex < drafts.length - 1) selectDraft(activeIndex + 1);
          break;
        case 'k':
        case 'arrowup':
          if (activeIndex > 0) selectDraft(activeIndex - 1);
          break;
        case 'a':
          updateStatus('approve');
          break;
        case 'r':
          updateStatus('reject');
          break;
        case 'e':
          toggleEditor(true);
          e.preventDefault();
          break;
        case 'c':
          copyToClipboard();
          break;
      }
    });

    document.getElementById('btn-approve').onclick = () => updateStatus('approve');
    document.getElementById('btn-reject').onclick = () => updateStatus('reject');
    document.getElementById('btn-edit').onclick = () => toggleEditor(true);
    document.getElementById('btn-close-editor').onclick = () => toggleEditor(false);
    document.getElementById('btn-copy').onclick = copyToClipboard;

    loadDrafts();
  </script>
</body>
</html>
"""


class LoreReviewRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for the zero-dependency review dashboard."""

    session_token: str = ""
    db: Optional[Database] = None

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep terminal clean
        pass

    def _verify_token(self) -> bool:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        req_token = params.get("token", [""])[0]
        header_token = self.headers.get("X-Lore-Token", "")
        return (req_token == self.session_token) or (header_token == self.session_token)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if not self._verify_token():
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Forbidden: invalid or missing session token"}')
            return

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        if path == "/api/drafts":
            db = self.db or Database()
            drafts = db.list_drafts()
            payload = [d.model_dump(mode="json") for d in drafts]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if path.startswith("/api/drafts/") and path.endswith("/card"):
            parts = path.strip("/").split("/")
            draft_id = parts[2]
            db = self.db or Database()
            draft = db.get_draft(draft_id)
            if draft and getattr(draft, "card_image_path", None):
                card_p = Path(draft.card_image_path)
                if card_p.exists():
                    mime = "image/svg+xml" if card_p.suffix == ".svg" else "image/png"
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.end_headers()
                    self.wfile.write(card_p.read_bytes())
                    return

            self.send_response(404)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if not self._verify_token():
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Forbidden: invalid or missing session token"}')
            return

        db = self.db or Database()

        # Approve: POST /api/drafts/<id>/approve
        if path.startswith("/api/drafts/") and path.endswith("/approve"):
            draft_id = path.strip("/").split("/")[2]
            db.update_draft_status(draft_id, DraftStatus.APPROVED)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "approved", "id": draft_id}).encode("utf-8"))
            return

        # Reject: POST /api/drafts/<id>/reject
        if path.startswith("/api/drafts/") and path.endswith("/reject"):
            draft_id = path.strip("/").split("/")[2]
            db.update_draft_status(draft_id, DraftStatus.REJECTED)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "rejected", "id": draft_id}).encode("utf-8"))
            return

        # Update: POST /api/drafts/<id>/update
        if path.startswith("/api/drafts/") and path.endswith("/update"):
            draft_id = path.strip("/").split("/")[2]
            length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(body_bytes.decode("utf-8"))
            new_content = data.get("content", "")
            db.update_draft_content(draft_id, new_content)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "updated", "id": draft_id}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


class LoreWebReviewServer:
    """Manages the lifecycle of the ThreadingHTTPServer on 127.0.0.1:4748..4755."""

    def __init__(self, start_port: int = 4748, max_attempts: int = 8, db: Optional[Database] = None):
        self.start_port = start_port
        self.max_attempts = max_attempts
        self.session_token = secrets.token_urlsafe(16)
        self.db = db
        self.server: Optional[http.server.ThreadingHTTPServer] = None
        self.port: Optional[int] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> Tuple[str, int]:
        """Binds and starts the HTTP server on an available port in the range."""
        handler_class = LoreReviewRequestHandler
        handler_class.session_token = self.session_token
        handler_class.db = self.db

        for p in range(self.start_port, self.start_port + self.max_attempts):
            try:
                server_address = ("127.0.0.1", p)
                self.server = http.server.ThreadingHTTPServer(server_address, handler_class)
                self.port = p
                break
            except OSError:
                continue

        if not self.server or not self.port:
            raise RuntimeError(
                f"Could not bind Lore review server to any port in range {self.start_port}..{self.start_port + self.max_attempts - 1}."
            )

        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        url = f"http://127.0.0.1:{self.port}/?token={self.session_token}"
        return url, self.port

    def stop(self) -> None:
        """Shuts down the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


def run_local_web_server(port: int = 4748, open_browser: bool = True) -> None:
    """CLI runner that launches the review dashboard and waits for keyboard interrupt."""
    server = LoreWebReviewServer(start_port=port)
    url, actual_port = server.start()
    print(f"\n✓ Lore Review Dashboard running at: {url}")
    print("  Press Ctrl+C to terminate the review server.\n")

    if open_browser:
        webbrowser.open(url)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Lore Review Gateway...")
        server.stop()