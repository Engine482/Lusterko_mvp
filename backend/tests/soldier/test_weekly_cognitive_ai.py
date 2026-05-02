"""Sprint 3 integration tests: T-WEEKLY-001..003, T-COG-001..003, T-AI-001..005."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.models.daily_checkin import DailyCheckin
from app.models.go_no_go_test import GoNoGoTest
from app.models.reaction_test import ReactionTest
from app.modules.ai import parser as ai_parser
from tests.factories import login_as, make_user


def _login_soldier(client: TestClient, email: str) -> None:
    user = make_user(email=email, roles=("soldier",))
    login_as(client, user)


def _complete_baseline(client: TestClient) -> None:
    client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 1, 0, 2]})
    client.post("/api/v1/soldier/baseline/pss4", json={"answers": [2, 1, 3, 2]})
    client.post("/api/v1/soldier/baseline/sleep", json={"sleep_score": 6})
    client.post(
        "/api/v1/soldier/baseline/reaction-test",
        json={"median_reaction_time_ms": 412, "valid_trials": 24},
    )
    client.post(
        "/api/v1/soldier/baseline/go-no-go",
        json={"commission_errors": 2, "omission_errors": 1, "valid_trials": 30},
    )
    client.post("/api/v1/soldier/baseline/complete")


# --- T-WEEKLY ---------------------------------------------------------------


def test_t_weekly_001_phq4_submission(client: TestClient) -> None:
    _login_soldier(client, "w001@example.com")
    res = client.post("/api/v1/soldier/weekly/phq4", json={"answers": [1, 2, 0, 3]})
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["total_score"] == 6


def test_t_weekly_002_pss4_submission_uses_reverse_scoring(client: TestClient) -> None:
    _login_soldier(client, "w002@example.com")
    # answers [4, 4, 0, 0] → 4 + 4 + (4-0) + (4-0) = 16
    res = client.post("/api/v1/soldier/weekly/pss4", json={"answers": [4, 4, 0, 0]})
    assert res.status_code == 200
    assert res.json()["data"]["total_score"] == 16


def test_t_weekly_003_invalid_payload_rejected(client: TestClient) -> None:
    _login_soldier(client, "w003@example.com")
    bad = client.post("/api/v1/soldier/weekly/phq4", json={"answers": [1, 2, 0]})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "VALIDATION_ERROR"

    out = client.post("/api/v1/soldier/weekly/phq4", json={"answers": [1, 2, 0, 5]})
    assert out.status_code == 422


# --- T-COG ------------------------------------------------------------------


def test_t_cog_001_reaction_submission(client: TestClient) -> None:
    _login_soldier(client, "c001@example.com")
    res = client.post(
        "/api/v1/soldier/cognitive/reaction-test",
        json={"median_reaction_time_ms": 380, "valid_trials": 22},
    )
    assert res.status_code == 200, res.text
    with SessionLocal() as db:
        row = db.execute(select(ReactionTest)).scalar_one()
    assert row.context == "cognitive"
    assert row.median_reaction_time_ms == 380


def test_t_cog_002_go_no_go_submission(client: TestClient) -> None:
    _login_soldier(client, "c002@example.com")
    res = client.post(
        "/api/v1/soldier/cognitive/go-no-go",
        json={"commission_errors": 1, "omission_errors": 0, "valid_trials": 30},
    )
    assert res.status_code == 200
    with SessionLocal() as db:
        row = db.execute(select(GoNoGoTest)).scalar_one()
    assert row.context == "cognitive"


def test_t_cog_003_invalid_valid_trials_rejected(client: TestClient) -> None:
    _login_soldier(client, "c003@example.com")
    bad = client.post(
        "/api/v1/soldier/cognitive/go-no-go",
        json={"commission_errors": 0, "omission_errors": 0, "valid_trials": 3},
    )
    assert bad.status_code == 422


# --- T-AI -------------------------------------------------------------------


def test_t_ai_001_uk_comment_parsed(client: TestClient) -> None:
    _login_soldier(client, "ai001@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 4,
            "energy_score": 4,
            "mood_score": 5,
            "concentration_score": 4,
            "comment_text": "Погано спав, важко зосередитися",
        },
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["ai_parse_status"] == "success"

    with SessionLocal() as db:
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert analysis.language_detected == "uk"
    assert "sleep_issue" in analysis.markers
    assert "concentration_problem" in analysis.markers


def test_t_ai_002_ru_comment_parsed(client: TestClient) -> None:
    _login_soldier(client, "ai002@example.com")
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
            "comment_text": "Плохо сплю, тревожно и устал",
        },
    )
    with SessionLocal() as db:
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert analysis.language_detected == "ru"
    assert {"sleep_issue", "anxiety_tension", "fatigue"}.issubset(set(analysis.markers))


def test_t_ai_003_mixed_input_parsed(client: TestClient) -> None:
    _login_soldier(client, "ai003@example.com")
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
            "comment_text": "Ні до чого не лежить душа, тревожн",
        },
    )
    with SessionLocal() as db:
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert analysis.language_detected == "mixed"


def test_t_ai_004_failure_does_not_break_daily(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """If the AI strategy raises, parser returns failed; daily still saves."""

    class BoomStrategy:
        name = "boom"

        def analyze(self, text: str) -> ai_parser.CommentAnalysis:
            raise RuntimeError("boom")

    monkeypatch.setattr(ai_parser, "get_strategy", lambda: BoomStrategy())

    _login_soldier(client, "ai004@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
            "comment_text": "будь-який текст",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["ai_parse_status"] == "failed"

    with SessionLocal() as db:
        daily = db.execute(select(DailyCheckin)).scalar_one()
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert daily.comment_text == "будь-який текст"
    assert analysis.parse_status == "failed"


def test_t_ai_005_acute_distress_marker(client: TestClient) -> None:
    _login_soldier(client, "ai005@example.com")
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 3,
            "energy_score": 2,
            "mood_score": 2,
            "concentration_score": 3,
            "comment_text": "Не справляюся, нічого не виходить",
        },
    )
    with SessionLocal() as db:
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert "acute_distress" in analysis.markers
    assert analysis.text_risk_level == "high"


def test_no_comment_marks_skipped(client: TestClient) -> None:
    _login_soldier(client, "skip@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 7,
            "energy_score": 7,
            "mood_score": 7,
            "concentration_score": 7,
        },
    )
    assert res.json()["data"]["ai_parse_status"] == "skipped"
    with SessionLocal() as db:
        analysis = db.execute(select(CommentAiAnalysis)).scalar_one()
    assert analysis.parse_status == "skipped"
    assert analysis.markers == []


# --- Due-state v1 -----------------------------------------------------------


def test_due_state_weekly_after_recent_submission(client: TestClient) -> None:
    _login_soldier(client, "due-week@example.com")
    _complete_baseline(client)
    summary = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary["weekly_due"] is True

    client.post("/api/v1/soldier/weekly/phq4", json={"answers": [0, 0, 0, 0]})
    client.post("/api/v1/soldier/weekly/pss4", json={"answers": [0, 0, 4, 4]})
    summary = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary["weekly_due"] is False


def test_due_state_cognitive_after_old_submission(client: TestClient) -> None:
    _login_soldier(client, "due-cog@example.com")
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/cognitive/reaction-test",
        json={"median_reaction_time_ms": 350, "valid_trials": 20},
    )
    client.post(
        "/api/v1/soldier/cognitive/go-no-go",
        json={"commission_errors": 0, "omission_errors": 0, "valid_trials": 30},
    )
    fresh = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert fresh["cognitive_due"] is False

    # Backdate to 5 days ago to trigger due-state.
    with SessionLocal() as db:
        old = date.today() - timedelta(days=5)
        for cls in (ReactionTest, GoNoGoTest):
            row = db.execute(select(cls)).scalar_one()
            row.test_date = old
        db.commit()
    aged = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert aged["cognitive_due"] is True


# --- RBAC -------------------------------------------------------------------


def test_weekly_endpoints_reject_non_soldier(client: TestClient) -> None:
    user = make_user(email="cmdw@example.com", roles=("commander",))
    login_as(client, user)
    blocked = client.post("/api/v1/soldier/weekly/phq4", json={"answers": [0, 0, 0, 0]})
    assert blocked.status_code == 403


# --- Internal AI endpoint ---------------------------------------------------


def test_internal_ai_endpoint_requires_token(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("INTERNAL_API_TOKEN", "secret-test-token")

    no_token = client.post(
        "/internal/ai/analyze-comment",
        json={"text": "Погано спав"},
    )
    assert no_token.json()["error"]["code"] == "FORBIDDEN"

    ok = client.post(
        "/internal/ai/analyze-comment",
        json={"text": "Погано спав, тривожно"},
        headers={"X-Internal-Token": "secret-test-token"},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()["data"]
    assert body["language_detected"] == "uk"
    assert "sleep_issue" in body["markers"]
    assert "anxiety_tension" in body["markers"]


def test_internal_ai_endpoint_disabled_without_token(client: TestClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("INTERNAL_API_TOKEN", raising=False)
    res = client.post(
        "/internal/ai/analyze-comment",
        json={"text": "anything"},
        headers={"X-Internal-Token": "anything"},
    )
    assert res.json()["error"]["code"] == "FORBIDDEN"
