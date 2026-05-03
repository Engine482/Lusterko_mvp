// Liveness probe for Railway / uptime monitors. Sibling to backend
// /api/v1/health — answers whether the Next.js process is up; does NOT
// reach into the backend, since a frontend-only outage should still page.

export const dynamic = "force-static";

export function GET() {
  return Response.json({ status: "ok", service: "lusterko-frontend" });
}
