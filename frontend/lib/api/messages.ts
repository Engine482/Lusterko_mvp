import { ApiCallError } from "./client";

const SETTINGS_ERROR_COPY: Record<string, string> = {
  UNAUTHORIZED: "Перевірте поточний пароль.",
  WEAK_PASSWORD: "Пароль має містити мінімум 12 символів.",
  INVALID_PROFILE: "Введіть коректне імʼя.",
  ACCOUNT_LOCKED: "Забагато спроб. Спробуйте за кілька хвилин.",
};

// Maps the standard error envelope into a Ukrainian message that does not
// expose raw codes or stack traces. Falls back to a generic phrase so the
// production UI never surfaces "UNAUTHORIZED: Current password..." verbatim.
export function localizeSettingsError(err: unknown): string {
  if (err instanceof ApiCallError && err.code in SETTINGS_ERROR_COPY) {
    return SETTINGS_ERROR_COPY[err.code];
  }
  return "Не вдалося зберегти зміни. Спробуйте ще раз.";
}
