import { apiCall } from "./client";
import type { ParseStatus, RiskStatus } from "@/types/enums";

export type BaselineStepCode = "phq4" | "pss4" | "sleep" | "reaction_test" | "go_no_go";

export type OnboardingStatus = {
  baseline_completed: boolean;
  completed_at: string | null;
  steps: { step_code: BaselineStepCode; completed: boolean }[];
  next_required_step: BaselineStepCode | null;
};

export type DailyTodayState = {
  already_submitted: boolean;
  checkin_date: string;
  last_risk_status: RiskStatus | null;
};

export type DailySubmissionResult = {
  daily_checkin_id: string;
  risk_status: RiskStatus;
  explanation_text: string | null;
  ai_parse_status: ParseStatus;
};

export type CompletionSummary = {
  daily_due: boolean;
  weekly_due: boolean;
  cognitive_due: boolean;
  last_risk_status: RiskStatus | null;
};

export const soldierApi = {
  onboardingStatus: () =>
    apiCall<OnboardingStatus>("/api/v1/soldier/onboarding-status"),

  submitPhq4: (answers: number[]) =>
    apiCall<{ step_code: BaselineStepCode; computed?: Record<string, number> }>(
      "/api/v1/soldier/baseline/phq4",
      { method: "POST", body: { answers } },
    ),

  submitPss4: (answers: number[]) =>
    apiCall<{ step_code: BaselineStepCode; computed?: Record<string, number> }>(
      "/api/v1/soldier/baseline/pss4",
      { method: "POST", body: { answers } },
    ),

  submitSleep: (sleepScore: number) =>
    apiCall<{ step_code: BaselineStepCode }>("/api/v1/soldier/baseline/sleep", {
      method: "POST",
      body: { sleep_score: sleepScore },
    }),

  submitReactionTest: (medianMs: number, validTrials: number) =>
    apiCall<{ step_code: BaselineStepCode }>(
      "/api/v1/soldier/baseline/reaction-test",
      {
        method: "POST",
        body: { median_reaction_time_ms: medianMs, valid_trials: validTrials },
      },
    ),

  submitGoNoGo: (commission: number, omission: number, validTrials: number) =>
    apiCall<{ step_code: BaselineStepCode }>("/api/v1/soldier/baseline/go-no-go", {
      method: "POST",
      body: {
        commission_errors: commission,
        omission_errors: omission,
        valid_trials: validTrials,
      },
    }),

  completeBaseline: () =>
    apiCall<{ baseline_completed: boolean; completed_at: string }>(
      "/api/v1/soldier/baseline/complete",
      { method: "POST" },
    ),

  getDailyToday: () =>
    apiCall<DailyTodayState>("/api/v1/soldier/daily-checkins/today"),

  submitDaily: (body: {
    sleep_score: number;
    energy_score: number;
    mood_score: number;
    concentration_score: number;
    comment_text?: string | null;
  }) =>
    apiCall<DailySubmissionResult>("/api/v1/soldier/daily-checkins", {
      method: "POST",
      body,
    }),

  completionSummary: () =>
    apiCall<CompletionSummary>("/api/v1/soldier/completion-summary"),
};
