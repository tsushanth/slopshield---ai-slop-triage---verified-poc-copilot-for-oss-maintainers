"""`python -m slopshield run <issue-file>` entrypoint.

Orchestrates the classify -> reproduce -> draft pipeline for a single
simulated incoming vulnerability report.
"""
import argparse
import sys
from pathlib import Path

from slopshield import classify, draft, reproduce

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_REPO = REPO_ROOT / "fixtures" / "target-repo"
DEFAULT_OUT_DIR = REPO_ROOT / "out"


def run(issue_path: Path, mock: bool, target_repo_dir: Path, out_root: Path) -> None:
    issue_id = issue_path.stem
    issue_text = issue_path.read_text()

    out_dir = out_root / issue_id
    out_dir.mkdir(parents=True, exist_ok=True)

    verdict = classify.classify(issue_text, mock=mock)
    (out_dir / "verdict.json").write_text(verdict.to_json())
    print(f"[{issue_id}] verdict: {verdict.verdict} — {verdict.rationale}")

    if verdict.verdict != classify.GENUINE:
        print(f"[{issue_id}] skipping reproduction (verdict is not genuine)")
        return

    repro_result = reproduce.reproduce(issue_id, target_repo_dir)
    (out_dir / "evidence.log").write_text(repro_result.log)
    print(f"[{issue_id}] reproduction: {'PASS' if repro_result.passed else 'FAIL'} "
          f"(see {out_dir / 'evidence.log'})")

    if not repro_result.passed:
        print(f"[{issue_id}] skipping advisory/patch draft (reproduction did not pass)")
        return

    draft_result = draft.draft(issue_text, repro_result.log, mock=mock)
    (out_dir / "advisory.md").write_text(draft_result.advisory)
    (out_dir / "fix.patch").write_text(draft_result.patch)
    print(f"[{issue_id}] wrote advisory.md and fix.patch to {out_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slopshield")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="triage one simulated issue report")
    run_parser.add_argument("issue_file", type=Path, help="path to an issue markdown file")
    run_parser.add_argument("--mock", action="store_true",
                             help="use canned LLM responses instead of calling the Anthropic API")
    run_parser.add_argument("--target-repo", type=Path, default=DEFAULT_TARGET_REPO,
                             help="path to the toy target app repro'd against")
    run_parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                             help="directory to write verdict/evidence/advisory/patch to")

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        if not args.issue_file.exists():
            print(f"error: issue file not found: {args.issue_file}", file=sys.stderr)
            sys.exit(1)
        run(args.issue_file, mock=args.mock, target_repo_dir=args.target_repo, out_root=args.out_dir)


if __name__ == "__main__":
    main()
