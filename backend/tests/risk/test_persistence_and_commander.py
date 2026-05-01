"""Sprint 4 integration: recompute persistence + commander endpoints.

Mirrors Spec §14 scenarios that require DB state and Backlog TASK-4806..4808.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.risk_event import RiskEvent
from app.models.risk_rule_hit import RiskRuleHit
from app.models.risk_status import RiskStatusRow
from tests.factories import issue_invite_for, make_unit, make_user


def _login(client: TestClient, email: str, *, roles=("soldier",), unit_id=None):  # type: ignore[no-untyped-def]
    user = make_user(email=email, roles=roles, unit_id=unit_id)
    token = issue_invite_for(user.id)
    client.get(f"/api/v1/auth/google/start?invite_token={token}")
    client.get(
        "/api/v1/auth/google/callback", params={"state": token, "dev_stub": 1}
    )
    return user


def _complete_baseline(client: TestClient) -> None:
    client.post("/api/v1/soldier/baseline/phq4", json={"answers": [1, 1, 0, 2]})
    client.post("/api/v1/soldier/baseline/pss4", json={"answers": [2, 1, 3, 2]})
    client.post("/api/v1/soldier/baseline/sleep", json={"sleep_score": 7})
    client.post(
        "/api/v1/soldier/baseline/reaction-test",
        json={"median_reaction_time_ms": 400, "valid_trials": 24},
    )
    client.post(
        "/api/v1/soldier/baseline/go-no-go",
        json={"commission_errors": 2, "omission_errors": 1, "valid_trials": 30},
    )
    client.post("/api/v1/soldier/baseline/complete")


# --- Persistence -------------------------------------------------------------


def test_baseline_completion_creates_initial_risk_status(client: TestClient) -> None:
    _login(client, "p001@example.com")
    _complete_baseline(client)
    with SessionLocal() as db:
        status = db.execute(select(RiskStatusRow)).scalar_one()
        events = db.execute(select(RiskEvent)).scalars().all()
    assert status.current_risk_status == "green"
    # baseline_completion event + zero daily means a single recompute fired.
    sources = {e.source_event_type for e in events}
    assert "baseline_completion" in sources


def test_daily_with_low_scores_yields_yellow_or_red(client: TestClient) -> None:
    _login(client, "p002@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 2,
            "energy_score": 3,
            "mood_score": 3,
            "concentration_score": 2,
        },
    )
    body = res.json()["data"]
    assert body["risk_status"] in ("yellow", "red")
    assert body["explanation_text"]
    with SessionLocal() as db:
        hits = db.execute(select(RiskRuleHit)).scalars().all()
    assert any(h.rule_code in {"F1", "F3", "F4", "HF1"} for h in hits)


def test_recompute_appends_event_per_write(client: TestClient) -> None:
    _login(client, "p003@example.com")
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 5,
            "energy_score": 5,
            "mood_score": 5,
            "concentration_score": 5,
        },
    )
    client.post("/api/v1/soldier/weekly/phq4", json={"answers": [1, 1, 1, 1]})
    client.post(
        "/api/v1/soldier/cognitive/reaction-test",
        json={"median_reaction_time_ms": 410, "valid_trials": 22},
    )
    with SessionLocal() as db:
        events = db.execute(select(RiskEvent)).scalars().all()
    sources = [e.source_event_type for e in events]
    assert {"baseline_completion", "daily_checkin", "weekly_phq4", "reaction_test"}.issubset(
        set(sources)
    )


def test_acute_distress_comment_persists_hard_flag(client: TestClient) -> None:
    _login(client, "p004@example.com")
    _complete_baseline(client)
    res = client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 3,
            "energy_score": 2,
            "mood_score": 2,
            "concentration_score": 3,
            "comment_text": "Не справляюся, нічого не виходить",
        },
    )
    body = res.json()["data"]
    assert body["risk_status"] == "red"
    with SessionLocal() as db:
        status = db.execute(select(RiskStatusRow)).scalar_one()
    assert status.hard_flag in {"acute_distress", "severe_functional_cluster"}


def test_completion_summary_reflects_real_status(client: TestClient) -> None:
    _login(client, "p005@example.com")
    _complete_baseline(client)
    summary = client.get("/api/v1/soldier/completion-summary").json()["data"]
    assert summary["last_risk_status"] == "green"


# --- Commander API ----------------------------------------------------------


def test_commander_dashboard_summary_counts_by_status(client: TestClient) -> None:
    unit = make_unit("Bravo")
    # Soldier 1: green via baseline only.
    _login(client, "soldier-g@example.com", unit_id=unit.id)
    _complete_baseline(client)
    # Soldier 2: red via low daily.
    _login(client, "soldier-r@example.com", unit_id=unit.id)
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 2,
            "energy_score": 2,
            "mood_score": 2,
            "concentration_score": 2,
        },
    )

    _login(client, "cmd@example.com", roles=("commander",), unit_id=unit.id)
    res = client.get("/api/v1/commander/dashboard/summary")
    assert res.status_code == 200, res.text
    counts = res.json()["data"]["counts"]
    assert counts["green"] >= 1
    assert counts["red"] >= 1


def test_commander_cases_filters_to_own_unit(client: TestClient) -> None:
    own = make_unit("Charlie")
    other = make_unit("Delta")
    _login(client, "own-soldier@example.com", unit_id=own.id)
    _complete_baseline(client)
    _login(client, "other-soldier@example.com", unit_id=other.id)
    _complete_baseline(client)

    _login(client, "cmd-c@example.com", roles=("commander",), unit_id=own.id)
    res = client.get("/api/v1/commander/dashboard/cases").json()["data"]
    # Both factory users have full_name="Test User"; what we really verify is
    # that exactly one row comes back (the own-unit soldier), not two.
    assert len(res["cases"]) == 1


def test_commander_case_card_returns_filtered_fields(client: TestClient) -> None:
    unit = make_unit("Echo")
    target = _login(client, "target@example.com", unit_id=unit.id)
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 3,
            "energy_score": 3,
            "mood_score": 7,
            "concentration_score": 7,
            "comment_text": "Погано спав",
        },
    )

    _login(client, "cmd-e@example.com", roles=("commander",), unit_id=unit.id)
    res = client.get(f"/api/v1/commander/cases/{target.id}")
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    # Allowed fields per RBAC §6.2.
    assert body["user_id"] == str(target.id)
    assert body["current_risk_status"] in {"green", "yellow", "red", "insufficient_data"}
    assert "explanation_text" in body
    assert isinstance(body["recent_status_trend"], list)
    # Disallowed fields must NOT leak.
    forbidden = {
        "phq4_total",
        "pss4_total",
        "sleep_score",
        "comment_text",
        "markers",
        "confidence_score",
        "raw_model_name",
    }
    assert forbidden.isdisjoint(set(body.keys()))


def test_commander_cannot_view_user_in_other_unit(client: TestClient) -> None:
    a = make_unit("Foxtrot")
    b = make_unit("Golf")
    target = _login(client, "outsider@example.com", unit_id=b.id)
    _complete_baseline(client)
    _login(client, "cmd-f@example.com", roles=("commander",), unit_id=a.id)
    res = client.get(f"/api/v1/commander/cases/{target.id}")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_commander_endpoints_reject_non_commander(client: TestClient) -> None:
    unit = make_unit("Hotel")
    _login(client, "sold-h@example.com", unit_id=unit.id)
    res = client.get("/api/v1/commander/dashboard/summary")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INVALID_ACTIVE_ROLE"


def test_commander_with_no_unit_sees_empty(client: TestClient) -> None:
    _login(client, "cmd-noborder@example.com", roles=("commander",), unit_id=None)
    summary = client.get("/api/v1/commander/dashboard/summary").json()["data"]
    assert summary["unit_id"] is None
    assert all(v == 0 for v in summary["counts"].values())
    cases = client.get("/api/v1/commander/dashboard/cases").json()["data"]
    assert cases["cases"] == []


def test_status_filter_narrows_cases(client: TestClient) -> None:
    unit = make_unit("India")
    _login(client, "green-1@example.com", unit_id=unit.id)
    _complete_baseline(client)
    _login(client, "red-1@example.com", unit_id=unit.id)
    _complete_baseline(client)
    client.post(
        "/api/v1/soldier/daily-checkins",
        json={
            "sleep_score": 2,
            "energy_score": 2,
            "mood_score": 2,
            "concentration_score": 2,
        },
    )

    _login(client, "cmd-i@example.com", roles=("commander",), unit_id=unit.id)
    red_cases = client.get(
        "/api/v1/commander/dashboard/cases", params={"status": "red"}
    ).json()["data"]["cases"]
    statuses = {c["current_risk_status"] for c in red_cases}
    assert statuses == {"red"}
