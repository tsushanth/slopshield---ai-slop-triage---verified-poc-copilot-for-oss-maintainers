from pathlib import Path

from slopshield import classify

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "issues"


def test_mock_classify_genuine_report():
    text = (FIXTURES / "genuine_001.md").read_text()
    verdict = classify.classify(text, mock=True)
    assert verdict.verdict == classify.GENUINE
    assert verdict.rationale


def test_mock_classify_slop_report():
    text = (FIXTURES / "slop_001.md").read_text()
    verdict = classify.classify(text, mock=True)
    assert verdict.verdict == classify.SLOP
    assert verdict.rationale


def test_parse_verdict_from_llm_json():
    raw = '{"verdict": "genuine", "rationale": "names app.py and gives curl repro steps"}'
    verdict = classify._parse_verdict(raw)
    assert verdict.verdict == "genuine"
    assert "curl" in verdict.rationale


def test_parse_verdict_strips_surrounding_prose():
    raw = 'Sure, here is my answer:\n{"verdict": "slop", "rationale": "vague, no specifics"}\nHope that helps!'
    verdict = classify._parse_verdict(raw)
    assert verdict.verdict == "slop"


def test_llm_classify_constructs_prompt_and_parses_response(monkeypatch):
    captured = {}

    class FakeTextBlock:
        type = "text"
        text = '{"verdict": "genuine", "rationale": "specific endpoint and repro command"}'

    class FakeMessages:
        def create(self, model, max_tokens, system, messages):
            captured["model"] = model
            captured["system"] = system
            captured["messages"] = messages
            return type("Resp", (), {"content": [FakeTextBlock()]})()

    class FakeClient:
        def __init__(self):
            self.messages = FakeMessages()

    class FakeAnthropicModule:
        def Anthropic(self):
            return FakeClient()

    monkeypatch.setitem(__import__("sys").modules, "anthropic", FakeAnthropicModule())

    verdict = classify._llm_classify("some issue text with /endpoint?x=1")

    assert verdict.verdict == "genuine"
    assert captured["messages"] == [{"role": "user", "content": "some issue text with /endpoint?x=1"}]
    assert "genuine" in captured["system"] or "slop" in captured["system"]
