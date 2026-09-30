# SecureExam — Architectural Module Dependency & Coupling Analysis

## 1. Overview & Metrics Framework
Architectural maintainability and testability depend directly on modular design, high cohesion, and loose coupling. In this analysis, we evaluate the architectural packages of SecureExam using Robert C. Martin's Package Coupling Metrics:
- **Afferent Coupling ($C_a$)**: Number of external modules that depend on classes within this module (incoming dependencies). Indicates module responsibility.
- **Efferent Coupling ($C_e$)**: Number of external modules that this module depends upon (outgoing dependencies). Indicates module fragility.
- **Instability ($I$)**:
  $$I = \frac{C_e}{C_a + C_e} \quad (0 \le I \le 1)$$
  - $I = 0$: Maximally stable / independent module (difficult to change, safe to depend upon).
  - $I = 1$: Maximally instable module (easily impacted by changes in dependencies).

---

## 2. Module Coupling & Cohesion Analysis Table

| Module / Subsystem | Primary Responsibility | Afferent ($C_a$) | Efferent ($C_e$) | Instability ($I$) | Architectural Classification |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`core.security`** | Password hashing, JWT token crypto, password validation | 6 | 1 | **0.14** | Highly Stable Core Foundation |
| **`core.database`** | Engine setup, session lifecycle, declarative base | 7 | 1 | **0.12** | Highly Stable Core Foundation |
| **`core.sanitizer`** | Bleach HTML whitelist sanitization | 2 | 0 | **0.00** | Pure Independent Utility |
| **`services.audit_service`** | Immutable security audit persistence | 5 | 2 | **0.29** | Stable Cross-Cutting Service |
| **`services.auth_service`** | Registration, login authentication, session generation | 2 | 4 | **0.67** | Dynamic Service Layer |
| **`services.exam_service`** | Exam lifecycle, question authoring, publication | 2 | 5 | **0.71** | Dynamic Domain Service |
| **`services.attempt_service`**| Active exam session, authoritative timer initialization | 2 | 5 | **0.71** | Dynamic Domain Service |
| **`services.evaluation_service`** | Server-side scoring, penalty calculation, result sealing | 2 | 5 | **0.71** | Candidate for Decoupling Refactor |
| **`services.result_service`** | Result querying, BOLA ownership validation | 1 | 3 | **0.75** | Query Service |

---

## 3. Structural Dependency Graph
The module dependency relationships are visualized in `diagrams/module-dependency.mmd`.

### 3.1 Key Observations & Baseline for Refactoring
1. **Core Foundation Stability**: `core.security` and `core.database` possess very low instability ($I \le 0.14$), confirming that foundational components do not fluctuate when high-level business rules change.
2. **Coupling in `EvaluationService`**: In Version 1.0, `EvaluationService` had direct efferent coupling to `Exam`, `Question`, `QuestionOption`, `ExamAttempt`, and `Result`. Furthermore, positive marking was hardcoded directly inside a monolithic evaluation loop.
3. **Decoupling Opportunity**: In Milestone 7, `EvaluationService` is refactored using the **Strategy Pattern** (`EvaluationStrategy`). This decouples scoring policies (positive marking vs. negative marking) into dedicated, independently testable strategy implementations, reducing method complexity and coupling.