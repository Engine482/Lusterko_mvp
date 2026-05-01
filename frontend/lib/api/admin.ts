import { apiCall } from "./client";
import type { Role, UserStatus, InviteStatus } from "@/types/enums";

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  status: UserStatus;
  unit_id: string | null;
  roles: Role[];
  created_at: string;
  updated_at: string;
};

export type AdminUnit = {
  id: string;
  name: string;
  code: string | null;
};

export type IssuedInvite = {
  invite_id: string;
  token: string;
  expires_at: string;
  status: InviteStatus;
};

export type AuditLogItem = {
  id: string;
  created_at: string;
  event_type: string;
  actor_user_id: string | null;
  target_user_id: string | null;
  entity_type: string | null;
  entity_id: string | null;
  metadata_json: Record<string, unknown>;
};

type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export const adminApi = {
  listUsers: (params?: {
    unit_id?: string;
    status?: UserStatus;
    role?: Role;
    page?: number;
    page_size?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.unit_id) qs.set("unit_id", params.unit_id);
    if (params?.status) qs.set("status", params.status);
    if (params?.role) qs.set("role", params.role);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiCall<Paginated<AdminUser>>(`/api/v1/admin/users${suffix}`);
  },
  getUser: (id: string) => apiCall<{ user: AdminUser }>(`/api/v1/admin/users/${id}`),
  createUser: (body: {
    full_name: string;
    email: string;
    unit_id: string | null;
    roles: Role[];
  }) =>
    apiCall<{ user: AdminUser }>("/api/v1/admin/users", { method: "POST", body }),
  updateUser: (id: string, body: { full_name?: string; unit_id?: string | null }) =>
    apiCall<{ user: AdminUser }>(`/api/v1/admin/users/${id}`, { method: "PATCH", body }),
  setRoles: (id: string, roles: Role[]) =>
    apiCall<{ user: AdminUser }>(`/api/v1/admin/users/${id}/roles`, {
      method: "PUT",
      body: { roles },
    }),
  issueInvite: (id: string) =>
    apiCall<IssuedInvite>(`/api/v1/admin/users/${id}/invite`, { method: "POST" }),
  deactivate: (id: string) =>
    apiCall<{ user_id: string; status: UserStatus }>(
      `/api/v1/admin/users/${id}/deactivate`,
      { method: "POST" },
    ),
  reactivate: (id: string) =>
    apiCall<{ user_id: string; status: UserStatus }>(
      `/api/v1/admin/users/${id}/reactivate`,
      { method: "POST" },
    ),
  listUnits: () => apiCall<{ items: AdminUnit[] }>("/api/v1/admin/units"),
  createUnit: (body: { name: string; code?: string | null }) =>
    apiCall<AdminUnit>("/api/v1/admin/units", { method: "POST", body }),
  listAuditLogs: (params?: { page?: number; page_size?: number; event_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.page) qs.set("page", String(params.page));
    if (params?.page_size) qs.set("page_size", String(params.page_size));
    if (params?.event_type) qs.set("event_type", params.event_type);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiCall<Paginated<AuditLogItem>>(`/api/v1/admin/audit-logs${suffix}`);
  },
};
