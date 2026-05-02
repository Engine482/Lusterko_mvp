# Lusterko — PRD v1.0

> Джерело: `Lusterko_PRD_v1_uk.pdf`
> Формат: Markdown-конвертація для роботи Claude Code / Codex / Cursor.
> Примітка: це робоча текстова версія. У разі суперечностей первинним джерелом лишається PDF.

«Люстерко»
PRD MVP web app системи цифрового моніторингу моральнопсихологічного стану особового складу

Версія: PRD v1.0
Формат: фінальна консолідована редакція
Мова: українська

1. Executive Summary / Короткий виклад
1.1. Суть продукту
«Люстерко» — це MVP web app системи цифрового моніторингу морально-психологічного
стану особового складу, призначеної для регулярного виявлення ранніх ознак
функціонального, емоційного, стресового та когнітивного просідання військовослужбовців.
Система поєднує короткі стандартизовані self-report оцінки, прості цифрові когнітивні проби,
rule-based логіку оцінки ризику та вузько обмежений AI-модуль для структурованої
інтерпретації короткого текстового коментаря користувача.

1.2. Проблема, яку вирішує система
У підрозділах морально-психологічний стан часто оцінюється фрагментарно, нерегулярно і
переважно суб’єктивно. Через це негативна динаміка виявляється запізно, а командир, медик
або психолог отримують не ранній сигнал, а вже наслідок.

1.3. Запропоноване рішення
MVP пропонує контрольований цифровий контур оцінки стану, який включає baseline-скринінг,
щоденний короткий check-in, щотижневу переоцінку емоційного і стресового навантаження,
періодичні когнітивні проби, rule-based Risk Engine та окремі інтерфейси для солдата,
командира, медика / психолога й адміністратора.

1.4. Ціль MVP
Створити робочий, демонстрабельний і придатний до контрольованого пілоту продукт, який
доводить життєздатність логіки короткого цифрового моніторингу стану.

1.5. Практична цінність
Система дозволяє раніше виявляти негативну динаміку, зменшувати залежність від
випадкового виявлення проблеми, давати командиру інструмент пріоритизації уваги, а медику
/ психологу — структурований потік кейсів.

1.6. Формат пілоту
Рекомендований формат пілоту: один підрозділ, приблизно 30–100 користувачів,
контрольований доступ, окремі рольові інтерфейси та збір кількісних і якісних результатів.

1.7. Висновок
«Люстерко» у форматі MVP — це реалістичний web app продукт, головна цінність якого
полягає у створенні робочого цифрового інструменту раннього сигналу та підтримки
управлінської уваги.

2. Problem Statement / Постановка проблеми
2.1. Поточний стан
У практиці підрозділів морально-психологічний стан залишається критично важливим, але
недостатньо формалізованим параметром. Найчастіше він оцінюється як побічний висновок із
поведінки, працездатності або вже явних ознак проблеми.

2.2. Основні системні проблеми







Відсутність регулярного короткого моніторингу.
Надмірна залежність від суб’єктивного спостереження.
Запізніле виявлення негативної динаміки.
Відсутність персональної динаміки відносно власної baseline-норми.
Перевантаження фахівців несортованим потоком випадків.
Відсутність пояснюваного механізму сигналізації ризику.

2.3. Наслідки для підрозділу
Це призводить до погіршення якості управлінського реагування, недооцінки функціонального і
когнітивного просідання, неефективного розподілу уваги фахівців і відсутності накопичуваної
аналітики по людині та підрозділу.

2.4. Формулювання продуктової проблеми
У підрозділі відсутній короткий, регулярний, пояснюваний і масштабований цифровий
механізм раннього виявлення негативної динаміки морально-психологічного, функціонального
та когнітивного стану військовослужбовця.

2.5. Висновок
Продукт покликаний закрити не “всю тему МПС”, а конкретну нестачу: відсутність простого
цифрового інструменту раннього сигналу і пріоритизації уваги.

3. Product Vision / Бачення продукту
3.1. Загальне бачення
«Люстерко» мислиться як система цифрового супроводу стану особового складу, яка
переводить морально-психологічний стан у структурований, регулярно оновлюваний і
practically usable контур спостереження.

3.2. Бачення MVP
MVP має бути не “максимально розумною системою”, а робочим, коротким і пояснюваним
інструментом, придатним до використання в пілотному середовищі.





Короткий сценарій для користувача.
Регулярна динаміка замість разової оцінки.
Пояснюваний ризиковий сигнал.
Раціональне і вузьке використання AI.

3.3. Принципова позиція
Система допомагає раніше побачити ризикову динаміку і краще організувати увагу, але не
підміняє людину, командира, медика чи психолога.

3.4. Чим продукт не повинен стати





Цифровою психіатрією з претензією на діагностику.
Терапевтичним чат-ботом.
Неконтрольованим AI-агентом.
Важкою бюрократичною формою або системою “про все”.

3.5. Висновок
Бачення продукту полягає у створенні короткого, регулярного, пояснюваного і керованого
цифрового інструменту спостереження за станом особового складу.

4. Goals / Цілі продукту
4.1. Загальна мета
Створити цифровий інструмент, який дозволяє регулярно фіксувати стан військовослужбовця,
виявляти негативну динаміку раніше, ніж вона стане очевидною, і підтримувати своєчасне
управлінське та фахове реагування.

4.2. Цілі MVP







Створити робочий web app MVP.
Реалізувати короткий і регулярний сценарій моніторингу.
Побудувати baseline і персоналізовану динаміку.
Реалізувати пояснюваний rule-based Risk Engine.
Інтегрувати обмежений AI-модуль.
Забезпечити багаторольову модель доступу.

4.3. Цілі пілоту





Перевірити реальну придатність щоденного сценарію.
Перевірити корисність ризикових сигналів.
Перевірити придатність role-based workflow.
Перевірити стабільність технічної реалізації.

4.4. Нецілі MVP






Клінічна діагностика.
Психотерапевтичний супровід.
Автономні кадрові рішення.
Складні інтеграції з відомчими системами.
Повноцінна predictive ML-система.

5. Product Scope / Межі MVP
5.1. Що входить у MVP











Web app із mobile-friendly інтерфейсом.
Invite-based доступ, email+password, multi-role access, role selection і role switching.
Soldier-side assessment flow: baseline, daily, weekly, cognitive.
Assessment Framework із self-report, cognitive і text layers.
AI text interpretation module.
Rule-based Risk Engine.
Commander interface.
Medic / psychologist interface.
Admin interface.
Централізована БД, REST API, базовий аудит і RBAC.

5.2. Що не входить у MVP









Клінічна діагностика.
Психотерапевтична або чат-орієнтована взаємодія.
Голосовий аналіз.
Wearables та фізіологічні сенсори.
Predictive ML на великих даних.
Глибокі інтеграції з відомчими системами.
Автономні кадрові або медичні рішення.
Розширена аналітика і звітність.

5.3. Що відкладається на V2+
Після пілоту можуть бути додані розширення AI-модуля, покращення Risk Engine, гнучкіша
конфігурація правил, розширена аналітика, додаткові identity providers та інтеграції.

5.4. P0 склад MVP
До P0 входять auth model, multi-role access, soldier flows, AI text parsing, Risk Engine basic,
commander dashboard, medic detailed case view, admin provisioning і базовий аудит.

6. Target Users & Roles / Цільові користувачі та ролі
6.1. Основні ролі





Військовослужбовець — проходить оцінки і формує первинний цифровий слід даних.
Командир — бачить агреговану картину і пріоритизує увагу.
Медик / психолог — працює з ризиковими й критичними кейсами.
Адміністратор системи — створює користувачів, керує ролями і доступом.

6.2. Multi-role user model
Один користувач може мати одну або кілька ролей одночасно. Це спрощує демо, тестування і
робить архітектуру гнучкішою.

6.3. Active role concept
У кожній сесії користувач працює лише в одній active role. Саме вона визначає доступні
маршрути, API, дані та інтерфейс.

6.4. Role switching
Якщо в користувача кілька ролей, він може обрати роль після входу і змінювати її всередині
системи без повторної авторизації.

6.5. Role isolation
Ролі відрізняються не лише інтерфейсом, а й рівнем деталізації доступних даних: soldier
бачить власний сценарій, commander — управлінську зведену картину, medic —
деталізований кейс, admin — адміністративний контур.

7. User Value by Role / Цінність системи по ролях
7.1. Для військовослужбовця
Короткий, простий і не перевантажений спосіб регулярної фіксації стану без складної
психологічної мови і без псевдодіагностики.

7.2. Для командира
Швидкий управлінський огляд стану підрозділу, ранній сигнал ризикових випадків, менша
залежність від інтуїтивної оцінки.

7.3. Для медика / психолога
Пріоритизований потік кейсів, динаміка стану, пояснюваність системного сигналу і економія
уваги за рахунок зменшення шуму.

7.4. Для адміністратора
Керований доступ, багаторольова модель, контроль ролей, інвайтів і простежуваність
адміністративних дій.

7.5. Спільна цінність
Продукт з’єднує кілька різних контурів в один процес: soldier дає сигнал, система його
структурує, commander бачить пріоритет, medic отримує кейс, admin підтримує доступ і
керованість.

8. Assessment Framework / Framework оцінки стану
8.1. Загальний принцип
Framework побудований не навколо спроби “визначити людину взагалі”, а навколо виявлення
негативної динаміки функціонального, емоційного, стресового та когнітивного стану відносно
baseline і поточного тренду.

8.2. Основні типи сигналів




Self-report сигнали: daily functional check-in, PHQ-4, PSS-4, sleep block.
Цифрові когнітивні сигнали: reaction time test, go / no-go test.
AI-інтерпретований текстовий сигнал: короткий необов’язковий коментар.

8.3. Baseline
На старті система формує baseline-профіль на основі PHQ-4, PSS-4, sleep block, reaction time
test і go / no-go test.

8.4. Daily layer
Щоденний check-in включає 4 шкали: сон, енергія, загальний стан / настрій, концентрація.
Кожна шкала оцінюється за 0–10. Додатково можна залишити короткий текстовий коментар.

8.5. Weekly layer
Раз на тиждень проходяться PHQ-4 і PSS-4 для відстеження накопичення емоційного і
стресового навантаження.

8.6. Cognitive layer
Двічі на тиждень проходяться reaction time test і go / no-go test як поведінковий шар цифрових
когнітивних сигналів.

8.7. Частота застосування





На старті: PHQ-4, PSS-4, sleep block, reaction time test, go / no-go test.
Щодня: functional check-in, optional comment.
1 раз на тиждень: PHQ-4, PSS-4.
2 рази на тиждень: reaction time test, go / no-go test.

8.8. Обмеження framework
Framework не є клінічною діагностичною системою, не визначає професійну придатність
автоматично і не замінює фаховий перегляд.

9. AI Text Interpretation Module / AI-модуль інтерпретації тексту
9.1. Роль у MVP
AI використовується лише для аналізу короткого необов’язкового текстового коментаря під
час daily check-in. Це допоміжний аналітичний шар, а не ядро продукту.

9.2. Чому AI використовується саме тут





Текст містить сигнали, яких немає у шкалах.
Задача вузька і контрольована.
Вартість реалізації відносно невисока.
Таке використання легко пояснювати і дебажити.

9.3. Підтримувані мови
Модуль повинен підтримувати українську, російську і mixed input, із поверненням поля
language_detected: uk / ru / mixed / unknown.

9.4. Основні задачі модуля





Language detection.
Marker extraction.
Text risk classification: none / low / medium / high.
Summary generation for system use.

9.5. Категорії маркерів









sleep_issue
fatigue
low_mood
anxiety_tension
concentration_problem
irritability
post_stress_reaction
acute_distress

9.6. Формат виходу
AI-модуль повинен повертати тільки structured JSON із language_detected, has_signal, markers,
text_risk_level, confidence_score, summary_for_system і parse_status.

9.7. Guardrails





Без діагнозів.
Без терапевтичних або медичних порад.
Без діалогового режиму.
Без автономного остаточного рішення.

9.8. Fallback
Якщо AI не повернув валідний результат, система все одно повинна зберегти daily check-in,
зафіксувати parse_status і не зламати основний сценарій.

10. Risk Engine / Логіка оцінки ризику
10.1. Загальний принцип
Risk Engine — це пояснюваний rule-based модуль, який інтегрує кілька джерел сигналів у
єдиний risk status. Він не є black box моделлю і повинен бути відтворюваним, керованим і
аудитованим.

10.2. Завдання




Інтегрувати сигнали з framework оцінки.
Оцінювати відхилення від baseline.
Виявляти негативну динаміку.





Присвоювати green / yellow / red статус.
Формувати explanation text.
Піднімати пріоритет у разі hard flags.

10.3. Домени ризику





Functional risk.
Emotional / stress risk.
Cognitive risk.
Text risk modifier.

10.4. Рівні ризику




Green — недостатньо ознак значущого ризику.
Yellow — є сигнали, що потребують уваги.
Red — сильна сукупність сигналів або hard flag.

10.5. Таблиця правил
У MVP використовується набір правил по доменах functional, emotional/stress, cognitive і text
modifier. Окремо існують hard flags для acute distress, повторного високого text risk, severe
functional cluster і severe cognitive drop.

10.6. Логіка агрегації
Підсумковий ризиковий бал формується як сума доменних внесків із застосуванням порогів і
обмежень по максимальному внеску кожного домену. Hard flags мають пріоритет над
звичайною сумою.

10.7. Пояснюваність
Кожен yellow або red кейс має містити коротке людське пояснення причини спрацювання.

10.8. Історичність
Risk Engine повинен оновлювати поточний risk status і зберігати risk events та rule hits history
для аудиту і післяпілотної оцінки.

10.9. Обмеження
Risk Engine не є діагностичною системою, не замінює людину і потребує подальшого
калібрування після пілоту.

11. User Flows / Сценарії використання
11.1. Ключові сценарії








Вхід у систему через інвайт + встановлення паролю; повторний вхід — email+password.
Вибір ролі після входу.
Зміна ролі всередині системи.
Первинне підключення і baseline onboarding.
Щоденний check-in.
Щотижнева переоцінка.
Періодичні когнітивні проби.





Перегляд dashboard командиром.
Перегляд і ведення кейсу медиком / психологом.
Створення користувача, призначення ролей і деактивація доступу адміністратором.

11.2. Загальний принцип сценаріїв
Усі сценарії будуються навколо короткого шляху до основної дії, рольової однозначності,
мінімуму тертя і пояснюваних переходів між кроками.

11.3. Висновок
User flows показують, що MVP — це не набір тестів, а повноцінний багаторольовий продукт із
логікою: доступ → роль → оцінка → risk scoring → dashboard → case review →
адміністрування.

12. UX & Screen Model / Модель інтерфейсів і екранів
12.1. Загальні UX-принципи







Один екран — одна головна дія.
Мінімум когнітивного навантаження.
Role-driven UI.
Mobile-friendly soldier experience.
Швидкий доступ до суті.
Пояснюваність без перевантаження.

12.2. Shared screens





Invite Landing Screen.
OAuth Callback Screen.
Role Selection Screen.
Global Role Switcher.

12.3. Soldier screens
Soldier-side контур включає Soldier Home, Baseline Flow, Daily Check-in, Daily Confirmation,
Weekly Reassessment Screens і Cognitive Screens.

12.4. Commander screens
Commander-side контур включає Commander Dashboard і Commander Case Card.

12.5. Medic / psychologist screens
Medic-side контур включає Priority Cases List, Detailed Case View і Notes / Case Workflow
Elements.

12.6. Admin screens
Admin-side контур включає Admin Dashboard, Users List, Create User, User Profile, Units Screen і
Audit Log Screen.

12.7. Route guard model
Shared auth routes є публічними; рольовий доступ до soldier, commander, medic і admin screens
визначається active role і перевіряється на сервері.

12.8. Global states
Кожен ключовий екран має мати loading, empty, error і success state.

12.9. Висновок
UX & Screen Model побудована на простоті, рольовій однозначності та швидкому доступі до
суті.

13. System Architecture / Архітектура системи MVP
13.1. Загальний архітектурний принцип
MVP будується як web app із централізованою серверною логікою, де frontend відповідає за
UX, backend — за business logic, контроль доступу, AI integration і Risk Engine, а реляційна БД
— за збереження стану системи.

13.2. Основні архітектурні компоненти









Client Layer.
Backend Application Layer.
Data Layer.
Assessment Processing Layer.
Risk Engine Layer.
AI Text Module.
Auth & Access Layer.
Administration Layer.

13.3. Формат продукту
На рівні MVP продукт реалізується як standalone web app з mobile-friendly soldier experience.

13.4. Потоки даних






Auth flow: invite → set password → session → active role → role-specific interface; повторний вхід — email+password з тим же session-cookie контуром.
Soldier assessment flow: input → save → normalization → AI if text → Risk Engine → updated
status.
Commander flow: dashboard request → scope validation → aggregated data.
Medic flow: case list → detailed case → notes / status update.
Admin flow: action → validation → write to DB → audit.

13.5. Рекомендований технічний стек






Frontend: React / Next.js.
Backend: Python (FastAPI) або Node.js.
Database: PostgreSQL.
AI integration: LLM API через thin wrapper / service layer.
Auth: first-party email+password (argon2id). Див. ADR `docs/06_decisions/2026-05-02-auth-email-password.md`.



Deployment: server-side deployment з HTTPS.

13.6. Архітектурні обмеження
Не входять у MVP мікросервісна складність, offline-first синхронізація, важкі інтеграції, voice
analytics, wearables та predictive ML platform.

14. Authorization & Access Model / Модель авторизації та доступу
14.1. Загальний принцип
У межах MVP використовується керована invite-based модель доступу: адміністратор створює
користувача, задає email і ролі, генерує інвайт, користувач переходить за посиланням з
інвайт-листа, встановлює пароль, після чого система відкриває сесію.

14.2. Invite-based access flow
Інвайт пов’язується з конкретним користувачем та email, має строк дії (7 днів) і не повинен
працювати повторно. Прийняття інвайта — це момент, коли встановлюється початковий пароль.

14.3. Email + password authentication
> **Sprint 7 Auth Pivot:** з 2026-05-02 first-party email+password замінив Google OAuth як
> primary auth. Повний rationale: `docs/06_decisions/2026-05-02-auth-email-password.md`.
> Google OAuth і user_identities-таблицю прибрано без backward-сумісних слідів.

Параметри: argon2id-хеш паролю (мінімум 12 символів), скидання паролю через токенізоване
посилання в email (TTL 1 год), session-cookie 30д rolling, rate-limit 5/15хв на пару (IP, email)
з soft-lockout 5хв і експоненційним backoff. Без 2FA на P0. SSO/SAML відкладено до V1.

14.4. Identity model
Користувач і його credentials — це різні сутності в моделі (`users.password_hash` як
nullable атрибут). Це дозволяє за потреби пізніше додати paralel-провайдер (OIDC/SAML)
без переписування user-модеі — passwords залишаться як один із способів входу або стануть
nullable.

14.5. Multi-role access model
Один користувач може мати кілька ролей одночасно. Для однозначності доступу
використовується active role concept.

14.6. Active role session model
Active role визначає доступні маршрути, API, дані і рольовий home screen. Доступ
перевіряється по зв’язці authenticated user + active session + active role + scope.

14.7. Role selection and switching
Якщо ролей більше однієї, після входу показується екран вибору ролі. Далі роль можна
змінювати всередині системи без повторного логіну.

14.8. Scope model
Commander і medic / psychologist працюють лише в межах своїх unit scopes. Soldier бачить
тільки власні дані. Admin працює в адміністративному контурі.

14.9. Обмеження моделі доступу
У MVP немає відкритої самореєстрації, довільного створення ролей користувачем і складного
enterprise SSO-контуру.

15. Data Model / Модель даних
15.1. Загальні принципи






Реляційність.
Історичність.
Відокремлення ролей і способів входу.
Мінімізація дублювання.
Придатність до пілоту.

15.2. Основні групи сутностей






Організаційні сутності: units, users, user_roles, user_identities, auth_invites, user_sessions.
Оціночні сутності: baseline_profiles, baseline_events, daily_checkins,
weekly_phq4_assessments, weekly_pss4_assessments, reaction_tests, go_no_go_tests.
AI- та risk-related сутності: comment_ai_analyses, risk_statuses, risk_events, risk_rule_hits.
Case management сутності: case_reviews, case_review_notes.
Audit сутності: audit_logs.

15.3. Ключові організаційні сутності
Units підтримують unit scope. Users — базовий профіль. User identities — способи входу. User
roles — багаторольову модель. Auth invites — контрольований первинний доступ. User
sessions — active role і життєвий цикл сесії.

15.4. Ключові оціночні сутності
Baseline profiles задають персональну стартову норму. Daily check-ins є центральним
джерелом динаміки. Weekly assessments і cognitive tests формують повільніший і поведінковий
шари сигналу.

15.5. Risk і case management сутності
Comment AI analyses зберігають structured result AI. Risk statuses — поточний стан. Risk events
і risk rule hits — історію та пояснюваність. Case reviews і notes — робочий контур медика /
психолога.

15.6. Audit
Audit logs зберігають auth, admin, security-relevant і case-related події.

15.7. P0 сутності
До P0 належать units, users, user_identities, user_roles, auth_invites, user_sessions,
baseline_profiles, baseline_events, daily_checkins, weekly_phq4_assessments,
weekly_pss4_assessments, reaction_tests, go_no_go_tests, comment_ai_analyses, risk_statuses,
risk_events, case_reviews і audit_logs.

16. API Specification / API-специфікація
16.1. Загальні принципи
У межах MVP використовується REST API з JSON, версіоноване як /api/v1/…, з UUID і
стандартизованими timestamps.

16.2. Рольовий принцип API
API побудоване навколо ролей і active role. Основні контури: Auth API, Admin API, Soldier API,
Commander API, Medic / Psychologist API, Internal AI API.

16.3. Auth API







POST /api/v1/auth/login
POST /api/v1/auth/invite/accept
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
GET /api/v1/auth/me
POST /api/v1/auth/select-role
POST /api/v1/auth/refresh
POST /api/v1/auth/logout

16.4. Admin API












POST /api/v1/admin/users
GET /api/v1/admin/users
GET /api/v1/admin/users/{user_id}
PATCH /api/v1/admin/users/{user_id}
PUT /api/v1/admin/users/{user_id}/roles
POST /api/v1/admin/users/{user_id}/invite
POST /api/v1/admin/users/{user_id}/deactivate
POST /api/v1/admin/users/{user_id}/reactivate
GET /api/v1/admin/units
POST /api/v1/admin/units
GET /api/v1/admin/audit-logs

16.5. Soldier API















GET /api/v1/soldier/onboarding-status
POST /api/v1/soldier/baseline/phq4
POST /api/v1/soldier/baseline/pss4
POST /api/v1/soldier/baseline/sleep
POST /api/v1/soldier/baseline/reaction-test
POST /api/v1/soldier/baseline/go-no-go
POST /api/v1/soldier/baseline/complete
POST /api/v1/soldier/daily-checkins
GET /api/v1/soldier/daily-checkins/today
POST /api/v1/soldier/weekly/phq4
POST /api/v1/soldier/weekly/pss4
POST /api/v1/soldier/cognitive/reaction-test
POST /api/v1/soldier/cognitive/go-no-go
GET /api/v1/soldier/completion-summary

16.6. Commander API




GET /api/v1/commander/dashboard/summary
GET /api/v1/commander/dashboard/cases
GET /api/v1/commander/cases/{user_id}

16.7. Medic API





GET /api/v1/medic/cases
GET /api/v1/medic/cases/{case_review_id}
PATCH /api/v1/medic/cases/{case_review_id}
POST /api/v1/medic/cases/{case_review_id}/notes

16.8. Internal AI API
POST /internal/ai/analyze-comment — внутрішній endpoint для backend-to-backend виклику AIмодуля.

16.9. P0 endpoints
До ядра P0 входять усі auth endpoints, базовий admin provisioning, baseline / daily / weekly /
cognitive soldier endpoints, commander dashboard, medic detailed case і internal AI analyzecomment.

17. Functional Requirements / Функціональні вимоги
17.1. Auth & access









Керований доступ лише для створених адміністратором користувачів.
Invite-based login (інвайт → встановлення паролю).
Email + password authentication (argon2id, 12+ chars, rate-limited).
Multi-role model.
Role selection after login.
In-app role switching.
Logout and session termination.
Server-side role enforcement.

17.2. Soldier-side










Soldier home із due-state задач.
Baseline onboarding із 5 кроків.
Збереження часткового прогресу baseline.
Щоденний check-in з 4 шкалами і optional comment.
Не більше одного daily check-in на день.
Weekly reassessment.
Cognitive assessments.
Completion summary.
Відсутність діагностичного output для soldier.

17.3. Commander-side


Commander dashboard.






Cases list with filters.
Commander case card.
Scope limitation for commander.
Без надлишкової клінічної деталізації.

17.4. Medic / psychologist-side






Priority cases list.
Detailed case view.
Case status update.
Case notes.
Scope limitation for medic / psychologist.

17.5. Admin-side







User creation.
Role assignment.
Invite generation.
User deactivation / reactivation.
Units management.
Audit log access.

17.6. Framework, AI, Risk Engine, Cases
Система повинна формувати baseline profile, зберігати всі оцінки, нормалізувати сигнали,
виконувати structured text analysis, рахувати Risk Engine, підтримувати case lifecycle і аудит.

17.7. Критерій функціональної готовності
MVP функціонально готовий, якщо працюють доступ, role switching, soldier flows, AI text
parsing, Risk Engine, commander dashboard, medic case workflow, admin control і базовий audit
trail.

18. Non-Functional & Security Requirements / Нефункціональні вимоги
і безпека
18.1. Ключові напрями













Security model.
Session security.
Transport security.
RBAC.
Privacy & data minimization.
Auditability.
AI guardrails.
Reliability & availability.
Data integrity.
Data retention.
Hosting & deployment assumptions.
Performance expectations.



Error handling policy.

18.2. Security model
Система повинна працювати як закритий керований контур із invite validation, argon2id
password verification, brute-force lockout і blocking inactive users.

18.3. Session security
Сесія повинна підтримувати active role, refresh flow, logout і інвалідацію при деактивації
користувача.

18.4. RBAC
Усі перевірки доступу виконуються на сервері по зв’язці authenticated user + active session +
active role + scope.

18.5. Privacy & data minimization
Система збирає лише дані, необхідні для доступу, framework оцінки, Risk Engine, case review і
аудиту. Різні ролі бачать різну глибину інформації.

18.6. AI guardrails
AI використовується лише для structured text analysis, не ставить діагнози, не дає порад, не
веде діалог і не є single point of failure.

18.7. Reliability
Ключові сценарії повинні працювати стабільно. Якщо AI-модуль недоступний, daily check-in
все одно зберігається.

18.8. Security-critical P0 requirements
До нефункціонального P0 належать HTTPS, invite validation, argon2id password storage,
brute-force lockout, active-role-based RBAC, deactivated-user blocking, logout with session
invalidation, базовий аудит, AI guardrails і duplicate protection.

19. Dev Backlog Specification / Backlog розробки
19.1. Основні епіки













Epic A — Auth & Access
Epic B — Admin Module
Epic C — Soldier Module
Epic D — Commander Module
Epic E — Medic / Psychologist Module
Epic F — Assessment Processing Layer
Epic G — AI Text Module
Epic H — Risk Engine
Epic I — Case Review System
Epic J — Due Logic & Notifications
Epic K — Audit & Security
Epic L — UI Infrastructure

19.2. P0 release slice
До P0 входять invite-based email+password login (з password reset), multi-role model, role
selection і switching, admin provisioning, soldier baseline / daily / weekly / cognitive flows,
AI text parsing, Risk Engine basic, commander dashboard, medic detailed case, server-side RBAC,
brute-force lockout і базовий audit trail.

19.3. P1 release slice
До P1 належать polished explanations, risk history, case workflow, notes, auto-open case logic,
audit UI, units management polish і покращена фільтрація commander dashboard.

19.4. P2 release slice
До P2 належать in-app reminders, local fallback auth UI, розширена аналітика, гнучкіша
конфігурація thresholds, richer reporting і додаткові identity providers.

19.5. Suggested build order






Sprint 1: auth & access, multi-role model, admin basic, app shell.
Sprint 2: soldier baseline, daily check-in, weekly reassessment.
Sprint 3: cognitive tests, AI text module, assessment normalization.
Sprint 4: Risk Engine, commander dashboard, commander case card.
Sprint 5: medic interface, case workflow, audit / stabilization.

19.6. Definition of MVP complete
MVP вважається завершеним, якщо працюють ключові role-based сценарії, AI text parsing, Risk
Engine, admin control і базовий audit trail.

20. Implementation Roadmap / Дорожня карта реалізації
20.1. Етап 0 — Концептуальний пакет
Формування one-pager, документа для МО, MVP-концепції, framework оцінки, концепції AI та
Risk Engine і каркаса PRD.

20.2. Етап 1 — Технічне проєктування
Завершення архітектури MVP, auth & access model, data model, API specification, screen model,
rule set, backlog і non-functional requirements.

20.3. Етап 2 — Розробка MVP
Реалізація P0 release slice як першої робочої версії web app.

20.4. Етап 3 — Внутрішнє тестування
Перевірка core flows, AI behavior, Risk Engine, role-based access, dashboard і admin actions.

20.5. Етап 4 — Demo Version
Підготовка стабільного demo environment, тестових акаунтів, демо-кейсів і сценарію показу.

20.6. Етап 5 — Пілотне впровадження
Запуск у контрольованому контурі одного підрозділу приблизно на 30–100 користувачів.

20.7. Етап 6 — Оцінка результатів пілоту
Збір adoption, operational, product і qualitative metrics та підготовка after-action report.

20.8. Етап 7 — Післяпілотне доопрацювання і V2
Калібрування Risk Engine, покращення UX, admin tooling, analytics і формування V2 roadmap.

20.9. Поточна позиція проєкту
Проєкт перебуває на межі між завершеним концептуальним пакетом і технічним
проєктуванням; це вже не ідея, але ще не етап коду.

21. Success Metrics & Pilot Evaluation / Метрики успіху та оцінка
пілоту
21.1. Чотири групи метрик





Adoption metrics — чи користуються системою.
Operational metrics — чи дає система practically useful signals.
Product metrics — чи продукт технічно стабільний.
Qualitative metrics — чи різні ролі бачать реальну цінність.

21.2. Adoption metrics






Onboarding completion rate.
Daily check-in completion rate.
Weekly reassessment completion rate.
Cognitive completion rate.
Active users by role.

21.3. Operational metrics








Number of yellow cases detected.
Number of red cases detected.
Case review rate.
Median time to review.
Confirmed useful signal rate.
False positive burden.
Escalation usefulness.

21.4. Product metrics







System availability.
Error rate in core flows.
AI parsing success rate.
AI safety compliance rate.
Risk explanation consistency.
Median completion time for main flows.

21.5. Qualitative metrics


Feedback from soldiers.





Feedback from commanders.
Feedback from medics / psychologists.
Feedback from administrator.

21.6. Мінімальні критерії успіху








Onboarding completion ≥ 70%.
Daily check-in completion ≥ 60%.
Weekly reassessment completion ≥ 65%.
Cognitive completion ≥ 60%.
Наявність practically useful risk signals.
Відсутність критичних технічних провалів.
Позитивне або принаймні змістовне role-based user feedback.

21.7. Формат after-action report
Після пілоту має бути підготовлений короткий after-action report із кількісними результатами,
якісними висновками, рішенням про подальший розвиток і списком рекомендацій.

22. Risks / Основні ризики
22.1. Продуктові ризики





Надмірне ускладнення MVP.
Перетворення продукту на “чергову анкету”.
Низький adoption.
Неправильна інтерпретація ролі системи.

22.2. Технічні ризики





Незавершена технічна рамка перед стартом розробки.
Нестабільність ключових сценаріїв.
Слабка role-based ізоляція.
AI-модуль як точка відмови.

22.3. Організаційні ризики




Відсутність відповідального за пілот.
Формальне використання без реальної цінності.
Слабкий адміністративний контур.

22.4. AI-related risks




Завищені очікування від AI.
Неконтрольований output.
Мовна нестабільність на uk / ru / mixed input.

22.5. Ризики пілоту і розвитку





Неправильний масштаб пілоту.
Слабкий demo-to-pilot перехід.
Шумовий або, навпаки, “сліпий” Risk Engine.
Передчасне масштабування.



Втрата продуктового фокусу після пілоту.

22.6. Пріоритетні ризики для MVP
Найкритичніші ризики: надмірне ускладнення, низький adoption, шумовий Risk Engine,
нестабільність core flows, слабка role-based ізоляція, неправильне сприйняття ролі AI і
слабкий організаційний контур пілоту.

23. Assumptions / Ключові припущення
23.1. Припущення щодо користувачів і доступу





Користувачі мають доступ до браузера і пристрою.
Можна використовувати email для invite flow.
Користувачі здатні пройти короткий onboarding.
Користувачі здатні регулярно проходити короткий daily flow.

23.2. Припущення щодо рольової моделі





Поділ на soldier / commander / medic_psych / admin є природним і прийнятним.
Multi-role model є корисною, а не шкідливою.
Active role model достатня для рольової ізоляції.
Commander і medic інтерфейси реально використовуватимуться.

23.3. Припущення щодо продуктового сценарію





Короткість сценарію є ключем до adoption.
Регулярність цінніша за глибину одного тесту.
Комбінація кількох слабших сигналів цінніша за один великий тест.
Пояснюваність важливіша за складність.

23.4. Припущення щодо framework, AI і Risk Engine







Обраний набір методик є мінімально достатнім.
Baseline має практичний сенс.
Cognitive layer додає реальну цінність.
Optional text comment справді вартий AI-обробки.
Rule-based Risk Engine достатній для MVP.
AI можна утримати в жорстких межах і він не повинен бути критичною точкою відмови.

23.5. Припущення щодо пілоту і технічної реалізації






Пілот має проводитися в обмеженому контрольованому контурі.
Для пілоту буде визначено відповідального.
Web app є достатнім форматом для MVP.
Обраний стек достатній для швидкої реалізації.
Позитивний пілот виправдає розвиток V2.

24. Constraints / Обмеження MVP
24.1. Загальний принцип
MVP будується як обмежена, але життєздатна система. Не все, що може бути корисним,
входить у першу версію; не все, що теоретично можливе, доцільно реалізовувати одразу.

24.2. Продуктові обмеження






MVP не є клінічною системою.
MVP не є терапевтичним сервісом.
MVP не є системою автоматичного рішення.
MVP не є всеосяжною платформою про МПС.
MVP свідомо обмежений у глибині методик.

24.3. Архітектурні обмеження





Web-first формат.
Централізована архітектура замість складної мікросервісної моделі.
Обмежений контур інтеграцій.
Відсутність складного real-time orchestration.

24.4. AI-обмеження





AI не є центром продукту.
AI не працює у вільному режимі.
AI не має прямого user-facing діалогу.
AI не повинен бути критичною залежністю всього продукту.

24.5. UX та організаційні обмеження






Щоденний сценарій повинен бути дуже коротким.
Weekly і cognitive сценарії теж мають бути короткими.
Пілот має бути обмеженим.
Потрібен адміністративний контур.
Потрібна рольова дисципліна.

24.6. Найважливіші обмеження MVP
Web app only, standalone deployment, invite-based access only, email+password (argon2id) як
primary auth path, multi-role але одна active role за раз, short daily flow only, limited
assessment set, AI only for
structured text analysis, rule-based Risk Engine only, no diagnosis / no therapy / no autonomous
decisions, limited pilot scope, strict MVP scope discipline.

25. Conclusion / Висновок
25.1. Що таке «Люстерко» на рівні MVP
«Люстерко» — це технічно й продуктово визначений MVP web app, який поєднує
контрольований доступ, baseline, регулярні оцінки, вузько обмежений AI-модуль, пояснюваний
rule-based Risk Engine, role-based інтерфейси та базовий контур безпеки й аудиту.

25.2. Яку проблему продукт реально вирішує
Продукт дає підрозділу короткий, регулярний, пояснюваний і керований цифровий механізм
раннього виявлення ризикової динаміки стану особового складу.

25.3. Чому рішення виглядає реалістичним






Воно вузько сфокусоване.
Не перевантажене функціями.
Використовує AI там, де це справді доречно.
Має прозору логіку ризику.
Мислиться як пілотний продукт, а не “все готове одразу”.

25.4. Чому продукт придатний до пілоту
MVP already has all core contours needed for real controlled use: доступ, baseline, регулярні
сценарії, AI text analysis, Risk Engine, commander dashboard, medic case review, admin control і
аудит.

25.5. Що буде доведено, якщо MVP спрацює
Якщо пілот буде успішним, це доведе життєздатність короткого цифрового сценарію,
практичний сенс role-based контурів, корисність rule-based Risk Engine і вузько обмеженого AIмодуля.

25.6. Що робити далі
Після цього PRD логічно зібрати фінальну документну версію, підготувати executive version
для замовника, перейти до sprint planning і почати розробку P0 MVP.

25.7. Фінальний висновок
Головна цінність «Люстерко» не в цифровізації заради цифровізації і не в AI заради AI, а в
створенні реального інструменту раннього сигналу і пріоритизації уваги до стану особового
складу.
