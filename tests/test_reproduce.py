from pathlib import Path

from slopshield import reproduce

FIXTURE_TARGET_REPO = Path(__file__).resolve().parent.parent / "fixtures" / "target-repo"


class FakeCompletedProcess:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_reproduce_pass(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output, text):
        calls.append(cmd)
        if cmd[1] == "build":
            return FakeCompletedProcess(0, stdout="build ok")
        return FakeCompletedProcess(0, stdout="response body: <script>alert(1)</script>\nREPRO_RESULT: PASS\n")

    monkeypatch.setattr(reproduce.subprocess, "run", fake_run)

    result = reproduce.reproduce("genuine_001", FIXTURE_TARGET_REPO)

    assert result.passed is True
    assert "PASS" in result.log
    assert len(calls) == 2
    assert calls[0][:3] == ["docker", "build", "-t"]
    assert calls[1][:3] == ["docker", "run", "--rm"]


def test_reproduce_fail_when_repro_script_reports_fail(monkeypatch):
    def fake_run(cmd, capture_output, text):
        if cmd[1] == "build":
            return FakeCompletedProcess(0, stdout="build ok")
        return FakeCompletedProcess(1, stdout="response body: nope\nREPRO_RESULT: FAIL\n")

    monkeypatch.setattr(reproduce.subprocess, "run", fake_run)

    result = reproduce.reproduce("genuine_001", FIXTURE_TARGET_REPO)

    assert result.passed is False
    assert "FAIL" in result.log


def test_reproduce_fail_when_docker_build_fails(monkeypatch):
    def fake_run(cmd, capture_output, text):
        return FakeCompletedProcess(1, stdout="", stderr="Dockerfile not found")

    monkeypatch.setattr(reproduce.subprocess, "run", fake_run)

    result = reproduce.reproduce("genuine_001", FIXTURE_TARGET_REPO)

    assert result.passed is False
    assert "Dockerfile not found" in result.log


def test_reproduce_missing_repro_script(monkeypatch, tmp_path):
    result = reproduce.reproduce("nonexistent_issue", tmp_path)
    assert result.passed is False
    assert "no repro script found" in result.log


def test_reproduce_docker_not_installed(monkeypatch):
    def fake_run(cmd, capture_output, text):
        raise FileNotFoundError("docker: command not found")

    monkeypatch.setattr(reproduce.subprocess, "run", fake_run)

    result = reproduce.reproduce("genuine_001", FIXTURE_TARGET_REPO)

    assert result.passed is False
    assert "docker: command not found" in result.log
