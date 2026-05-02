# Replace Google OAuth with email+password authentication

- **Status:** Accepted
- **Date:** 2026-05-02
- **Affects:** Sprint 1 implementation, PRD §14.3, API Contracts §3.1–3.2, DB Schema (`users`, `user_identities`), Test Scenarios auth flows, Wireframes login/invite screens. Reimplementation tracked under **Sprint 7 — Auth Pivot** in the development backlog.

## Context

P0 design (Sprint 1, shipped) used Google OAuth as primary authentication, with invite-based onboarding and an `auth_invites` + `user_identities` model. During Sprint 6 deployment to Railway, the pilot Google OAuth client was created in Google Cloud Console and two factors made it unworkable for an invite-based military pilot:

1. **Testing-mode whitelist.** In OAuth consent screen Testing status, every prospective user must be manually added in Cloud Console as a "test user". This is incompatible with the invite-based admin workflow — admins onboard end users without Cloud Console access, and adding test users does not scale even for a small pilot.
2. **Production verification timeline.** Moving the consent screen to "In production" requires Google app verification, quoted at 4–6 weeks. For a military-purpose application even minimal scopes (`email`, `profile`) introduce review-process information disclosure to a non-participant party, in addition to schedule risk.

Lusterko is invite-based, military mental-health, and assumes a closed user perimeter (`docs/01_product/PRD.md` §1, §14.3). External IdP dependence works against the trust model: a soldier's ability to sign in becomes contingent on possessing or creating a Google account, and identity material is co-resident with a third-party vendor.

## Decision

Replace Google OAuth entirely with email+password authentication. Implementation parameters:

| Concern | Choice | Rationale |
|---|---|---|
| Password hash | `argon2id` via `argon2-cffi` | Modern memory-hard KDF, OWASP-recommended for new apps |
| Minimum length | 12 chars (length-only policy) | Per NIST SP 800-63B; complexity rules increase user burden without proportional security gain |
| Common-password block | Optional top-N list | Cheap defense-in-depth; not blocking on first ship |
| Login rate-limit | 5 attempts / 15 min per (IP, email) | Industry-standard brute-force ceiling without locking out legitimate fat-fingered users |
| Soft-lockout | 5 consecutive fails → 5 min lock; exponential backoff per cycle | Stops automated attackers; honest users wait 5 min |
| Invite token TTL | 7 days | Already in P0 config; gives admins headroom for invite delivery |
| Password reset token TTL | 1 hour | Standard short window for reset links |
| Session cookie TTL | 30 days, rolling | Rolling renewal on each authenticated request |
| 2FA | Not in P0 | Deferred; revisit if pilot feedback or stakeholder demand surfaces |
| SSO / SAML | Not in P0 | Deferred to V1; see "Consequences" below |

Onboarding flow:

1. Admin issues invite (existing `auth_invites` mechanism) → mailer sends link to invitee.
2. Invitee opens `/invite?token=...` → frontend shows email (read-only), full name (editable, prefilled), password, confirm.
3. Submit → backend validates token, hashes password (argon2id), creates `users` row, marks invite consumed, issues session cookie. Redirect to dashboard.
4. Subsequent logins via `/login` (email + password).
5. Forgotten password → `/forgot-password` (anti-enumeration, generic response) → emailed reset link → `/reset-password?token=...` → new password + session.

Code/data removals (clean break, no compatibility shims):

- `app/modules/auth/google.py` (and dev-stub flow)
- `user_identities` table + model + migrations
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` env vars
- All Google-related tests
- Google OAuth screens and callback handler in frontend

## Consequences

**Positive**

- **Sovereignty.** No external IdP dependency; identity material lives in the application database under operator control.
- **Operational simplicity.** No Google Cloud Console maintenance per pilot user, no verification timeline coupled to product launches.
- **User accessibility.** No requirement for end users (soldiers) to possess or create accounts at a third-party vendor.
- **Audit story.** Authentication events are entirely first-party — simpler narrative for any future security review.

**Negative / trade-offs**

- **Credential storage responsibility.** We now own password hashes. Mitigated by argon2id, secure cookie defaults already in place, and the existing audit log.
- **Password recovery friction.** Users who lose access need email-based reset rather than "Sign in with Google" recovery. Acceptable for a controlled pilot.
- **No SSO convenience.** Operators with corporate IdPs will not get one-click sign-in. If a stakeholder requires SSO, the auth layer is small enough to add a parallel provider (OIDC or SAML) without rewriting the user model — `users.password_hash` becomes nullable, `user_identities`-style table is reintroduced for the IdP.

**Scope of change**

All implementation work tracked under Sprint 7 in `docs/03_planning/Lusterko_Development_Backlog_v1.md`. Documentation artifacts (PRD, API Contracts, DB Schema, Test Scenarios, Wireframes) updated as part of that sprint to keep this decision in sync with downstream specs.
