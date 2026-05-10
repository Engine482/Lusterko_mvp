"""Importing model modules so SQLAlchemy registers tables on Base.metadata.

Sprint 0 ships only the org contour + audit_logs. Assessments / risk / case
tables land in later sprints (Backlog TASK-2001+, TASK-3001+, TASK-4001+, TASK-5001+).
"""

from app.models.audit_log import AuditLog
from app.models.auth_invite import AuthInvite
from app.models.auth_lockout import AuthLockout
from app.models.baseline_event import BaselineEvent
from app.models.baseline_profile import BaselineProfile
from app.models.case_review import CaseReview
from app.models.case_review_note import CaseReviewNote
from app.models.comment_ai_analysis import CommentAiAnalysis
from app.models.daily_checkin import DailyCheckin
from app.models.demo_registration import DemoRegistration
from app.models.go_no_go_test import GoNoGoTest
from app.models.password_reset_token import PasswordResetToken
from app.models.reaction_test import ReactionTest
from app.models.risk_event import RiskEvent
from app.models.risk_rule_hit import RiskRuleHit
from app.models.risk_status import RiskStatusRow
from app.models.unit import Unit
from app.models.user import User
from app.models.user_role import UserRole
from app.models.user_session import UserSession
from app.models.weekly_phq4 import WeeklyPhq4Assessment
from app.models.weekly_pss4 import WeeklyPss4Assessment

__all__ = [
    "AuditLog",
    "AuthInvite",
    "AuthLockout",
    "BaselineEvent",
    "BaselineProfile",
    "CaseReview",
    "CaseReviewNote",
    "CommentAiAnalysis",
    "DailyCheckin",
    "DemoRegistration",
    "GoNoGoTest",
    "PasswordResetToken",
    "ReactionTest",
    "RiskEvent",
    "RiskRuleHit",
    "RiskStatusRow",
    "Unit",
    "User",
    "UserRole",
    "UserSession",
    "WeeklyPhq4Assessment",
    "WeeklyPss4Assessment",
]
