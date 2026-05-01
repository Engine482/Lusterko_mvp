import { ApiCallError } from "./client";

export function describeError(err: unknown): string {
  if (err instanceof ApiCallError) {
    return `${err.code}: ${err.message}`;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Невідома помилка";
}
