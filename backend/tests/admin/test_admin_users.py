"""Admin endpoint tests covering T-ADMIN-001..006 + T-RBAC-004 + T-AUDIT-003."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from tests.factories import login_as, make_unit, make_user


def _login(client: TestClient, *, email: str, roles: tuple[str, ...]) -> None:
    user = make_user(email=email, roles=tuple(roles))  # type: ignore[arg-type]
    login_as(client, user)


def test_t_admin_001_create_user(client: TestClient) -> None:
    _login(client, email="admin1@example.com", roles=("admin",))
    unit = make_unit("Unit Bravo")

    res = client.post(
        "/api/v1/admin/users",
        json={
            "full_name": "Soldier One",
            "email": "soldier1@example.com",
            "unit_id": str(unit.id),
            "roles": ["soldier"],
        },
    )
    assert res.status_code == 201, res.text
    payload = res.json()["data"]["user"]
    assert payload["email"] == "soldier1@example.com"
    assert payload["roles"] == ["soldier"]
    assert payload["status"] == "active"

    with SessionLocal() as db:
        events = db.execute(select(AuditLog.event_type)).scalars().all()
    assert "user_created" in events


def test_t_admin_002_assign_multiple_roles(client: TestClient) -> None:
    _login(client, email="admin2@example.com", roles=("admin",))
    target = make_user(email="multi@example.com", roles=("soldier",))

    res = client.put(
        f"/api/v1/admin/users/{target.id}/roles",
        json={"roles": ["soldier", "commander"]},
    )
    assert res.status_code == 200, res.text
    roles_now = sorted(res.json()["data"]["user"]["roles"])
    assert roles_now == ["commander", "soldier"]


def test_t_admin_003_generate_invite(client: TestClient) -> None:
    _login(client, email="admin3@example.com", roles=("admin",))
    target = make_user(email="invitee@example.com")

    res = client.post(f"/api/v1/admin/users/{target.id}/invite")
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["status"] == "pending"
    assert len(body["token"]) > 30
    assert "expires_at" in body


def test_t_admin_004_005_deactivate_then_reactivate(client: TestClient) -> None:
    _login(client, email="admin4@example.com", roles=("admin",))
    target = make_user(email="cycle@example.com")

    deactivated = client.post(f"/api/v1/admin/users/{target.id}/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["status"] == "inactive"

    reactivated = client.post(f"/api/v1/admin/users/{target.id}/reactivate")
    assert reactivated.status_code == 200
    assert reactivated.json()["data"]["status"] == "active"


def test_t_admin_006_audit_logs_endpoint(client: TestClient) -> None:
    _login(client, email="admin6@example.com", roles=("admin",))
    target = make_user(email="audit-target@example.com")
    client.post(f"/api/v1/admin/users/{target.id}/deactivate")

    res = client.get("/api/v1/admin/audit-logs")
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["total"] >= 1
    types = [item["event_type"] for item in body["items"]]
    assert "user_deactivated" in types


def test_t_rbac_004_active_role_governs_admin(client: TestClient) -> None:
    """Soldier+admin user gets blocked when active role is 'soldier'."""

    user = make_user(email="multi-admin@example.com", roles=("soldier", "admin"))
    login_as(client, user)
    # Multi-role: must pick an active role first.
    client.post("/api/v1/auth/select-role", json={"role": "soldier"})

    blocked = client.get("/api/v1/admin/users")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "INVALID_ACTIVE_ROLE"

    # Switch to admin → endpoint becomes available.
    client.post("/api/v1/auth/select-role", json={"role": "admin"})
    ok = client.get("/api/v1/admin/users")
    assert ok.status_code == 200


def test_unauthenticated_admin_call_rejected(client: TestClient) -> None:
    res = client.get("/api/v1/admin/users")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_inactive_user_session_denied(client: TestClient) -> None:
    """Deactivated user with a still-existing session loses access immediately."""

    user = make_user(email="alive-then-deact@example.com", roles=("admin",))
    login_as(client, user)
    # First call works.
    assert client.get("/api/v1/admin/users").status_code == 200

    # Direct DB deactivation (skipping admin endpoint to bypass cookie reuse).
    with SessionLocal() as db:
        from app.models.user import User

        target = db.execute(select(User).where(User.email == user.email)).scalar_one()
        target.status = "inactive"
        db.commit()

    blocked = client.get("/api/v1/admin/users")
    assert blocked.status_code == 401
    assert blocked.json()["error"]["code"] == "UNAUTHORIZED"
