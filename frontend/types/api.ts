import type { ErrorCode } from "./enums";

// Standard envelope per `Lusterko_API_Contracts_v1.md` §1.2-1.4.

export type ApiSuccess<T> = {
  success: true;
  data: T;
};

export type ApiError = {
  success: false;
  error: {
    code: ErrorCode;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type ApiResponse<T> = ApiSuccess<T> | ApiError;
