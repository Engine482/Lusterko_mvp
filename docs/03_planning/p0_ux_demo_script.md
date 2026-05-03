# Lusterko MVP — Demo script

> 10–15 хв walkthrough під P0 demo readiness checklist (`lusterko_p0_ui_ux_demo_hardening.md` §17). Сценарій лінійний — без розгалужень, щоб презентер пройшов його за один прогін без рішень на льоту.

> Стенд: Railway prod або локальний `make run-backend` + `pnpm start` у `frontend/`. Demo акаунт із 4 ролями створюється `BOOTSTRAP_ADMIN_PASSWORD=... ADMIN_EMAIL=... BOOTSTRAP_USER_ROLES=admin,soldier,commander,medic_psych make seed`.

---

## 0. Перед стартом (1 хв, не показувати на екрані)

- Перевірити `/health` (frontend) → `{"status":"ok"}`.
- Перевірити `/api/v1/health` (backend) → 200.
- Відкрити браузер у privacy mode щоб не було чужих cookies.
- Закрити девтулзи. Маштаб 100%.
- Перевірити, що demo seed виконано і видно у DB (admin_email повертає 4 ролі через `/api/v1/auth/me`).

---

## 1. Landing та ідентичність (45 с)

1. Відкрити **`/`** (Home).
2. Показати:
   - бренд "Люстерко" у header;
   - footer-ідентичність "Люстерко MVP · Volodymyr Motornyi · 2026" + версійний бейдж "P0 · v0.1.0 · demo";
   - favicon (мозок-дзеркало) у вкладці.
3. Натиснути footer-link "Про систему" → відкривається **`/about`**.
4. Прочитати вголос ключове: *"Демо-версія. Не є медичним діагностичним інструментом."* (disclaimer).

> Меседж: "Це не лендінг — це сам застосунок під MVP. Бренд + дисклеймер видно одразу."

---

## 2. Login UX (45 с)

1. Натиснути "Увійти" → **`/login`**.
2. Показати:
   - centered auth-card на темному фоні (clinical-tactical стиль);
   - disclaimer-блок під формою.
3. Ввести demo credentials.
4. Якщо в акаунта кілька ролей → показати **`/role`** screen:
   - картки 4 ролей із короткими описами;
   - **обрати "Військовий"** — потрапляємо на `/soldier`.

> Меседж: "Auth — email+password (Sprint 7 pivot із Google OAuth). Multi-role users явно вибирають активну роль."

---

## 3. Soldier home + due-state (1 хв)

На **`/soldier`**:

1. Показати привітання + сьогоднішня дата UA-форматом.
2. Показати due-cards:
   - **"Завершіть baseline" (X з 5 кроків)** — або daily/weekly/cognitive cards залежно від стану.
3. Натиснути **"Продовжити: Тест реакції"** (якщо baseline ще не завершено) АБО розпочати **`/soldier/baseline/phq4`** з нуля.

> Меседж: "Soldier home — це not a dashboard. Це список того, що від тебе зараз треба, з прямою кнопкою у наступний крок."

---

## 4. Baseline flow + reaction test (3 хв)

1. PHQ-4 (4 запитання) → "Зберегти" → переходимо на PSS-4.
2. PSS-4 (4 запитання) → "Зберегти" → переходимо на Sleep.
3. Sleep шкала → "Зберегти" → переходимо на Reaction.
4. **`/soldier/baseline/reaction`** — головна точка demo.
   - Показати інструкцію.
   - Натиснути **"Почати — спроба 1 з 10"** → поле сіре.
   - Чекати на синє ("Натисніть!") → клікнути → результат.
   - Повторити 10 разів. На 10-му покажеться медіана, далі редірект на Go/No-Go.
5. **`/soldier/baseline/gonogo`**:
   - "Почати" → 30 спроб (синій = тиснути, червоний = ні). Триває ~1 хв.
   - Завершення → редірект на `/soldier/baseline/complete`.
6. Показати completion screen.

> Меседж: "Reaction-time був головним блокером MVP до P0-UX-1 (TASK-8201, EPIC-82). Тепер baseline проходиться end-to-end. На iPhone Safari — touch-target 44px, працює і пальцем, і мишкою."

---

## 5. Daily + комент → AI parsing (1 хв)

1. **`/soldier/daily`**:
   - 4 шкали (сон / енергія / настрій / концентрація).
   - Опціональний коментар — ввести тестовий: *"Сьогодні погано спав, концентрація падає"*.
   - "Зберегти" → confirmation screen.
2. (Опціонально) показати, що comment пройшов через AI (markers у DB або через admin audit log далі).

> Меседж: "Daily — це 30 секунд на день. Коментар проходить через AI parsing layer (sprint 3) і витягує markers (sleep_issue, low_mood, ...). Якщо AI fail-нув — fallback зберігає raw comment без markers."

---

## 6. Role switch → Commander (45 с)

1. У header клікнути **role switcher** (≡ "Військовий ▾") → меню → **"Командир"**.
2. Перейти на **`/commander`**:
   - 4 KPI-картки за статусами ризику (Норма / Увага / Ризик / Недостатньо даних) — кольорові фули + текст (не тільки колір).
   - chip-фільтри статусів.
   - Список кейсів з explanation_text.

> Меседж: "Командир бачить агрегат + scoped кейси по своєму підрозділу. RBAC enforced server-side — UI рендерить лише те що backend повертає."

---

## 7. Commander → case detail (30 с)

1. Клікнути "Деталі →" на одному з кейсів → **`/commander/cases/<id>`**.
2. Показати картку:
   - поточний статус;
   - explanation_text від Risk Engine;
   - 14-денна динаміка статусів.
3. Назад "← До списку".

> Меседж: "Командир НЕ бачить raw daily/weekly score-ів — тільки агрегат + поточний risk status + динаміку. Field policy enforced у backend (RBAC §6.2)."

---

## 8. Role switch → Психолог (1 хв)

1. Role switcher → **"Психолог"** → **`/medic`**.
2. Показати:
   - chip-фільтри ризик / статус кейсу;
   - список priority cases.
3. Відкрити кейс → **`/medic/cases/<case_id>`**:
   - детальніша інформація (включно з recent daily / weekly даними);
   - можна змінити статус кейсу (new → in_review → monitoring → closed);
   - можна додати нотатку.
4. Додати тестову нотатку → "Зберегти" → з'являється у списку нотаток.

> Меседж: "Психолог бачить більше даних ніж командир (включно з raw scores), може вести кейс, додавати нотатки. Все — у audit log."

---

## 9. Role switch → Адмін (45 с)

1. Role switcher → **"Адміністратор"** → **`/admin`**.
2. KPI: усього користувачів / активних / деактивованих / підрозділів.
3. Відкрити **"Користувачі"** → таблиця users з ролями (UA-лейбли) + статусом.
4. Відкрити **"Журнал подій"** (audit log):
   - фільтр за типом події;
   - події `password_changed`, `role_assigned`, `case_status_updated` тощо.

> Меседж: "Audit log фіксує усі security/clinical events. Все, що показує психолог, командир, або soldier — фіксовано на backend."

---

## 10. Settings + Logout (45 с)

1. Header → **"Налаштування"** → **`/settings/profile`**:
   - змінити імʼя → "Зберегти" → success alert.
2. Підпункт **"Безпека"** → **`/settings/security`**:
   - змінити пароль (current + new + confirm).
   - Показати валідацію: ввести неправильний поточний → читабельний UA error "Перевірте поточний пароль" (без stack trace).
3. Header → **"Вийти"** → редірект на `/login`.

> Меседж: "Settings — final piece P0-UX-1 (EPIC-84). Logout invalidate-ить session і revoke-ить sibling sessions з інших девайсів."

---

## 11. Resilience demo (опціонально, 30 с)

1. **404**: ввести URL `/this-does-not-exist` → custom Ukrainian 404 page із "Повернутись на головну".
2. **Mobile**: відкрити iPhone DevTools view (375×667) → переконатись що нема горизонтального overflow на login / dashboard / baseline.
3. **`/health`** (frontend) + **`/api/v1/health`** (backend) → 200.

---

## Завершення (15 с)

> "Це P0 — фокус на flow, не на дизайні. Reaction test працює, multi-role + RBAC працюють, audit log фіксує. Наступний крок — pilot з реальним підрозділом, потім P1 (повніша адмінка + PDF-export + monitoring)."

---

## Technical fallback (якщо щось ламається)

| Симптом | Що зробити |
|---|---|
| Login висить на "Вхід..." | Перевірити backend `/api/v1/health`. Якщо 404 — перезапустити uvicorn. |
| Reaction тест не стартує | Hard reload (Cmd+Shift+R) — старий JS chunk. |
| Commander dashboard порожній | Скоріше за все, demo seed без recent daily/weekly. Запустити `make seed-demo`. |
| 401/403 у мід-кейсі | Cookie expired (30 днів). Logout → login заново. |
| Mobile horizontal scroll | Відкрити DevTools → Console → перевірити CSS warnings. EPIC-85 має покривати всі основні екрани. |
