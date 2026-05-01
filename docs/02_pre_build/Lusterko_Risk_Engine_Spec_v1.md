# Lusterko — Risk Engine Spec v1

## 1. Призначення
Risk Engine — це rule-based модуль, який:
- приймає сигнали з self-report, weekly scales, cognitive tests і AI-аналізу тексту;
- оцінює відхилення від baseline та негативну динаміку;
- формує `green / yellow / red`;
- повертає коротке людське пояснення;
- зберігає історію rule hits та risk events.

Це не діагностика, не психіатричний висновок і не автономне рішення щодо користувача. Це лише пріоритизація уваги.

## 2. Вхідні сигнали
### 2.1 Daily functional layer
Щоденні шкали 0–10:
- `sleep_score`
- `energy_score`
- `mood_score`
- `concentration_score`

Інтерпретація:
- 0–3 = виражене просідання
- 4–5 = помірне просідання
- 6–7 = умовна норма
- 8–10 = добра / висока функціональність

### 2.2 Weekly emotional/stress layer
- `phq4_total` = 0–12
- `pss4_total` = 0–16

### 2.3 Cognitive layer
- `reaction_time_median_ms`
- `reaction_time_valid_trials`
- `go_no_go_commission_errors`
- `go_no_go_omission_errors`
- `go_no_go_valid_trials`

### 2.4 Text layer
AI-модуль повертає:
- `language_detected`
- `has_signal`
- `markers[]`
- `text_risk_level`
- `confidence_score`
- `summary_for_system`
- `parse_status`

Підтримувані маркери:
- `sleep_issue`
- `fatigue`
- `low_mood`
- `anxiety_tension`
- `concentration_problem`
- `irritability`
- `post_stress_reaction`
- `acute_distress`

## 3. Baseline model
### 3.1 Що входить у baseline
Baseline формується після завершення:
- PHQ-4
- PSS-4
- sleep block
- reaction time test
- go/no-go test

### 3.2 Baseline values
Для кожного користувача зберігаються:
- `baseline_sleep_score`
- `baseline_energy_score`
- `baseline_mood_score`
- `baseline_concentration_score`
- `baseline_phq4_total`
- `baseline_pss4_total`
- `baseline_reaction_time_median_ms`
- `baseline_go_no_go_commission_errors`
- `baseline_go_no_go_omission_errors`

### 3.3 Якщо baseline неповний
Поки baseline не завершений:
- red не присвоюється за cumulative logic;
- можна показувати лише `insufficient_data` або тимчасовий green/yellow-lite;
- hard flags все одно мають право спрацьовувати.

## 4. Домени ризику
- Functional risk
- Emotional / stress risk
- Cognitive risk
- Text risk modifier

## 5. Система балів
### 5.1 Загальний принцип
Кожен домен дає бали ризику. Підсумок:
- `0–2` → Green
- `3–5` → Yellow
- `>=6` → Red

Hard flags мають пріоритет.

### 5.2 Обмеження внеску домену
- Functional: 3
- Emotional/stress: 2
- Cognitive: 2
- Text modifier: 2

## 6. Functional rules
### 6.1 Оцінка по кожній daily-шкалі
Для кожної з 4 шкал:
- **F1 severe drop vs baseline**: якщо поточне значення `<= baseline - 3` → `+1`
- **F2 moderate drop vs baseline**: якщо поточне значення `= baseline - 2` → `+0.5`
- **F3 absolute low state**: якщо поточне значення `<= 3` → `+1`

### 6.2 Cluster logic
- **F4 functional cluster**: якщо 2 або більше шкал мають `absolute low state` або `severe drop` → додатково `+1`

### 6.3 Severe functional cluster hard flag
- **HF1 severe_functional_cluster**: якщо 3 або 4 шкали одночасно `<= 3` або `<= baseline - 3` → `RED_HARD_FLAG`

### 6.4 Domain cap
Максимум Functional domain = 3.

## 7. Emotional/stress rules
### 7.1 Weekly PHQ-4
- **E1**: `phq4_total >= 6` → `+1`
- **E2**: `phq4_total >= 9` → `+2` замість +1
- **E3 delta from baseline**: `phq4_total >= baseline + 3` → додатково `+0.5`

### 7.2 Weekly PSS-4
- **E4**: `pss4_total >= 8` → `+1`
- **E5**: `pss4_total >= 11` → `+2` замість +1
- **E6 delta from baseline**: `pss4_total >= baseline + 4` → додатково `+0.5`

### 7.3 Combined weekly strain
- **E7 combined emotional/stress strain**: якщо одночасно elevated PHQ-4 і elevated PSS-4 → додатково `+0.5`

### 7.4 Domain cap
Максимум Emotional/stress = 2.

## 8. Cognitive rules
### 8.1 Reaction time
- **C1 moderate slowdown**: `reaction_time_median_ms >= baseline * 1.15` → `+1`
- **C2 severe slowdown**: `reaction_time_median_ms >= baseline * 1.30` → `+2` замість +1

### 8.2 Go / No-Go
- **C3 commission error increase**: помилки комісії зросли на `>= 50%` від baseline або на `>= 3 абсолютні помилки` → `+1`
- **C4 omission error increase**: помилки пропуску зросли на `>= 50%` від baseline або на `>= 3 абсолютні помилки` → `+1`

### 8.3 Severe cognitive drop
- **HF2 severe_cognitive_drop**: `reaction_time >= baseline * 1.40` і commission або omission errors суттєво зросли → `RED_HARD_FLAG`

### 8.4 Domain cap
Максимум Cognitive = 2.

## 9. Text rules
### 9.1 Base text modifier
За умови `parse_status = success` і `confidence_score >= 0.60`
- none → `+0`
- low → `+0.5`
- medium → `+1`
- high → `+2`

### 9.2 Marker reinforcement
Додатково `+0.5`, якщо в тексті одночасно є 2+ маркери з набору:
- `sleep_issue`
- `fatigue`
- `low_mood`
- `anxiety_tension`
- `concentration_problem`

### 9.3 Acute distress hard flag
- **HF3 acute_distress**: якщо присутній маркер `acute_distress` з confidence `>= 0.75` → `RED_HARD_FLAG`

### 9.4 Repeated high text risk
- **HF4 repeated_high_text_risk**: якщо `text_risk_level = high` двічі поспіль у двох останніх daily check-in → `RED_HARD_FLAG`

### 9.5 Parse failure policy
Якщо AI не спрацював:
- daily check-in все одно зберігається;
- text modifier = 0;
- логуються `parse_status`, `error_code`;
- Risk Engine продовжує працювати без текстового шару.

## 10. Final aggregation
### 10.1 Формула
`total_risk_score = functional_score + emotional_score + cognitive_score + text_modifier_score`

### 10.2 Thresholds
- `0–2` → Green
- `3–5` → Yellow
- `>=6` → Red

### 10.3 Hard flag priority
Якщо є хоча б один:
- `HF1 severe_functional_cluster`
- `HF2 severe_cognitive_drop`
- `HF3 acute_distress`
- `HF4 repeated_high_text_risk`

тоді фінальний статус = `Red`, незалежно від total score.

## 11. Explanation text
Для кожного yellow/red кейсу система має зберігати коротке пояснення.

### 11.1 Шаблони
**Functional**
- “Зафіксовано виражене просідання сну та енергії відносно базового профілю.”
- “Виявлено сукупне функціональне просідання за кількома щоденними шкалами.”

**Emotional/stress**
- “Щотижневі шкали вказують на підвищене емоційне та стресове навантаження.”
- “Виявлено зростання показників PHQ-4 / PSS-4 відносно baseline.”

**Cognitive**
- “Зафіксовано погіршення когнітивних показників порівняно з базовим рівнем.”
- “Виявлено сповільнення реакції та зростання кількості помилок.”

**Text**
- “Текстовий коментар містить ознаки виснаження / тривоги / дистресу.”
- “Повторно виявлено високоризиковий текстовий сигнал.”

### 11.2 Правило пояснення
Пояснення має:
- бути коротким;
- описувати причину сигналу;
- не містити діагнозів;
- не містити рекомендацій лікування.

## 12. Data outputs Risk Engine
### 12.1 `risk_statuses`
- `user_id`
- `current_risk_status`
- `current_risk_score`
- `functional_score`
- `emotional_score`
- `cognitive_score`
- `text_modifier_score`
- `hard_flag`
- `explanation_text`
- `calculated_at`

### 12.2 `risk_events`
- `event_id`
- `user_id`
- `source_event_type`
- `source_event_id`
- `previous_status`
- `new_status`
- `total_score`
- `hard_flag`
- `explanation_text`
- `created_at`

### 12.3 `risk_rule_hits`
- `event_id`
- `rule_code`
- `domain`
- `weight`
- `details_json`

## 13. Case opening logic
### 13.1 Auto-open
Автоматично створюється case review, якщо:
- статус став `Red`, або
- статус `Yellow` тримається 3 оцінки поспіль

### 13.2 Не створювати дублікати
Якщо вже є відкритий case review, новий не створюється. Натомість:
- додається новий risk event;
- existing case піднімається в пріоритеті.

## 14. Мінімальний набір тестів для Risk Engine
- Green case
- Yellow by functional cluster
- Yellow by weekly strain
- Red by cumulative score
- Red by acute distress
- Red by repeated high text risk
- Parse failure resilience
- Incomplete baseline behavior

## 15. Що ще треба зафіксувати в наступній редакції
- точні baseline sleep rules;
- мінімальну валідну кількість cognitive trials;
- time-window для “двічі поспіль”;
- чи yellow streak рахується по днях чи по подіях;
- чи командир бачить повний explanation, чи скорочений.
