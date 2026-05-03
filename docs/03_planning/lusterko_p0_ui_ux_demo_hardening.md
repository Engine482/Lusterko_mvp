# Люстерко MVP — P0 Appendix: UI/UX Stabilization & Demo Hardening

## Призначення документа

Цей документ є додатком до наявного P0 scope MVP «Люстерко».

Мета — не розширювати продукт за межі P0, а довести вже робочий MVP до презентаційного, мобільно-стабільного та демо-готового стану.

Поточний стан:

- застосунок уже реалізований згідно P0 scope;
- застосунок задеплоєний на Railway;
- застосунок відкривається на домені користувача;
- основна логіка працює;
- дизайн і системне UI-тестування були пропущені;
- на iPhone Safari видно проблеми з адаптивністю;
- немає кнопки logout;
- зміна паролю доступна лише через reset-flow;
- немає зміни імені в особистому кабінеті;
- reaction-time test не запускається;
- через це військовий baseline неможливо завершити.

Основна задача цього етапу: **demo hardening**.

---

## 1. Product boundary

Цей етап залишається в межах P0.

### Входить у scope

1. Automated UI testing для ключових flow.
2. Тестування smartphone, tablet і desktop viewports.
3. Фікс критичних функціональних блокерів.
4. Фікс мобільної та планшетної верстки.
5. Додавання мінімальних account-management функцій.
6. Легкий презентаційний редизайн.
7. Favicon/app icons/metadata.
8. Footer identity/version badge.
9. About/disclaimer.
10. Empty/loading/error/success states.
11. Базова accessibility-перевірка.
12. Ukrainian UI copy pass.
13. 404 page.
14. Health check endpoint.
15. Final regression і demo checklist.

### Не входить у scope

- повноцінний брендбук;
- складна дизайн-система;
- кастомні ілюстрації;
- складні анімації;
- PDF export;
- CSV export;
- email notifications;
- Google Analytics;
- складна адмінка;
- складний permission management понад уже наявні ролі;
- multilingual system;
- повний monitoring stack;
- продуктові фічі поза P0.

---

## 2. Recommended implementation order

Правильний порядок робіт:

1. Додати Playwright / automated UI tests.
2. Зафіксувати поточні failing flows.
3. Полагодити reaction-time test.
4. Забезпечити military baseline end-to-end completion.
5. Додати logout.
6. Додати зміну паролю в settings.
7. Додати зміну імені в settings.
8. Полагодити smartphone/tablet layout issues.
9. Додати favicon, metadata, footer identity, about/disclaimer, 404, health check.
10. Додати empty/loading/error/success states.
11. Зробити lightweight presentation redesign.
12. Запустити regression tests.
13. Перевірити production build і Railway deploy.
14. Провести manual iPhone Safari demo pass.

Не починати з «зробити красиво». Спочатку потрібно прибрати блокери й закріпити flow тестами.

---

## 3. Critical P0 blockers

### 3.1. Reaction-time test does not start

Поточна проблема:

- reaction-time test не запускається;
- користувач не може завершити military baseline;
- це блокує один із ключових сценаріїв MVP.

Required fix:

- знайти причину, чому тест не стартує;
- перевірити client-side state machine;
- перевірити click/touch handlers;
- перевірити timer logic;
- перевірити mobile/touch interaction;
- перевірити hydration/client-side errors;
- перевірити save result flow;
- додати automated test на старт, проходження і збереження результату.

Acceptance criteria:

```text
Given user starts military baseline
When user reaches reaction-time test
Then reaction-time test starts correctly
And works with mouse input
And works with touch input
And result is saved
And user can continue the baseline
And military baseline can be completed end-to-end
```

---

## 4. Account management features

### 4.1. Logout

Додати видимий logout.

Рекомендовані місця:

- user menu;
- settings/account page;
- mobile navigation/header if appropriate.

Acceptance criteria:

```text
Given user is logged in
When user clicks Logout
Then session/token is cleared
And user is redirected to login screen
And protected routes require login again
And browser Back button does not reveal private dashboard data after logout
```

Security notes:

- logout має реально очищати session/token;
- protected routes мають лишатися protected після logout;
- не можна просто приховувати UI без invalidation/cleanup.

---

### 4.2. Change password in settings

Додати Settings → Security / Account Security.

Fields:

- current password;
- new password;
- confirm new password.

Validation:

- current password required;
- new password required;
- confirm password must match;
- бажано мінімум 8 символів;
- password inputs мають бути `type="password"`;
- помилки мають бути людською українською мовою;
- production UI не має показувати raw stack traces.

Acceptance criteria:

```text
Given user is logged in
When user enters valid current password and matching new password
Then password is updated
And user sees a clear success confirmation
```

Failure states:

```text
Given user enters wrong current password
Then user sees a readable Ukrainian error message
And no raw technical error is exposed
```

---

### 4.3. Change display name in settings

Додати Settings → Profile.

Fields:

- display name / ім’я.

Acceptance criteria:

```text
Given user is logged in
When user changes display name
Then new name is saved
And visible in the interface after refresh
```

---

## 5. Automated UI testing

### 5.1. Recommended tool

Use **Playwright**.

Reason:

- good browser automation;
- supports Chromium/WebKit/Firefox;
- works well for mobile/tablet viewport testing;
- suitable for end-to-end flows;
- can capture screenshots/videos/traces for debugging.

---

### 5.2. Browser and viewport coverage

Minimum coverage:

#### Desktop

```text
- Desktop Chromium
- Desktop Safari/WebKit if feasible
```

#### Smartphones

```text
- iPhone 14/15/16 Pro Max-like viewport
- iPhone SE/small viewport if feasible
- Android Chrome-like viewport
```

#### Tablets

```text
- iPad Mini portrait
- iPad 10/11-inch portrait
- iPad 10/11-inch landscape
- iPad Pro 12.9-inch landscape
- Android tablet landscape
```

Tablet acceptance criteria:

```text
[ ] dashboard does not look broken or excessively stretched
[ ] forms have reasonable max-width
[ ] cards/grids adapt cleanly
[ ] baseline flow works with touch input
[ ] no horizontal overflow
[ ] primary actions remain visible
[ ] navigation works in portrait and landscape
```

---

### 5.3. Core test suites

#### Auth

```text
[ ] login works
[ ] logout works
[ ] protected route redirects when logged out
[ ] browser Back after logout does not reveal protected private content
```

#### Account settings

```text
[ ] user can open settings
[ ] user can change display name
[ ] user can change password
[ ] validation errors are readable
[ ] success states are visible
```

#### Role switching

```text
[ ] user with multiple roles can switch roles
[ ] UI updates after role switch
[ ] current role is clearly visible
```

#### Military baseline

```text
[ ] user can start military baseline
[ ] user can progress through all baseline steps
[ ] reaction-time test starts
[ ] reaction-time test completes
[ ] baseline result is saved
[ ] military baseline can be completed end-to-end
```

#### Mobile/tablet layout

```text
[ ] no horizontal scroll on key screens
[ ] primary action buttons are visible
[ ] forms fit within viewport
[ ] touch targets are usable
[ ] dashboard cards do not overflow
[ ] modals/dialogs fit viewport
```

#### Error/loading states

```text
[ ] loading state appears during async submit
[ ] button is disabled during submit where appropriate
[ ] network/API error is shown as readable Ukrainian message
[ ] no raw stack traces in production UI
```

#### Optional visual regression

Add screenshots for:

```text
[ ] login screen
[ ] dashboard
[ ] baseline flow
[ ] reaction-time test
[ ] settings/profile
[ ] settings/security
[ ] role switch UI
[ ] mobile dashboard
[ ] tablet dashboard
```

---

## 6. Mobile and tablet layout requirements

Main goals:

- no horizontal overflow;
- no clipped buttons;
- readable text;
- reasonable spacing;
- touch-friendly controls;
- forms not too wide on tablets;
- dashboards not chaotic on tablets;
- baseline flow comfortable on mobile/touch devices.

Minimum layout rules:

```text
- Mobile-first layout
- Mobile page padding: 16px
- Tablet page padding: 24px if appropriate
- Desktop page padding: 24–32px
- Max form width: 420–480px
- Dashboard max width: 1100–1280px
- Minimum touch target: 44px
- Avoid fixed pixel widths that break mobile
- Avoid 100vw patterns that cause overflow with scrollbars
- Ensure modals/dialogs fit small screens
- Ensure sticky headers/footers do not cover primary actions
```

---

## 7. Lightweight presentation redesign

### 7.1. Design direction

Recommended style:

**Clinical tactical minimalism**.

The app should feel like:

- serious;
- reliable;
- medical/psychophysiological;
- govtech/defense-compatible;
- calm;
- modern;
- not playful;
- not overdesigned;
- not “generic AI landing page”.

Target feel:

```text
Linear + Vercel dashboard + сучасний медичний кабінет + тактична стриманість
```

Avoid:

```text
- neon hacker aesthetic
- toy-like mental health app style
- excessive glassmorphism
- aggressive military visuals
- overloaded gradients
- decorative UI that hurts usability
```

---

### 7.2. Suggested design tokens

```text
Background primary: #0B1120
Background secondary: #111827
Card background: #172033
Border: #263246
Primary accent: #38BDF8
Secondary accent: #2DD4BF
Text primary: #F8FAFC
Text secondary: #CBD5E1
Muted text: #94A3B8
Success: #22C55E
Warning: #F59E0B
Danger: #EF4444
```

Typography:

```text
Font: Inter or system-ui / -apple-system
Base size: 16px
Mobile body minimum: 16px
Headings: 24–32px
Cards: 14–16px
Buttons: 15–16px
```

Shape/spacing:

```text
Card radius: 16–20px
Button radius: 12px
Input radius: 10–12px
Minimum touch target: 44px
Mobile page padding: 16px
Desktop page padding: 24–32px
```

---

### 7.3. Screens to update

Apply lightweight redesign to existing screens only:

```text
[ ] login/register/auth screens
[ ] dashboards
[ ] role switch UI
[ ] military baseline flow
[ ] reaction-time test screen
[ ] settings/profile
[ ] settings/security
[ ] commander view
[ ] psychologist view
[ ] error/loading/empty states
[ ] 404 page
```

Do not over-engineer a full design system, but centralize tokens/styles enough to avoid inconsistent UI.

---

## 8. Presentation polish tasks

### 8.1. Favicon and app icons

Add:

```text
[ ] favicon.ico
[ ] favicon.svg or favicon.png
[ ] apple-touch-icon.png
[ ] manifest icon 192x192 if manifest exists
[ ] manifest icon 512x512 if manifest exists
```

Preferred icon concept:

```text
Schematic mirror whose contour resembles a transverse cross-section of the human brain.
```

If final icon asset is not available, add a clean temporary favicon that matches the Lusterko identity and can be replaced later.

---

### 8.2. Page title and metadata

Add proper metadata.

Suggested title:

```text
Люстерко — моніторинг стану особового складу
```

Suggested description:

```text
MVP системи короткого психофізіологічного самозвіту, baseline-оцінки та командирського огляду стану підрозділу.
```

Add if applicable:

```text
[ ] Open Graph title
[ ] Open Graph description
[ ] Open Graph image if available
[ ] theme-color
[ ] mobile web app capable metadata
```

Suggested theme color:

```text
#0B1120
```

---

### 8.3. Footer identity and version badge

Add restrained footer/project identity.

Suggested footer:

```text
Люстерко MVP · Volodymyr Motornyi · 2026
```

Optional version badge:

```text
P0 · v0.1.0 · demo
```

Optional build info:

```text
Build: 2026-05-03
Environment: demo
```

Rules:

- do not expose demo credentials publicly in UI;
- do not expose secrets;
- commit hash may be shown only if already safe and intentional;
- footer should not clutter main workflows.

---

### 8.4. About page or modal

Add a short “Про систему” page/modal.

Suggested copy:

```text
Люстерко — MVP системи для короткої оцінки функціонального стану, самозвіту та огляду динаміки стану особового складу.

Цей демо-застосунок призначений для перевірки концепції, презентації логіки сценаріїв та збору первинного зворотного зв’язку.
```

Goal:

- a user who opens the demo without verbal context should understand what the system is within 10 seconds.

---

### 8.5. Demo/privacy disclaimer

Because the product touches psychophysiological/medical/defense-adjacent context, add a concise disclaimer.

Suggested copy:

```text
Демо-версія. Дані, введені в систему, використовуються лише для демонстрації роботи MVP. Система не є медичним діагностичним інструментом і не замінює консультацію фахівця.
```

If there are demo/synthetic records, add:

```text
Демо-середовище · тестові дані
```

Do not make this legally heavy. It should be short, visible where relevant, and not block the workflow.

---

### 8.6. Demo account handling

Do not show passwords or credentials in the public UI.

Allowed in UI:

```text
Поточна роль: Військовий
Доступні ролі: Командир, Психолог
```

Allowed in private README/demo script only:

```text
Demo user:
email: ...
password: ...
roles: soldier, commander, psychologist
```

---

## 9. UI states

### 9.1. Empty states

Replace empty blank sections with useful Ukrainian messages.

Examples:

```text
Поки немає записів baseline. Пройдіть першу оцінку, щоб побачити динаміку стану.
```

```text
Поки немає підлеглих у цьому демо-акаунті.
```

```text
Поки немає користувачів із позначеними ризиковими станами.
```

Empty screens without explanation should be treated as UX bugs.

---

### 9.2. Loading states

Add loading states for:

```text
[ ] dashboard data loading
[ ] login submit
[ ] baseline step save
[ ] reaction-time test initialization
[ ] profile update
[ ] password update
```

Examples:

```text
Завантаження...
Збереження...
Завантаження baseline...
Оновлення профілю...
```

Buttons should be disabled during submit where duplicate submit may cause bugs.

---

### 9.3. Error states

Replace raw errors with readable Ukrainian errors.

Bad:

```text
Error 500
Request failed
Cannot read properties of undefined
```

Good:

```text
Не вдалося зберегти результат. Перевірте з’єднання та спробуйте ще раз.
```

```text
Не вдалося змінити пароль. Перевірте поточний пароль і спробуйте ще раз.
```

```text
Не вдалося завантажити дані. Оновіть сторінку або спробуйте пізніше.
```

Required:

```text
[ ] login error
[ ] baseline save error
[ ] password change error
[ ] profile update error
[ ] reaction test error
[ ] network/API error
```

Production UI must not expose raw stack traces.

---

### 9.4. Success states

Add confirmation after successful actions.

Required:

```text
[ ] Ім’я оновлено
[ ] Пароль змінено
[ ] Результат baseline збережено
[ ] Ви вийшли з акаунта
```

---

## 10. Accessibility baseline

This is not a full WCAG audit, but a minimum accessibility pass is required.

Checklist:

```text
[ ] visible focus states
[ ] inputs have labels
[ ] icon buttons have aria-labels
[ ] touch targets are at least 44px
[ ] sufficient contrast for main text and controls
[ ] statuses are not communicated by color alone
[ ] forms are keyboard usable
[ ] errors are associated with relevant fields where practical
```

Rationale:

- users may be tired, stressed, sleep-deprived, concussed, or using the app in poor lighting;
- defense/medical-adjacent tools should not rely on fragile UI patterns.

---

## 11. Ukrainian UI copy pass

Ensure interface copy is consistently Ukrainian.

Checklist:

```text
[ ] buttons are Ukrainian
[ ] settings labels are Ukrainian
[ ] errors are Ukrainian
[ ] success messages are Ukrainian
[ ] baseline instructions are Ukrainian
[ ] role names are Ukrainian
[ ] empty states are Ukrainian
[ ] avoid unnecessary English terms
```

English technical terms may remain only where genuinely appropriate.

Suggested role labels:

```text
Військовий
Командир
Психолог
```

---

## 12. 404 / fallback page

Add clean fallback page.

Suggested copy:

```text
Сторінку не знайдено

Такої сторінки немає або посилання застаріло.

Повернутися на головну
```

Acceptance criteria:

```text
Given user opens an unknown route
Then user sees a clean 404 page
And can return to the main app
```

---

## 13. Health check endpoint

Add `/health` endpoint if not already present.

Example response:

```json
{
  "status": "ok",
  "service": "lusterko",
  "environment": "demo"
}
```

Acceptance criteria:

```text
Given /health is requested
Then it returns 200 OK
And includes basic service/environment info
And exposes no secrets
```

Useful for:

- Railway health checks;
- deployment debugging;
- quick production sanity check.

---

## 14. Basic security polish

Minimum checklist:

```text
[ ] password fields use type="password"
[ ] logout clears session/token
[ ] protected routes remain protected after logout
[ ] browser Back after logout does not reveal private dashboard data
[ ] no credentials in frontend code
[ ] no secrets in repository
[ ] no stack traces in production UI
[ ] demo credentials are not visible in public UI
```

Do not implement complex security architecture in this sprint unless required by the existing stack.

---

## 15. Analytics/logging decision

Do not add Google Analytics in this sprint.

Reason:

- military/medical-adjacent demo;
- privacy questions;
- not necessary for P0 demo hardening.

Acceptable:

```text
[ ] server-side error logs
[ ] browser console errors fixed
[ ] optional minimal internal logging if already present
```

Possible later:

```text
- Sentry
- privacy-conscious analytics
- structured audit logs
```

Do not add these now if they slow down demo readiness.

---

## 16. Sprint structure

### Sprint P0-UX-1 — Stabilization

Tasks:

```text
[ ] Add Playwright
[ ] Add smoke tests for core flows
[ ] Capture current failures
[ ] Fix reaction-time test
[ ] Ensure military baseline can complete end-to-end
[ ] Add logout
[ ] Add display name change
[ ] Add password change
[ ] Fix obvious mobile/tablet layout blockers
```

Result:

```text
MVP is functionally complete and baseline can be finished.
```

---

### Sprint P0-UX-2 — Presentation polish

Tasks:

```text
[ ] Apply lightweight design tokens
[ ] Improve buttons/forms/cards
[ ] Update auth screens
[ ] Update dashboard screens
[ ] Update baseline screens
[ ] Update settings screens
[ ] Add favicon/app icons
[ ] Add metadata/theme-color
[ ] Add footer identity/version badge
[ ] Add About page/modal
[ ] Add demo/privacy disclaimer
[ ] Add 404 page
[ ] Add health endpoint
[ ] Add empty/loading/error/success states
[ ] Ukrainian UI copy pass
[ ] Accessibility baseline pass
```

Result:

```text
MVP looks clean, serious, modern, and presentation-ready.
```

---

### Sprint P0-UX-3 — Regression and deploy

Tasks:

```text
[ ] Run automated tests
[ ] Run mobile viewport tests
[ ] Run tablet viewport tests
[ ] Run desktop tests
[ ] Run lint/typecheck/build according to stack
[ ] Manual iPhone Safari test
[ ] Manual desktop Safari/Chrome test
[ ] Verify Railway deployment
[ ] Verify domain/subdomain
[ ] Verify demo account
[ ] Prepare short demo script/checklist
```

Result:

```text
MVP is ready to show to external stakeholders.
```

---

## 17. Demo readiness checklist

Before demo:

```text
[ ] App opens on production domain
[ ] Railway deployment is healthy
[ ] /health returns OK
[ ] Login works
[ ] Logout works
[ ] Protected routes are protected after logout
[ ] Role switch works
[ ] Current role is clearly visible
[ ] Military baseline starts
[ ] Reaction-time test starts
[ ] Reaction-time test works on touch input
[ ] Military baseline completes end-to-end
[ ] Baseline result is saved
[ ] Commander view opens
[ ] Psychologist view opens
[ ] Settings opens
[ ] Display name can be changed
[ ] Password can be changed
[ ] No horizontal overflow on iPhone viewport
[ ] No horizontal overflow on iPad viewport
[ ] Primary buttons are not clipped
[ ] Forms are usable on smartphone
[ ] Forms are usable on tablet
[ ] Footer identity/version is visible but not intrusive
[ ] Favicon appears in browser tab
[ ] Metadata/title are correct
[ ] About/disclaimer exists
[ ] 404 page exists
[ ] Empty states are readable
[ ] Loading states exist
[ ] Error messages are readable and Ukrainian
[ ] No raw stack traces in production UI
[ ] No secrets or credentials exposed in frontend
[ ] UI copy is consistently Ukrainian
[ ] Test/demo account with multiple roles is ready
[ ] Short demo script is ready
```

---

## 18. Claude Code / Codex task prompt

Use the following as the implementation prompt.

```text
You are working on the existing deployed MVP of the Lusterko app.

Context:
The app already implements the P0 scope and is deployed on Railway under the user's domain. The app is functional, but proper design and systematic UI testing were skipped. The current goal is NOT to expand the product beyond P0. The goal is to stabilize the MVP, fix mobile/tablet layout issues, add minimal account-management UX, repair a critical broken baseline flow, and apply a lightweight presentation-grade visual redesign.

Primary goals:
1. Add automated UI testing for core flows and smartphone/tablet/desktop viewports.
2. Fix mobile and tablet layout issues, especially on iPhone Safari-like and iPad Safari-like viewports.
3. Fix the reaction-time test, which currently does not start and blocks completion of the military baseline.
4. Add logout functionality.
5. Add password change inside user settings.
6. Add display name change inside user settings.
7. Add lightweight presentation polish: favicon/app icons, metadata, footer identity/version, about/disclaimer, empty/loading/error/success states, 404 page, health endpoint, accessibility baseline, Ukrainian UI copy pass.
8. Apply a lightweight, modern, presentation-grade UI redesign without changing product scope.
9. Re-run tests and ensure the MVP is demo-ready.

Important constraint:
Do not introduce large new product features. Treat this as Appendix to P0: UI/UX Stabilization & Demo Hardening.

Recommended implementation order:
1. Inspect current stack and app structure.
2. Add Playwright tests.
3. Capture current failing flows.
4. Fix reaction-time test.
5. Ensure military baseline can complete end-to-end.
6. Add logout.
7. Add password change in settings.
8. Add display name change in settings.
9. Fix smartphone/tablet layout issues.
10. Add presentation polish items.
11. Apply lightweight redesign.
12. Run regression tests.
13. Verify production build/deploy readiness.

Recommended design direction:
Clinical tactical minimalism.
The app should feel like a serious, reliable healthtech/govtech/defense dashboard, not like a playful consumer app. Use a restrained dark navy/graphite visual system with clean cards, good spacing, readable typography, clear buttons, and subtle cyan/teal accents.

Suggested design tokens:
- Background primary: #0B1120
- Background secondary: #111827
- Card background: #172033
- Border: #263246
- Primary accent: #38BDF8
- Secondary accent: #2DD4BF
- Text primary: #F8FAFC
- Text secondary: #CBD5E1
- Muted text: #94A3B8
- Success: #22C55E
- Warning: #F59E0B
- Danger: #EF4444
- Font: Inter or system-ui
- Card radius: 16–20px
- Button radius: 12px
- Minimum touch target: 44px
- Mobile page padding: 16px

Step 1 — Audit:
Inspect the current codebase, routing, auth implementation, baseline flow, reaction-time test implementation, settings/account pages, layout system, styling setup, and deployment assumptions.
Identify the stack and avoid unnecessary rewrites.

Step 2 — Automated testing:
Add Playwright if not present.
Create tests for:
- login
- logout
- protected route redirect after logout
- browser Back after logout does not reveal private dashboard data
- role switching
- opening settings
- changing display name
- changing password
- starting military baseline
- progressing through all military baseline steps
- starting and completing reaction-time test
- completing military baseline
- mobile/tablet layout sanity checks

Test viewports:
- Desktop Chromium
- Mobile Safari-like WebKit viewport
- iPhone 14/15/16 Pro Max-like viewport
- iPhone SE/small viewport if feasible
- Android Chrome-like viewport
- iPad Mini portrait
- iPad 10/11-inch portrait
- iPad 10/11-inch landscape
- iPad Pro 12.9-inch landscape
- Android tablet landscape

Add layout assertions where practical:
- no horizontal scroll on key screens
- primary action buttons visible
- forms fit within viewport
- dashboard cards do not overflow
- modals/dialogs fit viewport
- no obvious console errors during key flows

Step 3 — Fix blockers:
Fix the reaction-time test so it starts, runs, captures user interaction correctly, saves the result, and allows the military baseline to complete.
Make sure it works with mouse and touch input.

Acceptance criteria:
- reaction-time test starts
- reaction-time test completes
- result is saved
- military baseline can be completed end-to-end
- works on mobile/touch viewport

Step 4 — Account UX:
Add logout.
Add display name change in Settings/Profile.
Add password change in Settings/Security with:
- current password
- new password
- confirm new password
- validation
- success state
- clear error state

Security requirements:
- password inputs use type="password"
- logout clears session/token
- protected routes remain protected after logout
- browser Back after logout should not reveal private data
- no credentials or secrets in frontend code
- no raw stack traces in production UI

Step 5 — Mobile/tablet UI fixes:
Fix all layout issues discovered in testing.
Prioritize:
- no horizontal overflow
- responsive forms
- readable cards
- buttons not clipped
- safe mobile spacing
- proper viewport behavior
- touch-friendly controls
- tablet dashboard not excessively stretched
- tablet forms have reasonable max-width

Step 6 — Presentation polish:
Add:
1. Favicon and app icons:
   - favicon.ico
   - favicon.svg or png
   - apple-touch-icon
   - web manifest icons if applicable

2. Page metadata:
   - title: “Люстерко — моніторинг стану особового складу”
   - description: “MVP системи короткого психофізіологічного самозвіту, baseline-оцінки та командирського огляду стану підрозділу.”
   - Open Graph title/description if applicable
   - theme-color: #0B1120
   - mobile web app metadata where appropriate

3. Footer/project identity:
   - show “Люстерко MVP”
   - show “Volodymyr Motornyi” attribution
   - show version/build label such as “P0 · v0.1.0 · demo”
   - do NOT expose demo credentials publicly in the UI

4. About page or modal:
   Add short explanation:
   “Люстерко — MVP системи для короткої оцінки функціонального стану, самозвіту та огляду динаміки стану особового складу.

   Цей демо-застосунок призначений для перевірки концепції, презентації логіки сценаріїв та збору первинного зворотного зв’язку.”

5. Demo/privacy disclaimer:
   Add concise disclaimer:
   “Демо-версія. Дані, введені в систему, використовуються лише для демонстрації роботи MVP. Система не є медичним діагностичним інструментом і не замінює консультацію фахівця.”

   If applicable, add:
   “Демо-середовище · тестові дані”

6. Empty/loading/error/success states:
   Replace raw or empty UI states with clear Ukrainian messages.
   Add loading states for dashboard, forms, and baseline submission.
   Add success states after profile update, password change, and baseline save.
   Ensure production UI does not expose raw stack traces.

7. Accessibility baseline:
   - visible focus states
   - inputs have labels
   - icon buttons have aria-labels
   - touch targets at least 44px
   - sufficient text contrast
   - statuses are not communicated by color alone
   - forms are keyboard usable

8. Ukrainian UI copy pass:
   Ensure interface copy is consistently Ukrainian.
   Avoid unnecessary English in buttons, settings, errors, and baseline instructions.
   Suggested role labels:
   - Військовий
   - Командир
   - Психолог

9. 404 page:
   Add a clean fallback page:
   “Сторінку не знайдено. Такої сторінки немає або посилання застаріло. Повернутися на головну.”

10. Health check:
   Add /health endpoint if not present.
   It should return a simple OK response with service/environment info and expose no secrets.

Step 7 — Lightweight redesign:
Apply a lightweight redesign across existing screens:
- login/register/auth screens
- dashboards
- baseline flow
- reaction-time test screen
- settings
- role switch UI
- commander view
- psychologist view
- buttons
- forms
- cards
- alerts
- loading states
- empty states
- 404 page

Do not over-engineer a design system, but centralize tokens/styles enough that the UI is consistent.

Step 8 — Verification:
Run lint/typecheck/tests/build according to the project stack.
Run Playwright tests.
Document remaining known issues if any.
Ensure app is ready for Railway redeploy.

Deliverables:
1. Code changes.
2. Playwright test suite.
3. Short markdown report:
   - what was broken
   - what was fixed
   - what tests were added
   - how to run tests
   - remaining risks
4. Demo readiness checklist.

Acceptance criteria:
- The app has a visible logout option.
- User can change password from settings.
- User can change display name from settings.
- Reaction-time test starts and completes.
- Military baseline can be completed end-to-end.
- Main screens work on mobile Safari-like viewport.
- Main screens work on iPad/tablet viewports.
- No horizontal overflow on key mobile/tablet screens.
- UI has favicon/app metadata/footer identity/about/disclaimer.
- UI has readable empty/loading/error/success states.
- UI copy is consistently Ukrainian.
- Basic accessibility pass is complete.
- 404 page exists.
- /health endpoint exists.
- No secrets or demo credentials are exposed in frontend code.
- UI looks clean, modern, serious, and presentation-ready.
- Automated UI tests cover the critical flows.
- App builds successfully and can be redeployed to Railway.

Do not add:
- Google Analytics
- PDF export
- CSV export
- email notifications
- large new admin features
- full brandbook
- complex monitoring stack
- multilingual system
- feature work outside P0 demo hardening
```

---

## 19. Expected final state

After this work, the MVP should feel like:

```text
A serious early-stage healthtech/govtech/defense demo that works reliably on smartphone, tablet, and desktop, has clean presentation polish, does not expose obvious prototype rough edges, and can be shown to external stakeholders without first apologizing for the UI.
```

The priority is not perfect beauty. The priority is:

1. key flow works;
2. mobile/tablet presentation does not break;
3. account UX is not embarrassing;
4. design feels intentional;
5. demo risk is low.
