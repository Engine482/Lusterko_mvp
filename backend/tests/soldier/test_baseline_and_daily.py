"""Soldier flow tests: T-SOLDIER-001..005, T-DAILY-001..005, RBAC."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.daily_checkin import DailyCheckin
from tests.factories import issue_invite_for, make_user


def _login_soldier(client: TestClient, email: str = "soldier@example.com") -> None:
    user = make_user(email=email, roles=("soldier",))
    token = issue_invite_for(user.id)
    client.get(f"/api/v1/auth/google/start?invite_token={token}")
    client.get(
        "/api/v1/auth/google/callback", params={"state": token, "dev_stub": 1}
    )


def _complete_baseline(client: TestClient) -> None:
    assert client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 1, 0, 2]}).status_code == 200
    assert client.post("/api/v1/soldier/baseline/pss4", json={"answers": [2, 1, 3, 2]}).status_code == 200
    assert client.post("/api/v1/soldier/baseline/sleep", json={"sleep_score": 6}).status_code == 200
    assert (
        client.post(
            "/api/v1/soldier/baseline/reaction-test",
            json={"median_reaction_time_ms": 412, "valid_trials": 24},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/soldier/baseline/go-no-go",
            json={"commission_errors": 2, "omission_errors": 1, "valid_trials": 30},
        ).status_code
        == 200
    )
    res = client.post("/api/v1/soldier/baseline/complete")
    assert res.status_code == 200, res.text
    assert res.json()["data"]["baseline_completed"] is True


# --- T-SOLDIER --------------------------------------------------------------


def test_t_soldier_001_onboarding_status_incomplete(client: TestClient) -> None:
    _login_soldier(client, "s001@example.com")
    res = client.get("/api/v1/soldier/onboarding-status")
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["baseline_completed"] is False
    assert body["next_required_step"] == "phq4"
    assert all(step["completed"] is False for step in body["steps"])


def test_t_soldier_002_submit_phq4(client: TestClient) -> None:
    _login_soldier(client, "s002@example.com")
    res = client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 2, 0, 3]})
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["computed"]["phq4_total"] == 6


def test_t_soldier_003_invalid_phq4_payload_rejected(client: TestClient) -> None:
    _login_soldier(client, "s003@example.com")
    bad = client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 2, 0]})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "VALIDATION_ERROR"

    out_of_range = client.post(
        "/api/v1/soldier/baseline/phq4", json={"answers": [1, 2, 0, 5]}
    )
    assert out_of_range.status_code == 422


def test_t_soldier_004_baseline_cannot_complete_if_steps_missing(client: TestClient) -> None:
    _login_soldier(client, "s004@example.com")
    client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 1, 1, 1]})
    res = client.post("/api/v1/soldier/baseline/complete")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_t_soldier_005_baseline_complete_unlocks_daily(client: TestClient) -> None:
    _login_soldier(client, "s005@example.com")
    _complete_baseline(client)
    today_state = client.get("/api/v1/soldier/daily-checkins/today").json()["data"]
    assert today_state["already_submitted"] is False

    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 7,
            "energy_score": 6,
            "mood_score": 7,
            "concentration_score": 6,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["risk_status"] == "insufficient_data"
    assert body["ai_parse_status"] == "skipped"


# --- T-DAILY -----------------------------------------------------------------


def test_t_daily_001_valid_submit(client: TestClient) -> None:
    _login_soldier(client, "d001@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 4,
            "mood_score": 6,
            "concentration_score": 5,
            "comment_text": "Тестовий коментар",
        },
    )
    assert res.status_code == 200, res.text


def test_t_daily_002_one_per_day(client: TestClient) -> None:
    _login_soldier(client, "d002@example.com")
    _complete_baseline(client)
    payload = {
        "sleep_score": 5,
        "energy_score": 4,
        "mood_score": 6,
        "concentration_score": 5,
    }
    assert client.post("/api/v1/soldier/daily-checkins", json=payload).status_code == 200
    second = client.post("/api/v1/soldier/daily-checkins", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DAILY_ALREADY_SUBMITTED"


def test_t_daily_003_blocked_before_baseline_complete(client: TestClient) -> None:
    _login_soldier(client, "d003@example.com")
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 7,
            "energy_score": 6,
            "mood_score": 7,
            "concentration_score": 6,
        },
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "BASELINE_NOT_COMPLETE"


def test_t_daily_004_works_without_comment(client: TestClient) -> None:
    _login_soldier(client, "d004@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 8,
            "energy_score": 8,
            "mood_score": 8,
            "concentration_score": 8,
        },
    )
    assert res.status_code == 200
    with SessionLocal() as db:
        row = db.execute(select(DailyCheckin)).scalar_one()
    assert row.comment_text is None


def test_t_daily_005_invalid_score_rejected(client: TestClient) -> None:
    _login_soldier(client, "d005@example.com")
    _complete_baseline(client)
    bad = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 11,  # out of range
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
        },
    )
    assert bad.status_code == 422


# --- RBAC --------------------------------------------------------------------


def test_soldier_endpoints_reject_non_soldier(client: TestClient) -> None:
    user = make_user(email="cmd@example.com", roles=("commander",))
    token = issue_invite_for(user.id)
    client.get(f"/api/v1/auth/google/start?invite_token={token}")
    client.get(
        "/api/v1/auth/google/callback", params={"state": token, "dev_stub": 1}
    )
    res = client.get("/api/v1/soldier/onboarding-status")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INVALID_ACTIVE_ROLE"


def test_completion_summary_reflects_state(client: TestClient) -> None:
    _login_soldier(client, "summary@example.com")
    summary_pre = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary_pre == {
        "daily_due": False,
        "weekly_due": False,
        "cognitive_due": False,
        "last_risk_status": None,
    }
    _complete_baseline(client)
    summary_post = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary_post["daily_due"] is True

    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
        },
    )
    summary_after = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary_after["daily_due"] is False


def test_baseline_step_progress_advances_next_required(client: TestClient) -> None:
    _login_soldier(client, "progress@example.com")
    client.post("/api/v1/soldier/baseline/phq4", json={"answers": [0, 0, 0, 0]})
    body = client.get("/api/v1/soldier/onboarding-status").json()["data"]
    assert body["next_required_step"] == "pss4"
    assert any(s["step_code"] == "phq4" and s["completed"] for s in body["steps"])


def test_pss4_reverse_scoring(client: TestClient) -> None:
    _login_soldier(client, "pss4@example.com")
    # answers [4, 4, 0, 0] → 4 + 4 + (4-0) + (4-0) = 16 (max).
    res = client.post("/api/v1/soldier/baseline/pss4", json={"answers": [4, 4, 0, 0]})
    assert res.status_code == 200
    assert res.json()["data"]["computed"]["pss4_total"] == 16


# Light placeholder: avoid date-dependent flakiness by asserting the today
# state object reports the current calendar day.
def test_today_endpoint_reports_today(client: TestClient) -> None:
    _login_soldier(client, "today@example.com")
    body = client.get("/api/v1/soldier/daily-checkins/today").json()["data"]
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert body["checkin_date"] in (today, yesterday)  # tolerate UTC vs local
