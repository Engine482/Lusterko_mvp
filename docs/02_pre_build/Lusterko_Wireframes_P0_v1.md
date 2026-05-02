# Lusterko — Wireframes P0 v1

## 1. Призначення документа
`Wireframes P0` фіксує:
- які саме екрани є в MVP
- що на кожному екрані є обов’язковим
- яка одна головна дія на екрані
- які є стани `loading / empty / error / success`
- як виглядає навігація по ролях
- які блоки є обов’язковими, а які не входять у P0

Це не UI-kit і не візуальний дизайн. Це структурна схема інтерфейсу.

## 2. Глобальні UX-принципи P0
- Один екран — одна головна дія
- Мінімум когнітивного шуму
- Role-driven UI
- Mobile-first для soldier
- Desktop-friendly для commander / medic / admin
- Пояснюваність без псевдоклініки

## 3. Глобальна структура екранів P0
### Shared / Auth
1. Login Screen
2. Invite Landing Screen (set initial password)
3. Forgot Password Screen
4. Reset Password Screen
5. Role Selection Screen
6. Global Role Switcher

### Soldier
5. Soldier Home
6. Baseline Step: PHQ-4
7. Baseline Step: PSS-4
8. Baseline Step: Sleep
9. Baseline Step: Reaction Test
10. Baseline Step: Go / No-Go
11. Baseline Completion Screen
12. Daily Check-in
13. Daily Success / Confirmation
14. Weekly Reassessment
15. Cognitive Task Launcher
16. Reaction Test Screen
17. Go / No-Go Screen
18. Completion Summary

### Commander
19. Commander Dashboard
20. Commander Cases List
21. Commander Case Card

### Medic / psychologist
22. Medic Priority Cases List
23. Medic Detailed Case View
24. Add Note / Update Case Status block

### Admin
25. Admin Dashboard
26. Users List
27. Create User
28. User Profile / Edit User
29. Units Screen
30. Audit Log Screen

## 4. Shared / Auth wireframes

> **Sprint 7 update:** Wireframes oновлено під email+password флоу
> (`docs/06_decisions/2026-05-02-auth-email-password.md`). Google OAuth
> сторінки прибрано.

### 4.1 Login Screen
Layout:
- Header: логотип / назва "Люстерко"
- Form: `email`, `password`, CTA `Увійти`
- Link: `Забули пароль?`

States:
- `idle`
- `submitting`
- `error: UNAUTHORIZED` — generic "невірний email або пароль"
- `error: ACCOUNT_LOCKED` — повідомлення з retry-after; не розкриває чи акаунт реальний

### 4.2 Invite Landing Screen
Layout:
- Header: логотип
- Main block: короткий текст про встановлення паролю
- Form fields:
  - `token` (prefilled з URL, read-only або редагований)
  - `full_name` (editable, prefilled з admin-input)
  - `password` (min 12 chars)
  - `confirm password`
- CTA `Встановити пароль і увійти`

States:
- `valid invite`
- `error: INVALID_INVITE`
- `error: INVITE_EXPIRED`
- `error: WEAK_PASSWORD`
- `error: ACCOUNT_LOCKED`

### 4.3 Forgot Password Screen
Layout:
- Form: `email`, CTA `Надіслати посилання`
- Link: `Назад до входу`

After-submit state (always identical, незалежно від існування акаунту):
- "Якщо введена адреса зареєстрована в Lusterko — на неї надійде лист
  із посиланням для скидання паролю. Посилання дійсне 1 годину."

### 4.4 Reset Password Screen
Layout:
- Form: `token` (prefilled з URL), `new password`, `confirm`, CTA `Зберегти пароль`

States:
- `idle`
- `submitting`
- `error: INVALID_RESET_TOKEN` / `RESET_TOKEN_EXPIRED` / `WEAK_PASSWORD`

Після успішного збереження — користувач залогінений автоматично, всі
попередні сесії припинені.

### 4.5 Role Selection Screen
Role cards:
- Військовослужбовець
- Командир
- Медик / психолог
- Адміністратор

Кожна картка містить назву ролі, короткий опис і CTA `Увійти як ...`.

### 4.6 Global Role Switcher
- показує поточну active role
- відкриває список доступних ролей
- після switch очищається role-scoped cache і йде redirect на role home

## 5. Soldier wireframes
### 5.1 Soldier Home
Header:
- привітання
- поточна дата
- role switcher

Main status card:
- поточний стан
- current risk status
- коротке explanation text

Due tasks block:
- baseline step due
- daily due
- weekly due
- cognitive due

Recent activity:
- останні виконані дії

### 5.2 Baseline Flow — загальні правила
Кожен baseline step — окремий екран.

Fixed layout:
- Step X / 5
- progress bar
- question block
- primary CTA `Далі`
- secondary CTA `Зберегти і вийти`

### 5.3 Baseline PHQ-4 Screen
- заголовок
- 4 питання на одному екрані
- CTA `Далі`

### 5.4 Baseline PSS-4 Screen
- 4 питання
- шкали відповіді
- CTA `Далі`

### 5.5 Baseline Sleep Screen
- заголовок “Сон”
- одна шкала 0–10
- CTA `Далі`

### 5.6 Baseline Reaction Test Screen
- instruction card
- `Почати тест`
- stimulus area
- progress indicator
- end state з CTA `Далі`

### 5.7 Baseline Go / No-Go Screen
- коротка інструкція
- `Почати тест`
- зона стимулу
- progress
- end state з CTA `Завершити baseline`

### 5.8 Baseline Completion Screen
- confirmation state
- текст про сформований базовий профіль
- CTA `Перейти на головний екран`

### 5.9 Daily Check-in Screen
- дата
- 4 шкали:
  - Сон
  - Енергія
  - Загальний стан / настрій
  - Концентрація
- optional comment
- primary CTA `Зберегти`

Усе на одному екрані.

### 5.10 Daily Success / Confirmation Screen
- підтвердження збереження
- поточний статус
- коротке explanation text
- CTA `Повернутися на головний екран`

### 5.11 Weekly Reassessment Screen
- PHQ-4
- PSS-4
- CTA `Зберегти результати`

### 5.12 Cognitive Task Launcher
- картка реакції
- картка Go / No-Go
- short explanation
- CTA на кожну задачу

### 5.13 Reaction Test Screen
### 5.14 Go / No-Go Screen
Обидва мають:
- instruction state
- in-progress state
- completion state

### 5.15 Completion Summary Screen
- daily: done / due
- weekly: done / due
- cognitive: done / due
- last risk status
- CTA `Повернутися на головний`

## 6. Commander wireframes
### 6.1 Commander Dashboard
- unit name
- role switcher
- last updated
- KPI row: Green / Yellow / Red / Insufficient data
- main cases block
- filters all / yellow / red

### 6.2 Commander Cases List
- filters
- search by name
- list/table of cases

### 6.3 Commander Case Card
- user name
- current status
- updated_at
- explanation block
- recent trend
- без deep details, raw AI, medic notes

## 7. Medic / psychologist wireframes
### 7.1 Medic Priority Cases List
- unit header
- role switcher
- filters by case status and risk
- cases list

### 7.2 Medic Detailed Case View
Секції:
- current risk
- latest daily
- latest weekly
- latest cognitive
- AI summary
- notes
- action block: change status / add note

### 7.3 Add Note / Update Case Status block
- status dropdown + CTA `Оновити статус`
- textarea + CTA `Додати нотатку`

## 8. Admin wireframes
### 8.1 Admin Dashboard
- total users
- active users
- inactive users
- pending invites
- units count
- quick actions

### 8.2 Users List
- search
- filters by unit / role / status
- list/table:
  - full_name
  - email
  - unit
  - roles
  - status
  - actions

### 8.3 Create User Screen
- full_name input
- email input
- unit select
- roles multiselect
- CTA `Створити користувача`

### 8.4 User Profile / Edit User
- basic info
- roles
- invite section
- danger zone deactivate/reactivate

### 8.5 Units Screen
- list of units
- create new unit input
- CTA `Додати підрозділ`

### 8.6 Audit Log Screen
- filters
- table/list:
  - created_at
  - event_type
  - actor
  - target
  - entity
  - metadata preview

## 9. Global states for all key screens
Кожен ключовий екран має мати:
- Loading
- Empty
- Error
- Success

## 10. Navigation model P0
### Soldier
Home → baseline / daily / weekly / cognitive → confirmation → back to home

### Commander
Dashboard → cases list → case card → back

### Medic
Cases list → detailed case → add note / update status inline

### Admin
Dashboard → users / units / audit → user profile / create user

## 11. Due-state UI rules
### 11.1 Priority order on Soldier Home
1. незавершений baseline
2. daily due
3. weekly due
4. cognitive due

### 11.2 Label set
- `Потрібно пройти`
- `Доступно`
- `Виконано`
- `Недоступно до завершення baseline`

### 11.3 Commander / Medic urgency
- red = highest
- yellow = medium
- green не виноситься в пріоритетні списки

## 12. P0 wireframe acceptance rules
### Soldier
- весь core flow проходиться без плутанини
- daily на одному екрані
- baseline має чіткий прогрес
- cognitive tests мають focused mode

### Commander
- за 5–10 секунд видно, хто потребує уваги
- немає чутливої деталізації

### Medic
- один екран дає повний робочий контекст кейсу
- note/status actions поруч із кейсом

### Admin
- створення юзера, ролей, invite, deactivate/reactivate прямолінійні
- audit log читається без додаткових пояснень

## 13. Що не входить у Wireframes P0
- visual design system
- branded illustration layer
- dark mode fine tuning
- charts-heavy analytics
- advanced commander reporting
- complex notification center
- localization switcher
- deep responsive micro-variants
