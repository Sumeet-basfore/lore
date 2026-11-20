# Building a Local-First Code-to-Content Pipeline: DLP and AST Diffing

Most developers want to share what they build, but nobody wants to spend two hours converting git logs into public posts.

When engineers try generic LLMs for this, two bad things happen:
1. Developers paste raw diffs into web prompts, leaking API keys, internal URLs, and customer database schema names.
2. The LLM produces generic marketing fluff with empty adjectives, copula crutches, and fabricated statistics.

When we built Lore, we treated repo-to-post generation as a systems engineering problem. The two foundational components in this architecture are the local-first DLP scanner and the AST semantic diff extractor.

Here is how both work under the hood.

---

## 1. The DLP Scanner: Preventing Credential Leaks on Loopback

Before any text reaches an LLM prompt, it passes through our security scanner. We cannot rely on LLM system prompts to "ignore secrets" because models fail at negative constraints and token leakage is irreversible.

Our scanner implements a two-tier policy:

### Tier 1: Hard Block
If a file or diff line matches a private key signature (PEM block, RSA header, PKCS12 file), the pipeline stops immediately. Zero bytes leave the local process.

### Tier 2: Redaction and Masking
For inline credentials, we run 42 Gitleaks-derived regular expressions covering:
* AWS access keys and secret keys
* GitHub personal access tokens
* OpenAI, Anthropic, and cloud provider keys
* Slack, Discord, and Telegram webhook URLs
* Database URIs containing embedded passwords (`postgres://user:pass@host/db`)

Each matched token is replaced with `[MASKED_<TYPE>]`.

### Shannon Entropy Thresholding
Regex only catches known credential structures. It misses raw high-entropy strings like custom HMAC tokens or database salts.

Lore calculates Shannon entropy over every contiguous token with length >= 24:

```python
import math
from collections import Counter

def calculate_shannon_entropy(token: str) -> float:
    length = len(token)
    if length == 0:
        return 0.0
    frequencies = Counter(token)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in frequencies.values()
    )
```

We apply alphabet-specific threshold limits:
* Hex strings (Base16): Entropy >= 3.75 flags potential secrets.
* Base64 / ASCII strings: Entropy >= 4.8 flags potential secrets.
* Sensitive variable identifiers (names containing `password`, `token`, `secret`, `api_key`): Threshold drops to length >= 10 and entropy >= 3.2.

To avoid false positives on git commit hashes, any 40-character hexadecimal string is checked against `git rev-parse`. If the SHA exists in the local git object database, Lore whitelists it as a commit hash rather than a masked secret.

Lines longer than 2,048 characters are rejected immediately to protect against regular expression denial-of-service (ReDoS).

---

## 2. AST Diffing: Semantic Changes Over Raw Lines

Raw `git diff` output is terrible input for an LLM:
* A package lockfile change can add 4,000 lines of noise.
* Adding a single parameter to a function header creates a diff that obscures whether the logic changed.
* LLM context windows get saturated by repetitive boilerplate rather than architectural decisions.

Lore replaces brute-force diff dumps with an AST inspector. For Python code, we parse the before and after states using the standard library `ast` module. For TypeScript, Go, and Rust, we parse declaration tokens.

Instead of feeding this to the model:

```diff
- def sync_records(client, batch_size=50):
-     for page in client.paginate(batch_size):
-         process(page)
+ def sync_records(client, batch_size=50, max_retries=3):
+     for page in client.paginate(batch_size):
+         try:
+             process(page)
+         except TransientError:
+             retry_backoff(page, max_retries)
```

The AST extractor produces a structured report:

```json
{
  "file": "src/sync/worker.py",
  "modified_functions": [
    {
      "name": "sync_records",
      "signature_change": "added max_retries=3",
      "error_handling_added": ["TransientError"],
      "loop_type": "paginated_batch"
    }
  ],
  "assertions_added": ["assert retry_count <= 3"],
  "lines_added": 6,
  "lines_deleted": 3
}
```

This reduces token usage by roughly 85% while giving the model exact semantic intent. It knows that you added exponential retry backoff to a pagination worker, not just that 6 lines changed in a Python file.

---

## 3. Resolving the "Clean Commit Fallacy"

Most engineering repos have messy git histories. Developers do not write clean conventional commit messages for every experimental step. We push `wip`, `fix typo`, and `checkpoint` commits.

If a tool relies only on commit messages, it produces garbage content.

Lore clusters commits within a 4-hour temporal window. It flags low-entropy messages, pulls the combined AST diff across the entire cluster, and scores modified files to identify the hero file. A single architecture atom is generated from the combined work, ignoring the 5 intermediate `wip` commits.

---

## 4. The Result: Verifiable Technical Content

By combining local DLP scanning with AST diff extraction:
* Private infrastructure details and API keys never leave your machine.
* Models receive high-density structural facts instead of noisy lockfiles.
* Every generated claim (files modified, lines changed, functions updated) links directly to commit SHAs in an immutable evidence ledger.

When you run local Ollama models (`gemma4:e2b`, `qwen3:4b`, or `llama3.2:3b`), the entire pipeline runs offline on loopback.

Good developer content does not come from clever marketing prompts. It comes from mining ground truth directly out of the codebase.
