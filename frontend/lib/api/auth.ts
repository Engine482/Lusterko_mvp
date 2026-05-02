import { apiCall } from "./client";
import type { Role } from "@/types/enums";

export type AuthMe = {
  user: {
    id: string;
    email: string;
    full_name: string;
    status: "active" | "inactive";
    unit_id: string | null;
  };
  roles: Role[];
  active_role: Role | null;
  role_selection_required: boolean;
};

export const authApi = {
  login: (email: string, password: string) =>
    apiCall<{ logged_in: boolean }>("/api/v1/auth/login", {
      method: "POST",
      body: { email, password },
    }),
  acceptInvite: (input: { token: string; full_name?: string; password: string }) =>
    apiCall<{ accepted: boolean }>("/api/v1/auth/invite/accept", {
      method: "POST",
      body: input,
    }),
  passwordForgot: (email: string) =>
    apiCall<{ queued: boolean }>("/api/v1/auth/password/forgot", {
      method: "POST",
      body: { email },
    }),
  passwordReset: (token: string, password: string) =>
    apiCall<{ reset: boolean }>("/api/v1/auth/password/reset", {
      method: "POST",
      body: { token, password },
    }),
  me: () => apiCall<AuthMe>("/api/v1/auth/me"),
  selectRole: (role: Role) =>
    apiCall<{ active_role: Role }>("/api/v1/auth/select-role", {
      method: "POST",
      body: { role },
    }),
  refresh: () => apiCall<{ refreshed: boolean }>("/api/v1/auth/refresh", { method: "POST" }),
  logout: () => apiCall<{ logged_out: boolean }>("/api/v1/auth/logout", { method: "POST" }),
};
