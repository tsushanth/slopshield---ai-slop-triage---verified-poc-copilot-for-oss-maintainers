# SlopShield — Local MVP Scaffold Plan

## Core value being demoed
Given an incoming vulnerability report (as a text file, standing in for a GitHub issue), the tool should:
1. Classify it as likely-genuine vs. AI-generated slop, with a rationale.
2. If genuine-looking, attempt to reproduce the claimed vuln against a small sample target app inside an isolated Docker container, capturing pass/fail evidence (logs).
3. If reproduction passes, auto-draft a GHSA-style advisory and a fix patch.

Everything else (multi-repo management, live GitHub/GitLab integration, billing, hosting) is out of scope for proving this loop works.

## Stack choice
**Python 3.11+, single small package, CLI-only.**

- `anthropic` SDK for the two LLM calls (classify, draft) — this is the one external network dependency, and it's inherent to the idea ("LLM agent"), so it isn't scoped out. A `--mock` flag will use canned responses so the demo can also run fully offline / without an API key.
- `subprocess` + the `docker` CLI (already on the dev machine) for sandboxed execution — no `docker-py` SDK, no orchestration framework. This is the other dependency that can't be cut: "reproduce in an isolated container" *is* the product.
- No web framework, no database, no queue. Input = local files. Output = local files (JSON/markdown/patch) written to `out/`.
- Plain `argparse`, not a CLI framework like Click/Typer — one subcommand (`run`), doesn't need more.

Rejected alternatives: Node/TS (extra tooling — tsconfig, package.json, build step — for no benefit over Python here), Go single-binary (nice for distribution later, but slower to iterate on LLM prompt scaffolding right now).

## Explicitly out of scope for this local demo
- Auth, accounts, multi-tenant orgs.
- Billing/subscription logic.
- Any deployment/hosting (no server process, no webhook listener).
- Live GitHub/GitLab API integration (no OAuth app, no webhooks, no real PR/issue creation). Inbound reports are simulated as local markdown files in `fixtures/issues/`; outputs (advisory, patch) are written to disk, not posted anywhere.
- A database — run state is just files in `out/`.
- Real CVE/GHSA submission — we only draft the advisory text locally.
- A trained/fine-tuned classifier — a single off-the-shelf LLM call with a prompt is enough to prove the concept.
- A realistic/large vulnerable target app — one tiny toy Flask/Node app with 1-2 deliberately planted bugs is enough to exercise the repro step.
- A dashboard/UI — CLI stdout + generated markdown/JSON files is enough to demonstrate the value.

Not scoped out (core to the idea, kept minimal instead):
- Docker-based sandboxed execution — required to prove "verified PoC," done via plain `docker build`/`docker run` shell-outs against the one toy target app.
- Real LLM calls for classification and drafting — required to prove "AI agent triage," with a `--mock` fallback for offline runs.

## File/directory layout
```
slopshield/
  README.md
  requirements.txt                 # anthropic, pytest
  slopshield/
    __init__.py
    cli.py                         # `python -m slopshield run <issue-file>` entrypoint
    classify.py                    # calls LLM, parses genuine/slop verdict + rationale
    reproduce.py                   # docker build/run against fixtures/target-repo, parses pass/fail
    draft.py                       # calls LLM to draft advisory.md + fix.patch for confirmed issues
    prompts/
      classify.md
      advisory.md
      fix_patch.md
  fixtures/
    issues/
      genuine_001.md               # references a real bug in target-repo, with real repro steps
      genuine_002.md
      slop_001.md                  # vague/generic AI-slop-style report
      slop_002.md
      expected.json                # {"genuine_001": "genuine", "slop_001": "slop", ...} for smoke test
    target-repo/                   # tiny toy app with 1-2 planted bugs
      app.py
      Dockerfile
      repro/
        genuine_001.sh             # script the sandbox runs to attempt repro
        genuine_002.sh
  out/                             # generated at runtime, gitignored
    <issue-id>/
      verdict.json
      evidence.log
      advisory.md
      fix.patch
  tests/
    test_classify.py               # mocked LLM response → verdict parsing
    test_reproduce.py              # fake subprocess → pass/fail parsing
  run_demo.sh                      # loops all fixtures/issues, prints verdict, diffs vs expected.json
```

## Verification
- **Unit tests** (`pytest tests/`): mock the LLM client in `test_classify.py` to assert prompt construction and verdict/rationale parsing; mock `subprocess.run` in `test_reproduce.py` to assert pass/fail parsing from container output without needing Docker installed.
- **Manual run-through**:
  - `python -m slopshield run fixtures/issues/genuine_001.md` → expect verdict "genuine", a Docker container built/run against `target-repo`, `out/genuine_001/evidence.log` showing PASS, and `advisory.md` + `fix.patch` generated.
  - `python -m slopshield run fixtures/issues/slop_001.md` → expect verdict "slop" with rationale, no repro attempted, no advisory drafted.
  - `python -m slopshield run fixtures/issues/genuine_002.md --mock` → same flow but using canned LLM responses, to confirm the tool works offline without an API key.
- **Smoke test**: `./run_demo.sh` runs the tool over every file in `fixtures/issues/`, compares each verdict against `expected.json`, and prints a pass/fail summary line per issue — the fastest way to confirm the classify → reproduce → draft pipeline holds together end to end.
