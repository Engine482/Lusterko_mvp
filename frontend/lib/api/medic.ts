import { apiCall } from "./client";
import type { CaseStatus, RiskStatus } from "@/types/enums";

export type MedicCaseRow = {
  case_id: string;
  user_id: string;
  full_name: string;
  case_status: CaseStatus;
  current_risk_status: RiskStatus;
  opened_at: string;
  last_event_at: string | null;
};

export type MedicCaseDetail = {
  case_id: string;
  case_status: CaseStatus;
  opened_at: string;
  closed_at: string | null;
  assigned_to_user_id: string | null;
  user: {
    user_id: string;
    full_name: string;
    unit_id: string | null;
  };
  risk: {
    current_risk_status: RiskStatus;
    current_risk_score: string | null;
    explanation_text: string | null;
    hard_flag: string | null;
  };
  latest_daily: {
    checkin_date: string;
    sleep_score: number;
    energy_score: number;
    mood_score: number;
    concentration_score: number;
    comment_text: string | null;
  } | null;
  latest_weekly: {
    phq4_total: number | null;
    pss4_total: number | null;
    phq4_at: string | null;
    pss4_at: string | null;
  };
  latest_cognitive: {
    reaction_median_ms: number | null;
    reaction_at: string | null;
    gonogo_commission_errors: number | null;
    gonogo_omission_errors: number | null;
    gonogo_at: string | null;
  };
  latest_ai: {
    summary_for_system: string | null;
    parse_status: string | null;
    text_risk_level: string | null;
    markers: string[];
  };
  notes: {
    id: string;
    author_user_id: string;
    author_full_name: string;
    text: string;
    created_at: string;
  }[];
};

export const medicApi = {
  listCases: (params?: { case_status?: CaseStatus; risk?: RiskStatus }) => {
    const qs = new URLSearchParams();
    if (params?.case_status) qs.set("case_status", params.case_status);
    if (params?.risk) qs.set("risk", params.risk);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiCall<{ cases: MedicCaseRow[] }>(`/api/v1/medic/cases${suffix}`);
  },
  getCase: (caseId: string) =>
    apiCall<MedicCaseDetail>(`/api/v1/medic/cases/${caseId}`),
  updateStatus: (caseId: string, status: CaseStatus) =>
    apiCall<{ case_id: string; case_status: CaseStatus; closed_at: string | null }>(
      `/api/v1/medic/cases/${caseId}`,
      { method: "PATCH", body: { status } },
    ),
  addNote: (caseId: string, text: string) =>
    apiCall<{ note_id: string; case_review_id: string; created_at: string }>(
      `/api/v1/medic/cases/${caseId}/notes`,
      { method: "POST", body: { text } },
    ),
};
