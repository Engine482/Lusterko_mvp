# Lusterko — Master Index v1

Це master index для pre-build пакета MVP «Люстерко».

Його задача — дати:
- правильну структуру пакета;
- рекомендовану послідовність читання;
- коротке пояснення ролі кожного документа;
- швидкий маршрут переходу від документів до реальної розробки.

---

## 1. Склад пакета

### 1.1 Pre-build документи
1. `Lusterko_Risk_Engine_Spec_v1.md`
2. `Lusterko_API_Contracts_v1.md`
3. `Lusterko_DB_Schema_v1.md`
4. `Lusterko_RBAC_Matrix_v1.md`
5. `Lusterko_Test_Scenarios_P0_v1.md`
6. `Lusterko_Wireframes_P0_v1.md`

### 1.2 Planning documents
7. `Lusterko_Sprint_Plan_P0_v1.md`
8. `Lusterko_Development_Backlog_v1.md`

---

## 2. Рекомендована структура папок

Нижче — правильна логічна структура пакета. Навіть якщо зараз файли лежать в одній папці, саме так їх краще тримати надалі в repo або docs-пакеті.

```text
lusterko_docs/
├── 00_index/
│   └── Lusterko_Master_Index_v1.md
│
├── 01_pre_build/
│   ├── Lusterko_Risk_Engine_Spec_v1.md
│   ├── Lusterko_API_Contracts_v1.md
│   ├── Lusterko_DB_Schema_v1.md
│   ├── Lusterko_RBAC_Matrix_v1.md
│   ├── Lusterko_Test_Scenarios_P0_v1.md
│   └── Lusterko_Wireframes_P0_v1.md
│
├── 02_planning/
│   └── Lusterko_Sprint_Plan_P0_v1.md
│
└── 03_execution/
    └── Lusterko_Development_Backlog_v1.md
```

---

## 3. Правильна послідовність читання

Не треба читати це навмання. Пакет має нормальну логіку.

### Етап 1 — зрозуміти, як система думає
1. **Risk Engine Spec**  
   Це ядро логіки продукту. Пояснює, як із сигналів утворюється risk status.

2. **API Contracts**  
   Показує, як фронтенд і бекенд мають говорити між собою.

3. **DB Schema**  
   Фіксує, як усе це реально лягає в дані.

### Етап 2 — зрозуміти, хто що може бачити й робити
4. **RBAC Matrix**  
   Закриває доступи, role isolation, unit scope і field filtering.

### Етап 3 — зрозуміти, як перевіряти, що MVP справді працює
5. **Test Scenarios P0**  
   Дає критерії готовності та blocking bugs.

### Етап 4 — зрозуміти, як продукт має виглядати на рівні екранів
6. **Wireframes P0**  
   Замикає фронтенд, UX і screen-level logic.

### Етап 5 — зрозуміти, як це будувати
7. **Sprint Plan P0**  
   Дає макрорівень збірки MVP по спринтах.

8. **Development Backlog**  
   Дає задачі, з якими вже можна заходити в таск-трекер.

---

## 4. Коротка роль кожного документа

### 4.1 `Lusterko_Risk_Engine_Spec_v1.md`
Потрібен для:
- backend logic;
- risk scoring;
- hard flags;
- explanation generation;
- test design для risk layer.

### 4.2 `Lusterko_API_Contracts_v1.md`
Потрібен для:
- FastAPI routes;
- Pydantic schemas;
- frontend API client;
- стабільної інтеграції фронта і бека.

### 4.3 `Lusterko_DB_Schema_v1.md`
Потрібен для:
- Alembic migrations;
- ORM models;
- seed data;
- persistence layer.

### 4.4 `Lusterko_RBAC_Matrix_v1.md`
Потрібен для:
- backend guards;
- field-level response filtering;
- active role enforcement;
- scope isolation.

### 4.5 `Lusterko_Test_Scenarios_P0_v1.md`
Потрібен для:
- acceptance criteria;
- regression checks;
- release blocking decisions;
- demo readiness.

### 4.6 `Lusterko_Wireframes_P0_v1.md`
Потрібен для:
- screen implementation;
- role-based navigation;
- due-state UX;
- фронтенд-розробки без імпровізації.

### 4.7 `Lusterko_Sprint_Plan_P0_v1.md`
Потрібен для:
- визначення етапів збірки;
- planning cadence;
- sprint sequencing;
- release gates.

### 4.8 `Lusterko_Development_Backlog_v1.md`
Потрібен для:
- task tracker;
- sprint execution;
- assignable dev tasks;
- повсякденної роботи по MVP.

---

## 5. Мінімальний маршрут для різних ролей

### 5.1 Якщо ти продукт/архітектор
Читай так:
1. Risk Engine Spec
2. RBAC Matrix
3. Wireframes P0
4. Sprint Plan
5. Development Backlog

### 5.2 Якщо ти backend developer
Читай так:
1. API Contracts
2. DB Schema
3. Risk Engine Spec
4. RBAC Matrix
5. Test Scenarios P0
6. Development Backlog

### 5.3 Якщо ти frontend developer
Читай так:
1. Wireframes P0
2. API Contracts
3. RBAC Matrix
4. Test Scenarios P0
5. Development Backlog

### 5.4 Якщо ти QA / test owner
Читай так:
1. Test Scenarios P0
2. API Contracts
3. RBAC Matrix
4. Risk Engine Spec
5. Wireframes P0

---

## 6. Що вважати точкою старту розробки

Після цього пакета можна без самообману починати:
- repo bootstrap;
- migrations;
- backend skeleton;
- frontend skeleton;
- seed data;
- sprint execution.

Тобто далі вже не бракує базової передпроєктної рамки.

---

## 7. Що робити далі

Правильний наступний порядок:
1. завести ці документи в repo в `docs/`;
2. перенести backlog у task tracker;
3. відкрити Sprint 0;
4. підняти repo + DB + CI;
5. почати Sprint 1 execution.

---

## 8. Швидкий перелік файлів у поточному пакеті

- `Lusterko_Master_Index_v1.md`
- `Lusterko_Risk_Engine_Spec_v1.md`
- `Lusterko_API_Contracts_v1.md`
- `Lusterko_DB_Schema_v1.md`
- `Lusterko_RBAC_Matrix_v1.md`
- `Lusterko_Test_Scenarios_P0_v1.md`
- `Lusterko_Wireframes_P0_v1.md`
- `Lusterko_Sprint_Plan_P0_v1.md`
- `Lusterko_Development_Backlog_v1.md`

---

## 9. Фінальний висновок

Цей пакет уже можна вважати **робочим pre-build + execution pack** для MVP «Люстерко».

Він закриває:
- логіку продукту;
- API-контракти;
- модель даних;
- доступи;
- тестування;
- екрани;
- планування;
- backlog execution.
