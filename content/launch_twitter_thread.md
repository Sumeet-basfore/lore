# Lore v2.0 Launch Thread

### Tweet 1 (1/5)
Most developer content written with AI sounds like corporate brochure copy. It overuses buzzwords, spams em-dashes, and invents numbers because the model never inspected your repo. We built Lore to fix this. Lore is a local-first CLI that turns raw git commits into verified, high-signal engineering writing.

### Tweet 2 (2/5)
Lore works directly with your local git history. It clusters commits in 4-hour windows, calculates AST diffs across function boundaries, and records an evidence ledger. If your post mentions a 40ms latency reduction or 12 files touched, that claim links directly to commit SHAs. No fabricated metrics.

### Tweet 3 (3/5)
Before anything touches a model, Lore runs an enterprise DLP scanner. It checks 42 regex patterns and evaluates Shannon entropy to strip AWS keys, private tokens, and connection strings. If you use Ollama, zero bytes leave your machine. Your proprietary code stays on loopback.

### Tweet 4 (4/5)
The output runs through a 3-pass anti-slop engine. It strips 29 known AI markers, purges copula crutches like "serves as", removes negative parallelism, and drops decorative emojis. The result reads like an engineer talking to another engineer, not an AI marketing department.

### Tweet 5 (5/5)
Lore v2.0 includes a headless visual diff card generator (SVG and PNG at 1200x675), a local review dashboard on port 4748, and a stdio MCP server for Claude and Cursor.
Install via pip: `pip install -e .`
Scan your repository: `lore scan`
Code and docs: github.com/personal-repo/lore
