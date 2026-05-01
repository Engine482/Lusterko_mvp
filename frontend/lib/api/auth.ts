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
  start: (inviteToken: string) =>
    apiCall<{ redirect_url: string }>(
      `/api/v1/auth/google/start?invite_token=${encodeURIComponent(inviteToken)}`,
    ),
  me: () => apiCall<AuthMe>("/api/v1/auth/me"),
  selectRole: (role: Role) =>
    apiCall<{ active_role: Role }>("/api/v1/auth/select-role", {
      method: "POST",
      body: { role },
    }),
  refresh: () => apiCall<{ refreshed: boolean }>("/api/v1/auth/refresh", { method: "POST" }),
  logout: () => apiCall<{ logged_out: boolean }>("/api/v1/auth/logout", { method: "POST" }),
};
