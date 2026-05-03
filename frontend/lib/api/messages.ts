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

const COMMON_ERROR_COPY: Record<string, string> = {
  UNAUTHORIZED: "Невірний email або пароль. Спробуйте ще раз.",
  FORBIDDEN: "У вас немає доступу до цього розділу.",
  NOT_FOUND: "Запитаний ресурс не знайдено.",
  NETWORK_ERROR: "Немає звʼязку з сервером. Перевірте інтернет.",
  SERVER_ERROR: "Сталася помилка на сервері. Спробуйте за хвилину.",
  ACCOUNT_LOCKED: "Забагато спроб. Спробуйте за кілька хвилин.",
  INVALID_INPUT: "Перевірте введені дані.",
  INVALID_INVITE: "Інвайт-посилання недійсне або вже використане.",
  INVALID_RESET_TOKEN: "Посилання для скидання паролю недійсне або застаріло.",
  WEAK_PASSWORD: "Пароль має містити мінімум 12 символів.",
  INVALID_PROFILE: "Введіть коректне імʼя.",
  INVALID_ACTIVE_ROLE: "Ця роль вам не призначена.",
};

// Generic counterpart of localizeSettingsError for the rest of the app.
// Use this in pages instead of describeError() so production UI never
// shows raw error codes like "FORBIDDEN: …" to end users.
export function humanError(err: unknown): string {
  if (err instanceof ApiCallError) {
    if (err.code in COMMON_ERROR_COPY) {
      return COMMON_ERROR_COPY[err.code];
    }
    if (err.message && err.code === "VALIDATION_ERROR") {
      return err.message;
    }
  }
  return "Не вдалося завантажити дані. Спробуйте оновити сторінку.";
}
