"""AI text parsing for daily-check-in comments.

PRD §9 + Risk Engine §2.4. Strict structured output (no diagnosis, no advice,
no dialogue, no autonomous decisions). When the AI fails for any reason the
caller must still persist the daily check-in (PRD §22.4 — AI is not a single
point of failure).

Two strategies share the same `analyze` interface:
- `StubStrategy`: deterministic regex-based marker extraction. Always works,
  no external IO; default for dev/test.
- `OpenAIStrategy`: real LLM call when `OPENAI_API_KEY` env is set.

Both produce the schema documented in PRD §9.6.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Final

from app.core.constants import AI_MARKERS, AIMarker, LanguageDetected, ParseStatus, TextRiskLevel


# --- Public result shape -----------------------------------------------------


@dataclass(frozen=True)
class CommentAnalysis:
    language_detected: LanguageDetected
    has_signal: bool
    markers: list[AIMarker]
    text_risk_level: TextRiskLevel
    confidence_score: float
    summary_for_system: str | None
    parse_status: ParseStatus
    raw_model_name: str | None = None


# --- Helpers shared by strategies --------------------------------------------


_UK_HINTS = re.compile(r"[іїєґІЇЄҐ]")
_RU_HINTS = re.compile(r"[ыъэЫЪЭ]")

# Word-stem fallback for Cyrillic input that lacks language-specific letters.
# Each stem appears in only one language; partial matches via `in` are fine
# since these are distinctive enough that false positives are unlikely.
_UK_WORD_HINTS: Final[tuple[str, ...]] = (
    "погано", "важко", "втом", "виснаж", "пригніч", "тривож", "напруж",
    "зосередит", "зосередж", "роздратова", "немає", "сенсу", "сумно",
    "не лежить", "не справля", "не міг", "після", "дратує", "розсіян",
)
_RU_WORD_HINTS: Final[tuple[str, ...]] = (
    "плохо", "тревож", "уснут", "ничего", "грустно", "печал", "раздраж",
    "сосредот", "паника", "бесит", "вымотан", "обессилен", "сплю", "устал",
    "вспомина", "флешбек", "не могу", "не хочу", "после", "рассеян",
)


def _detect_language(text: str) -> LanguageDetected:
    has_uk_letter = bool(_UK_HINTS.search(text))
    has_ru_letter = bool(_RU_HINTS.search(text))
    lowered = text.lower()
    has_uk_word = any(stem in lowered for stem in _UK_WORD_HINTS)
    has_ru_word = any(stem in lowered for stem in _RU_WORD_HINTS)
    has_uk = has_uk_letter or has_uk_word
    has_ru = has_ru_letter or has_ru_word
    if has_uk and has_ru:
        return "mixed"
    if has_uk:
        return "uk"
    if has_ru:
        return "ru"
    return "unknown"


# --- Stub strategy -----------------------------------------------------------


# Keyword tables are intentionally short and human-readable. They are dual-use:
# they cover Ukrainian and Russian forms of the same idea (PRD §9.3).
_MARKER_KEYWORDS: Final[dict[AIMarker, tuple[str, ...]]] = {
    "sleep_issue": (
        "погано спав",
        "не спав",
        "не міг заснути",
        "безсон",
        "плохо сплю",
        "плохо спал",
        "не выспался",
        "бессонн",
        "не могу уснуть",
    ),
    "fatigue": (
        "втом",
        "виснаж",
        "знесилен",
        "немає сил",
        "устал",
        "вымотан",
        "обессилен",
        "нет сил",
    ),
    "low_mood": (
        "сумно",
        "пригнічен",
        "нічого не хочу",
        "ні до чого не лежить душа",
        "грустно",
        "подавлен",
        "ничего не хочу",
        "нет настроения",
    ),
    "anxiety_tension": (
        "тривож",
        "тривога",
        "напруже",
        "нервов",
        "тревожн",
        "паника",
        "не могу расслабиться",
    ),
    "concentration_problem": (
        "не можу зосередитися",
        "важко зосередитися",
        "розсіян",
        "не сосредоточиться",
        "трудно сосредоточиться",
        "рассеян",
    ),
    "irritability": (
        "дратує",
        "злий",
        "роздратован",
        "раздражает",
        "бесит",
        "зол",
    ),
    "post_stress_reaction": (
        "після стресу",
        "після того",
        "флешбек",
        "после стресса",
        "флешбек",
        "вспоминается",
    ),
    "acute_distress": (
        "не справляюся",
        "не справлюся",
        "не можу більше",
        "не хочу жити",
        "немає сенсу",
        "не справляюсь",
        "не могу больше",
        "не хочу жить",
        "нет смысла",
    ),
}


def _stub_match_markers(text: str) -> list[AIMarker]:
    lowered = text.lower()
    found: list[AIMarker] = []
    for marker in AI_MARKERS:
        keywords = _MARKER_KEYWORDS.get(marker, ())
        if any(kw in lowered for kw in keywords):
            found.append(marker)
    return found


def _classify_risk(markers: list[AIMarker]) -> TextRiskLevel:
    if "acute_distress" in markers:
        return "high"
    n = len(markers)
    if n == 0:
        return "none"
    if n == 1:
        return "low"
    if n == 2:
        return "medium"
    return "high"


@dataclass
class StubStrategy:
    name: str = "stub-v1"

    def analyze(self, text: str) -> CommentAnalysis:
        markers = _stub_match_markers(text)
        return CommentAnalysis(
            language_detected=_detect_language(text),
            has_signal=bool(markers),
            markers=markers,
            text_risk_level=_classify_risk(markers),
            confidence_score=0.7 if markers else 0.4,
            summary_for_system=(
                f"Виявлено маркери: {', '.join(markers)}." if markers else None
            ),
            parse_status="success",
            raw_model_name=self.name,
        )


# --- OpenAI strategy ---------------------------------------------------------


_OPENAI_SYSTEM_PROMPT = """\
You are a strict structured analyzer of short military mental-state comments
written in Ukrainian, Russian, or a mix. You DO NOT diagnose, advise, or
converse. You only extract structured signals.

Return a JSON object with EXACTLY these keys:
- language_detected: one of "uk", "ru", "mixed", "unknown"
- has_signal: boolean
- markers: array of strings, each one of:
  ["sleep_issue", "fatigue", "low_mood", "anxiety_tension",
   "concentration_problem", "irritability", "post_stress_reaction",
   "acute_distress"]
- text_risk_level: one of "none", "low", "medium", "high"
- confidence_score: number 0..1
- summary_for_system: short Ukrainian sentence, no advice, no diagnosis. If no
  signal, set null.

Rules:
- Use "acute_distress" only for explicit statements of inability to cope or
  loss of meaning.
- "high" risk when acute_distress is present OR ≥3 distinct markers.
- Never invent markers; only use the exact strings above.
- Output ONLY the JSON object, nothing else.
"""


@dataclass
class OpenAIStrategy:
    api_key: str
    model: str = "gpt-4o-mini"

    def analyze(self, text: str) -> CommentAnalysis:
        # Imported lazily so dev/test runs without `openai` installed don't break.
        try:
            from openai import OpenAI
        except ImportError as err:
            raise RuntimeError("openai package not installed") from err

        client = OpenAI(api_key=self.api_key)
        completion = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _OPENAI_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=400,
        )
        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)
        return _validate_payload(data, model_name=self.model)


def _validate_payload(data: dict, model_name: str) -> CommentAnalysis:  # type: ignore[type-arg]
    """Normalize and validate the strategy output. Unknown values become safe
    defaults so a malformed model response never crashes the caller."""

    valid_langs: set[LanguageDetected] = {"uk", "ru", "mixed", "unknown"}
    valid_risks: set[TextRiskLevel] = {"none", "low", "medium", "high"}
    valid_markers: set[str] = set(AI_MARKERS)

    lang = data.get("language_detected")
    if lang not in valid_langs:
        lang = "unknown"

    raw_markers = data.get("markers") or []
    markers: list[AIMarker] = [m for m in raw_markers if m in valid_markers]

    risk = data.get("text_risk_level")
    if risk not in valid_risks:
        risk = _classify_risk(markers)

    confidence_raw = data.get("confidence_score")
    try:
        confidence = float(confidence_raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    summary = data.get("summary_for_system")
    if isinstance(summary, str) and not summary.strip():
        summary = None

    return CommentAnalysis(
        language_detected=_as_language(lang),
        has_signal=bool(markers),
        markers=markers,
        text_risk_level=_as_text_risk(risk),
        confidence_score=confidence,
        summary_for_system=summary if isinstance(summary, str) else None,
        parse_status="success",
        raw_model_name=model_name,
    )


def _as_language(value: object) -> LanguageDetected:
    if value in ("uk", "ru", "mixed", "unknown"):
        return value
    return "unknown"


def _as_text_risk(value: object) -> TextRiskLevel:
    if value in ("none", "low", "medium", "high", "unknown"):
        return value
    return "unknown"


# --- Public entrypoint -------------------------------------------------------


def _provider_name() -> str:
    return os.environ.get("LUSTERKO_AI_PROVIDER", "auto")


def get_strategy() -> StubStrategy | OpenAIStrategy:
    provider = _provider_name()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if provider == "stub":
        return StubStrategy()
    if provider == "openai" or (provider == "auto" and api_key):
        if not api_key:
            return StubStrategy()
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIStrategy(api_key=api_key, model=model)
    return StubStrategy()


def failed_result(model_name: str | None) -> CommentAnalysis:
    return CommentAnalysis(
        language_detected="unknown",
        has_signal=False,
        markers=[],
        text_risk_level="unknown",
        confidence_score=0.0,
        summary_for_system=None,
        parse_status="failed",
        raw_model_name=model_name,
    )


def skipped_result() -> CommentAnalysis:
    return CommentAnalysis(
        language_detected="unknown",
        has_signal=False,
        markers=[],
        text_risk_level="unknown",
        confidence_score=0.0,
        summary_for_system=None,
        parse_status="skipped",
        raw_model_name=None,
    )


def analyze_comment(text: str | None) -> CommentAnalysis:
    """Public entrypoint. Empty/whitespace text → skipped. Strategy errors →
    failed (the daily check-in still saves)."""

    if not text or not text.strip():
        return skipped_result()
    strategy = get_strategy()
    try:
        return strategy.analyze(text.strip())
    except Exception:
        return failed_result(getattr(strategy, "name", None) or getattr(strategy, "model", None))
