import { apiCall } from "./client";
import type { RiskStatus } from "@/types/enums";

export type CommanderSummary = {
  unit_id: string | null;
  counts: Record<RiskStatus, number>;
};

export type CommanderCaseRow = {
  user_id: string;
  full_name: string;
  current_risk_status: RiskStatus;
  explanation_text: string | null;
  calculated_at: string | null;
  last_daily_at: string | null;
};

export type CommanderTrendEntry = {
  status: RiskStatus;
  at: string | null;
  source: string;
};

export type CommanderCaseCard = {
  user_id: string;
  full_name: string;
  unit_id: string | null;
  current_risk_status: RiskStatus;
  explanation_text: string | null;
  calculated_at: string | null;
  recent_status_trend: CommanderTrendEntry[];
};

export const commanderApi = {
  dashboardSummary: () =>
    apiCall<CommanderSummary>("/api/v1/commander/dashboard/summary"),

  dashboardCases: (params?: { status?: RiskStatus; name?: string }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.name) qs.set("name", params.name);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiCall<{ cases: CommanderCaseRow[] }>(
      `/api/v1/commander/dashboard/cases${suffix}`,
    );
  },

  caseCard: (userId: string) =>
    apiCall<CommanderCaseCard>(`/api/v1/commander/cases/${userId}`),
};
