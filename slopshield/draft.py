"""Draft a GHSA-style advisory and a fix patch for a confirmed vulnerability."""
import re
from dataclasses import dataclass
from pathlib import Path

MODEL = "claude-sonnet-5"

ADVISORY_PROMPT_PATH = Path(__file__).parent / "prompts" / "advisory.md"
FIX_PATCH_PROMPT_PATH = Path(__file__).parent / "prompts" / "fix_patch.md"

_XSS_PATCH = """\
--- a/app.py
+++ b/app.py
@@ -1,6 +1,7 @@
 import os

-from flask import Flask, request
+from flask import Flask, request
+from markupsafe import escape

 app = Flask(__name__)

@@ -12,7 +13,7 @@
 @app.route("/greet")
 def greet():
     name = request.args.get("name", "world")
-    return f"<h1>Hello {name}</h1>"
+    return f"<h1>Hello {escape(name)}</h1>"
"""

_PATH_TRAVERSAL_PATCH = """\
--- a/app.py
+++ b/app.py
@@ -18,8 +18,11 @@
 @app.route("/read")
 def read():
     filename = request.args.get("file", "public.txt")
-    path = os.path.join(DATA_DIR, filename)
-    with open(path, "r") as f:
+    path = os.path.realpath(os.path.join(DATA_DIR, filename))
+    if os.path.commonpath([path, DATA_DIR]) != DATA_DIR:
+        return "Forbidden", 403
+    with open(path, "r") as f:
         return f.read()
"""


@dataclass
class DraftResult:
    advisory: str
    patch: str


def draft(issue_text: str, evidence_log: str, mock: bool = False) -> DraftResult:
    if mock:
        return _mock_draft(issue_text, evidence_log)
    return _llm_draft(issue_text, evidence_log)


def _title_of(issue_text: str) -> str:
    match = re.search(r"^#\s+(.+)$", issue_text, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled report"


def _mock_draft(issue_text: str, evidence_log: str) -> DraftResult:
    title = _title_of(issue_text)
    is_xss = "xss" in issue_text.lower() or "/greet" in issue_text
    is_traversal = "path traversal" in issue_text.lower() or "/read" in issue_text

    if is_xss:
        patch = _XSS_PATCH
        patched_component = "`greet()` — escape `name` before interpolating it into HTML."
    elif is_traversal:
        patch = _PATH_TRAVERSAL_PATCH
        patched_component = "`read()` — reject paths that resolve outside `DATA_DIR`."
    else:
        patch = "--- a/app.py\n+++ b/app.py\n(no automatic patch available for this finding) [mock draft]\n"
        patched_component = "(unidentified — manual patch required)"

    advisory = f"""\
## Summary
{title}. Confirmed via sandboxed reproduction. [mock draft]

## Details
See the original report for full technical detail. Reproduction evidence
is attached below.

## PoC / Reproduction
```
{evidence_log.strip()[-800:]}
```

## Impact
Confirmed exploitable against the sandboxed target app; see report for
full impact assessment.

## Patches
Suggested fix: {patched_component}
"""
    return DraftResult(advisory=advisory, patch=patch)


def _llm_draft(issue_text: str, evidence_log: str) -> DraftResult:
    import anthropic

    client = anthropic.Anthropic()
    user_content = f"## Original report\n\n{issue_text}\n\n## Evidence log\n\n{evidence_log}"

    advisory_response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ADVISORY_PROMPT_PATH.read_text(),
        messages=[{"role": "user", "content": user_content}],
    )
    advisory = "".join(b.text for b in advisory_response.content if b.type == "text").strip()

    patch_response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=FIX_PATCH_PROMPT_PATH.read_text(),
        messages=[{"role": "user", "content": user_content}],
    )
    patch = "".join(b.text for b in patch_response.content if b.type == "text").strip()

    return DraftResult(advisory=advisory, patch=patch)
