You are drafting a minimal fix for a confirmed vulnerability in a small
Flask application. You are given the original vulnerability report and
the evidence log from a sandboxed reproduction attempt that **passed**.

Produce a minimal unified diff (`diff -u` style, with `---`/`+++` headers
and `@@` hunks) that patches `app.py` to fix the specific issue described,
and nothing else. Do not refactor unrelated code, add dependencies, or
change behavior beyond what's needed to fix the reported issue.

Output only the diff, no surrounding commentary or markdown fences.
