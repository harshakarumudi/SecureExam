# SecureExam — Use Case Model and Detailed Specifications

## Document Information
- **Project**: SecureExam — Secure Online Examination Management System
- **Institution**: Amrita School of Computing
- **Course**: Secure Software Engineering
- **Version**: 1.0.0
- **Status**: Baselined (Phase 3)
- **Target Course Outcomes**: CO1 (Develop secure system models), CO4 (Security testing and governance)

---

## 1. Actors and System Context

The SecureExam system defines three human primary actors and one automated system actor:

| Actor | Category | Description | Trust Level |
| :--- | :--- | :--- | :--- |
| **Student** | Primary Human | Enrolled examinee attempting tests, answering MCQs, and reviewing performance. | Untrusted / Authenticated Client |
| **Faculty** | Primary Human | Course instructor/examiner authoring exams, managing questions, and viewing candidate submissions. | Privileged / Authenticated Client |
| **Administrator** | Primary Human | System governance and audit officer overseeing user accounts, roles, and security audit logs. | Highly Privileged / Authenticated Client |
| **System Engine** | Automated System | Authoritative background evaluator calculating server timestamps and computing scores. | Fully Trusted Internal Service |

---

## 2. Use Case Inventory Matrix

| UC ID | Use Case Title | Primary Actor | Associated Requirement | Security Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **UC-01** | Register Account | Student | FR-STU-01 | Password policy validation, Argon2id hashing |
| **UC-02** | Authenticate (Login) | All Actors | FR-STU-02, SEC-AUTH-03 | Brute force rate limit, generic failure message |
| **UC-03** | Terminate Session (Logout) | All Actors | SEC-SESS-01 | Client token invalidation, audit logging |
| **UC-04** | View & Manage Profile | All Actors | FR-STU-01 | Self-ownership check |
| **UC-05** | Record Audit Event | System Engine | SEC-AUDIT-01 | Append-only audit insertion |
| **UC-06** | Browse Available Exams | Student | FR-STU-03 | Filter published & active exams only |
| **UC-07** | View Exam Instructions | Student | FR-STU-04 | Exam detail display |
| **UC-08** | Start Timed Attempt | Student | FR-STU-05, SEC-TIMER-01 | Authoritative server `expires_at` calculation |
| **UC-09** | Answer & Navigate MCQs | Student | FR-STU-06, FR-STU-07 | Single-answer selection, question palette |
| **UC-10** | Submit Exam Attempt | Student | FR-STU-08, SEC-TIMER-03 | Expiry validation (`now <= expires_at + 15s`) |
| **UC-11** | View Own Result & Score | Student | FR-STU-09, SEC-IDOR-01 | BOLA check (`attempt.student_id == user.id`) |
| **UC-12** | Create Examination | Faculty | FR-FAC-02 | Title, description, duration, passing marks |
| **UC-13** | Edit Owned Exam | Faculty | FR-FAC-03, SEC-IDOR-02 | Ownership check (`exam.created_by == user.id`) |
| **UC-14** | Author & Edit MCQs | Faculty | FR-FAC-04, SEC-XSS-01 | HTML sanitization via `bleach` |
| **UC-15** | Preview Exam Paper | Faculty | FR-FAC-06 | Formatted candidate simulation |
| **UC-16** | Publish / Unpublish Exam | Faculty | FR-FAC-07 | Status transition validation |
| **UC-17** | View Candidate Submissions | Faculty | FR-FAC-08, SEC-IDOR-02 | Candidate grade list for owned exams |
| **UC-18** | Manage User Accounts | Administrator | FR-ADM-02 | Platform-wide user inspection |
| **UC-19** | Assign & Change Roles | Administrator | FR-ADM-04 | Role elevation governance with audit trail |
| **UC-20** | Activate / Deactivate User | Administrator | FR-ADM-03 | Account lock enforcement |
| **UC-21** | Inspect Security Audit Logs | Administrator | FR-ADM-06, SEC-AUDIT-02 | Immutable audit stream viewer |
| **UC-22** | System-wide Exam Oversight | Administrator | FR-ADM-05 | Global exam audit & search |
| **UC-23** | Authoritative Timer Enforcement | System Engine | SEC-TIMER-01, 03 | Automated time calculation & rejection |
| **UC-24** | Server-Side Score Evaluation | System Engine | SEC-SCORE-01, 02 | Tamper-proof automated grading |
| **UC-25** | Object-Level Authorization Check | System Engine | SEC-IDOR-01, 02 | BOLA prevention interceptor |

---

## 3. Detailed Use Case Specifications

### 3.1 UC-02: Authenticate (Login)
- **Primary Actor**: Student, Faculty, Administrator
- **Preconditions**: User has registered an account.
- **Main Success Scenario**:
  1. Actor submits email and plaintext password to `POST /api/v1/auth/login`.
  2. Rate limiter confirms request frequency is under 10 requests/minute.
  3. `AuthService` queries user by normalized email.
  4. Server verifies password hash using Argon2id.
  5. Server checks that `user.is_active` is true.
  6. Server generates a cryptographically signed JWT containing `sub=user_id`, `role=user_role`, and 60-minute expiration.
  7. Server records `LOGIN_SUCCESS` in `audit_logs`.
  8. Server returns HTTP 200 with JWT access token and user role.
- **Alternative & Exception Flows**:
  - *Invalid Credentials*: If email does not exist or password hash verification fails, server logs `LOGIN_FAILED`, sleeps for dummy timing equalization, and returns HTTP 401 (`Invalid email or password`). No user enumeration is revealed.
  - *Rate Limit Exceeded*: If request count exceeds 10 req/min, server returns HTTP 429 (`Too Many Requests`).
  - *Deactivated Account*: If `user.is_active` is false, server returns HTTP 403 (`Account deactivated. Contact administrator.`).

---

### 3.2 UC-08: Start Timed Attempt
- **Primary Actor**: Student
- **Preconditions**: Student is authenticated. Target exam is `PUBLISHED` and within current availability window. Student has not already completed an attempt.
- **Main Success Scenario**:
  1. Student requests `POST /api/v1/exams/{id}/start`.
  2. RBAC verifies actor role is `STUDENT`.
  3. `AttemptService` verifies exam exists, status is `PUBLISHED`, and current UTC time is between `start_date` and `end_date`.
  4. Server queries existing attempts for `(student_id, exam_id)`. Confirms no completed attempts exist.
  5. Server records `started_at = utcnow()` and calculates authoritative `expires_at = started_at + timedelta(minutes=exam.duration_minutes)`.
  6. Server inserts record into `exam_attempts` with status `IN_PROGRESS`.
  7. Server queries exam questions and strips sensitive fields (`correct_option_id`, `explanation`).
  8. Server logs `ATTEMPT_STARTED` into `audit_logs`.
  9. Server returns HTTP 201 with `attempt_id`, `expires_at`, and sanitized question palette.
- **Alternative & Exception Flows**:
  - *Attempt Already Completed*: If student has already submitted this exam, server returns HTTP 400 (`Exam already submitted`).
  - *Exam Not Published / Inactive*: Returns HTTP 404/403 (`Exam is not currently available`).

---

### 3.3 UC-10: Submit Exam Attempt
- **Primary Actor**: Student, System Engine
- **Preconditions**: Student is authenticated. Attempt is in `IN_PROGRESS` state.
- **Main Success Scenario**:
  1. Student submits chosen option IDs to `POST /api/v1/attempts/{id}/submit`.
  2. Server verifies `attempt.student_id == current_user.id` (BOLA protection).
  3. Server captures current UTC time (`server_now`).
  4. System verifies `server_now <= attempt.expires_at + timedelta(seconds=15)` (authoritative timer enforcement).
  5. Server invokes `EvaluationService.evaluate_and_seal(attempt_id, answers)`.
  6. Server retrieves official question answer keys from database.
  7. Server iterates through questions: awarded marks = `question.marks` if chosen option equals `correct_option_id`, else `0` (positive marking only in V1.0).
  8. Server computes `total_score`, `percentage`, and sets `passed = total_score >= exam.passing_marks`.
  9. Server writes sealed record into `results` table and updates `exam_attempts.status = 'COMPLETED'`.
  10. Server logs `ATTEMPT_SUBMITTED` into `audit_logs`.
  11. Server returns HTTP 200 with verified result summary.
- **Alternative & Exception Flows**:
  - *Timer Expired*: If `server_now > attempt.expires_at + 15s`, server marks attempt `EXPIRED`, rejects late answers, grades answers recorded prior to expiry, and returns HTTP 400 (`Exam attempt has expired`).
  - *IDOR Attempt*: If Student A submits with Student B's `attempt_id`, server returns HTTP 403 Forbidden and logs security violation.

---

### 3.4 UC-13: Edit Owned Exam
- **Primary Actor**: Faculty
- **Preconditions**: Faculty is authenticated.
- **Main Success Scenario**:
  1. Faculty sends `PUT /api/v1/exams/{id}` with updated fields.
  2. RBAC verifies role is `FACULTY` (or `ADMIN`).
  3. Server queries `exam = ExamRepository.get(id)`.
  4. Server performs Object-Level Authorization: `exam.created_by == current_user.id`.
  5. If user is owner, server validates input boundaries (Pydantic v2) and sanitizes description.
  6. Server updates exam record and emits `EXAM_UPDATED` to `audit_logs`.
  7. Server returns HTTP 200 with updated exam representation.
- **Alternative & Exception Flows**:
  - *Horizontal Privilege Escalation (IDOR)*: Faculty A attempts to edit Faculty B's exam. Server detects `exam.created_by != current_user.id`, rejects with HTTP 403 Forbidden, and records unauthorized modification attempt in `audit_logs`.

---

### 3.5 UC-19: Assign & Change Roles
- **Primary Actor**: Administrator
- **Preconditions**: Administrator is authenticated with valid JWT carrying `role=ADMIN`.
- **Main Success Scenario**:
  1. Administrator submits `PUT /api/v1/admin/users/{id}/role` with new role (`STUDENT`, `FACULTY`, `ADMIN`).
  2. Server verifies `current_user.role == Role.ADMIN`.
  3. Server loads target user, updates `user.role`, and persists transaction.
  4. Server logs `ROLE_CHANGED` with `admin_id`, `target_user_id`, `old_role`, and `new_role` in `audit_logs`.
  5. Server returns HTTP 200 with updated user record.
- **Alternative & Exception Flows**:
  - *Vertical Privilege Escalation*: Non-admin user (Student or Faculty) submits request. Server dependency immediately aborts with HTTP 403 Forbidden and logs `UNAUTHORIZED_ACCESS_ATTEMPT`.

---

## 4. Actor-to-Use-Case Traceability Matrix

| Use Case | Student | Faculty | Administrator | System Engine |
| :--- | :---: | :---: | :---: | :---: |
| UC-01: Register Account | **X** | - | - | - |
| UC-02: Authenticate (Login) | **X** | **X** | **X** | - |
| UC-03: Terminate Session (Logout) | **X** | **X** | **X** | - |
| UC-04: View & Manage Profile | **X** | **X** | **X** | - |
| UC-05: Record Audit Event | - | - | - | **X** |
| UC-06: Browse Available Exams | **X** | - | - | - |
| UC-07: View Exam Instructions | **X** | - | - | - |
| UC-08: Start Timed Attempt | **X** | - | - | - |
| UC-09: Answer & Navigate MCQs | **X** | - | - | - |
| UC-10: Submit Exam Attempt | **X** | - | - | - |
| UC-11: View Own Result & Score | **X** | - | - | - |
| UC-12: Create Examination | - | **X** | **X** | - |
| UC-13: Edit Owned Exam | - | **X** | **X** | - |
| UC-14: Author & Edit MCQs | - | **X** | **X** | - |
| UC-15: Preview Exam Paper | - | **X** | **X** | - |
| UC-16: Publish / Unpublish Exam | - | **X** | **X** | - |
| UC-17: View Candidate Submissions | - | **X** | **X** | - |
| UC-18: Manage User Accounts | - | - | **X** | - |
| UC-19: Assign & Change Roles | - | - | **X** | - |
| UC-20: Activate / Deactivate User | - | - | **X** | - |
| UC-21: Inspect Security Audit Logs | - | - | **X** | - |
| UC-22: System-wide Exam Oversight | - | - | **X** | - |
| UC-23: Authoritative Timer Enforcement | - | - | - | **X** |
| UC-24: Server-Side Score Evaluation | - | - | - | **X** |
| UC-25: Object-Level Authorization Check | - | - | - | **X** |
