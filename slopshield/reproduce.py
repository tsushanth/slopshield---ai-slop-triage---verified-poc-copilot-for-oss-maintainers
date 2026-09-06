"""Attempt to reproduce a claimed vulnerability in an isolated Docker
container, built from fixtures/target-repo, running the repro script
that matches the issue id.
"""
import subprocess
from dataclasses import dataclass
from pathlib import Path

PASS_MARKER = "REPRO_RESULT: PASS"
FAIL_MARKER = "REPRO_RESULT: FAIL"


@dataclass
class ReproResult:
    passed: bool
    log: str


def reproduce(issue_id: str, target_repo_dir: Path) -> ReproResult:
    repro_script = target_repo_dir / "repro" / f"{issue_id}.sh"
    if not repro_script.exists():
        return ReproResult(
            passed=False,
            log=f"no repro script found at {repro_script}; cannot attempt reproduction.",
        )

    image_tag = f"slopshield-target-{issue_id}"
    log_parts = []

    build_cmd = ["docker", "build", "-t", image_tag, str(target_repo_dir)]
    log_parts.append(f"$ {' '.join(build_cmd)}")
    try:
        build_proc = subprocess.run(build_cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        log_parts.append(f"ERROR: {exc}")
        return ReproResult(passed=False, log="\n".join(log_parts))

    log_parts.append(build_proc.stdout)
    log_parts.append(build_proc.stderr)
    if build_proc.returncode != 0:
        log_parts.append(f"docker build failed with exit code {build_proc.returncode}")
        return ReproResult(passed=False, log="\n".join(log_parts))

    run_cmd = ["docker", "run", "--rm", image_tag, "sh", f"repro/{issue_id}.sh"]
    log_parts.append(f"$ {' '.join(run_cmd)}")
    try:
        run_proc = subprocess.run(run_cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        log_parts.append(f"ERROR: {exc}")
        return ReproResult(passed=False, log="\n".join(log_parts))

    log_parts.append(run_proc.stdout)
    log_parts.append(run_proc.stderr)

    output = run_proc.stdout + run_proc.stderr
    passed = run_proc.returncode == 0 and PASS_MARKER in output and FAIL_MARKER not in output
    return ReproResult(passed=passed, log="\n".join(log_parts))
