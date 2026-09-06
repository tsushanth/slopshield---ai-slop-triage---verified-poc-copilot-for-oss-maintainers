# SlopShield (local MVP scaffold)

SlopShield is a triage copilot for OSS maintainers drowning in low-quality,
often AI-generated ("slop") vulnerability reports. This repo is a **local,
offline-first proof of the core loop**, not the full product (see
[plan.md](plan.md) for what's deliberately out of scope).

Given one incoming vulnerability report (a markdown file, standing in for
a GitHub issue), the CLI:

1. **Classifies** it as `genuine` or `slop`, with a rationale, via an LLM
   call (or a canned/heuristic response in `--mock` mode).
2. If `genuine`, **reproduces** the claimed vulnerability against a tiny
   toy Flask app (`fixtures/target-repo`) inside an isolated Docker
   container, capturing pass/fail evidence.
3. If the reproduction **passes**, **drafts** a GHSA-style advisory and a
   fix patch for the confirmed issue.

Everything is local: input is a file, output is files written to `out/`.
Nothing is posted to GitHub/GitLab, no server runs, no data is stored in a
database.

## Requirements

- Python 3.11+ (developed against; 3.9+ likely works)
- [Docker](https://www.docker.com/) CLI, for the reproduction step
- An `ANTHROPIC_API_KEY` environment variable, for real (non-`--mock`) LLM
  calls

## Install

```
pip install -r requirements.txt
```

## Run

```
# Fully offline, no API key or Docker-less classify still works:
python -m slopshield run fixtures/issues/genuine_001.md --mock

# Real LLM calls (requires ANTHROPIC_API_KEY), real Docker reproduction:
python -m slopshield run fixtures/issues/genuine_001.md
```

Try each fixture to see the different pipeline branches:

- `fixtures/issues/genuine_001.md` — reflected XSS in the toy app's
  `/greet` endpoint. Classifies as genuine, reproduces (PASS), drafts an
  advisory + patch.
- `fixtures/issues/genuine_002.md` — path traversal in `/read`. Same flow.
- `fixtures/issues/slop_001.md` / `slop_002.md` — vague, generic-sounding
  reports with no project-specific detail. Classify as `slop`; the
  pipeline stops there (no reproduction attempted, nothing drafted).

Output for each run is written to `out/<issue-id>/`:

```
out/genuine_001/
  verdict.json      # {"verdict": "genuine", "rationale": "..."}
  evidence.log       # docker build/run output, incl. PASS/FAIL marker
  advisory.md         # GHSA-style draft advisory
  fix.patch           # draft unified-diff fix
```

## Smoke test

Runs every fixture issue in `--mock` mode and checks the verdict against
`fixtures/issues/expected.json`:

```
./run_demo.sh
```

## Unit tests

```
pytest tests/
```

`test_classify.py` mocks the LLM client to check prompt construction and
verdict/rationale parsing. `test_reproduce.py` mocks `subprocess.run` to
check pass/fail parsing from container output — neither requires Docker
or an API key to run.

## How the toy target app works

`fixtures/target-repo/app.py` is a tiny Flask app with two deliberately
planted bugs:

- `/greet?name=` reflects `name` into HTML unescaped (XSS).
- `/read?file=` joins `file` onto a data directory without checking for
  `../` traversal, so `file=../secret_admin.txt` leaks a file outside the
  intended directory.

`fixtures/target-repo/repro/<issue-id>.sh` are the scripts the sandbox
runs inside the built Docker image to attempt each repro: they start the
Flask app, send the malicious request, and print `REPRO_RESULT: PASS` or
`REPRO_RESULT: FAIL` depending on whether the vulnerable behavior showed
up in the response.
