"""Classify an incoming vulnerability report as genuine vs. AI-slop."""
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

GENUINE = "genuine"
SLOP = "slop"

MODEL = "claude-sonnet-5"

PROMPT_PATH = Path(__file__).parent / "prompts" / "classify.md"

# Signals used by the offline --mock heuristic. This is a stand-in for the
# real LLM call, not a from-scratch classifier: it looks for the same kind
# of concrete-vs-generic signals the LLM prompt asks for.
_TECHNICAL_MARKERS = [
    r"```",                      # code block
    r"\bcurl\b",                 # an actual command to run
    r"/[A-Za-z0-9_./]+\?",       # an endpoint with a query string
    r"def \w+\(",                # a named function
    r"\bos\.path\.\w+",          # a concrete API reference
    r"\bapp\.py\b",
]
_VAGUE_MARKERS = [
    r"\bcould potentially\b",
    r"\bmay be vulnerable\b",
    r"\bvarious injection attacks\b",
    r"\bimmediate action required\b",
    r"\bmight not follow security best practices\b",
    r"\btheoretically\b",
    r"\bfurther investigation would be needed\b",
]


@dataclass
class Verdict:
    verdict: str
    rationale: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def classify(issue_text: str, mock: bool = False) -> Verdict:
    if mock:
        return _mock_classify(issue_text)
    return _llm_classify(issue_text)


def _mock_classify(issue_text: str) -> Verdict:
    technical_hits = [m for m in _TECHNICAL_MARKERS if re.search(m, issue_text, re.IGNORECASE)]
    vague_hits = [m for m in _VAGUE_MARKERS if re.search(m, issue_text, re.IGNORECASE)]

    if len(technical_hits) > len(vague_hits):
        return Verdict(
            verdict=GENUINE,
            rationale=(
                f"Found {len(technical_hits)} concrete technical signal(s) "
                f"(code/commands/specific endpoints or APIs) outweighing "
                f"{len(vague_hits)} generic-slop phrase(s). [mock classifier]"
            ),
        )
    return Verdict(
        verdict=SLOP,
        rationale=(
            f"Found {len(vague_hits)} generic/vague phrase(s) and only "
            f"{len(technical_hits)} concrete technical signal(s) — reads as "
            f"templated AI-slop rather than a project-specific finding. [mock classifier]"
        ),
    )


def _llm_classify(issue_text: str) -> Verdict:
    import anthropic

    client = anthropic.Anthropic()
    system_prompt = PROMPT_PATH.read_text()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": issue_text}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text")
    return _parse_verdict(raw)


def _parse_verdict(raw: str) -> Verdict:
    raw = raw.strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"could not find JSON verdict in LLM response: {raw!r}")
    data = json.loads(match.group(0))
    verdict = data["verdict"].strip().lower()
    if verdict not in (GENUINE, SLOP):
        raise ValueError(f"unexpected verdict value: {verdict!r}")
    return Verdict(verdict=verdict, rationale=data.get("rationale", ""))
