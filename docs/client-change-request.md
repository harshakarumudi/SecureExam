# SecureExam — Formal Client Change Request (CR-2026-004)

## 1. Document Control
- **Change Request ID**: `CR-2026-004`
- **Project**: SecureExam (Secure Online Examination Management System)
- **Requester**: Academic Examination Board & Faculty Committee (Amrita School of Computing)
- **Submission Date**: 2026-09-30
- **Status**: **Approved & Implemented**
- **Impact Level**: Medium (Business Logic, Domain Model, Scoring Strategy)

---

## 2. Business Justification & Problem Statement
In standardized entrance and competitive university examinations (e.g., GATE, JEE, GRE), pure positive-marking schemes are susceptible to statistical guessing exploitation: candidates can achieve statistically significant scores simply by randomly guessing un-penalized multiple-choice questions.

The Examination Board requested an urgent modification to SecureExam Version 1.0:
1. Allow faculty examiners to optionally enable **Negative Marking** per examination.
2. Allow faculty to specify a deduction penalty (`negative_marks`) per question (e.g., 25% or 33% of the question marks).
3. Ensure that leaving a question unanswered incurs **zero penalty** (0 marks).
4. Enforce strict **Underflow Protection**: a candidate's aggregate exam score cannot drop below zero (`total_score = max(0.0, total_score)`).

---

## 3. Requirements Specification & Scoring Rules

### 3.1 Marking Rules Matrix
| Scenario | Standard Mode (Baseline V1.0) | Negative Marking Mode (CR-2026-004) |
| :--- | :---: | :---: |
| **Candidate selects Correct Option** | `+marks` | `+marks` |
| **Candidate selects Incorrect Option** | `0.0` | `-negative_marks` |
| **Candidate leaves Question Unanswered** | `0.0` | `0.0` (Zero penalty) |
| **Total Exam Score Floor** | `max(0.0, score)` | `max(0.0, score)` (Score cannot be negative) |

---

## 4. Threat & Security Impact Analysis

| Threat Dimension | STRIDE Category | Analysis & Potential Risk | Implemented Defensive Control |
| :--- | :--- | :--- | :--- |
| **Candidate Grade Tampering** | **[T] Tampering** | Candidate attempts to modify request payload to claim negative marking was disabled. | Server is the single source of truth. Exam's `enable_negative_marking` flag is retrieved from database; client input cannot toggle scoring mode. |
| **Penalty Evasion via Replay** | **[R] Repudiation** | Candidate disputes score deduction claiming question was skipped. | Each `StudentAnswer` persists the exact `selected_option_id` (or `None`), creating an immutable record of chosen vs. skipped questions. |
| **Arithmetic Underflow / Buffer Issue** | **[T] Tampering** | Negative aggregate score creates arithmetic anomalies or unexpected database constraints. | Floor constraint enforced via `total_score = max(0.0, total_score)` in `EvaluationService`. |

---

## 5. Architectural & Design Refactoring
To prevent code smells and adhere to the **Open-Closed Principle (OCP)**, the procedural evaluation routine was refactored using the **Strategy Pattern (GoF)**:
- `EvaluationStrategy` (Abstract base interface)
- `StandardEvaluationStrategy` (Positive-only scoring)
- `NegativeMarkingStrategy` (Configurable negative penalty scoring)
- `EvaluationStrategyFactory` (Resolves strategy based on `exam.enable_negative_marking`)

---

## 6. Verification & Automated Test Evidence
The change was verified through automated test suites in `tests/test_negative_marking.py`:
- `test_standard_evaluation_strategy_unit`: Verified positive scoring behavior.
- `test_negative_marking_strategy_unit`: Verified negative penalty deductions and zero-penalty skipped questions.
- `test_negative_marking_e2e_lifecycle`: Verified end-to-end exam creation, question configuration, attempt execution, and scoring yielding 3.5 / 15.0 marks.
- `test_negative_marking_underflow_protection`: Verified that double incorrect answers (-8.0 raw) are safely clamped to 0.0 total score.