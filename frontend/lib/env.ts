// `NEXT_PUBLIC_API_BASE_URL` lives in `.env.example` and is required at build time.
export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
