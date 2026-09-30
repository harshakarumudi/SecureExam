# SecureExam — Software Requirements Specification (SRS)

## Document Information
- **Project**: SecureExam — Secure Online Examination Management System
- **Institution**: Amrita School of Computing
- **Course**: Secure Software Engineering
- **Version**: 1.0.0
- **Status**: Baselined (Phase 1)
- **Course Outcomes Covered**: CO1, CO2, CO3, CO4

---

## 1. Problem Statement
Traditional academic and corporate online examination systems frequently suffer from critical security vulnerabilities that compromise academic integrity and data privacy:
1. **Client-Side Vulnerabilities**: Timers manipulated in browser local storage or DOM, allowing candidates to extend examination duration indefinitely.
2. **Insecure Authorization**: Broken Object-Level Authorization (BOLA/IDOR), allowing students to inspect exam answer keys or other students' grades by simply altering resource identifiers in HTTP requests.
3. **Tamperable Score Evaluation**: Unauthenticated or client-calculated score submission endpoints susceptible to direct payload interception and manipulation.
4. **Injection and Input Attacks**: Vulnerabilities to SQL Injection (SQLi) in search and filter parameters, and Cross-Site Scripting (XSS) in exam questions and explanations.
5. **Lack of Accountability**: Inadequate or absent audit trails failing to log administrative modifications, privilege escalations, and unauthenticated examination submissions.
6. **Supply Chain Vulnerabilities**: Outdated dependencies with known Common Vulnerabilities and Exposures (CVEs) and unhardened container deployment configurations.

**SecureExam** addresses these systemic challenges through a security-by-design architecture, enforcing rigorous server-authoritative controls, zero-trust backend authorization, cryptographic confidentiality, tamper-evident audit logging, and automated DevSecOps verification.

---

## 2. Project Objectives
1. **Confidentiality**: Protect examination content, answer keys, candidate credentials, and grade reports from unauthorized disclosure.
2. **Integrity**: Guarantee authoritative server-side evaluation and ensure no client payload can tamper with scores, question weights, or examination timers.
3. **Availability & Resilience**: Prevent denial-of-service and brute-force attacks on authentication and exam submission workflows through algorithmic rate limiting.
4. **Accountability & Non-Repudiation**: Maintain an immutable, tamper-evident audit log of all security-relevant transactions across students, faculty, and administrators.
5. **Pedagogical Alignment**: Map directly to Amrita School of Computing Course Outcomes CO1 (Secure System Models), CO2 (Threat Modeling), CO3 (Security Economics & Containerization), and CO4 (Security Testing, Governance & Compliance).

---

## 3. Project Scope

### In-Scope
- Role-based portals for **Student**, **Faculty**, and **Administrator**.
- Student workflow: Registration, authenticated session management, viewing available published exams, authoritative timed exam attempts, Single-Answer MCQ navigation, submission, and instant verified grade report.
- Faculty workflow: Exam authoring, lifecycle management (draft, publish, unpublish), question bank authoring with option weights and explanations, candidate submission review.
- Administrator workflow: User account lifecycle management (activation, deactivation, role assignment), system-wide exam oversight, immutable security audit log viewer.
- Security-by-Design controls: Argon2id password hashing, JWT with strict expiry, server-side RBAC, strict object ownership validation, parameterized queries, XSS sanitization, rate limiting, and security response headers.
- Containerization: Multi-stage non-root Dockerfiles and Docker Compose orchestration with network segmentation.
- DevSecOps: Automated CI/CD pipeline incorporating linting, automated unit/integration/security testing, and dependency scanning (`pip-audit`).

### Out-of-Scope (V1.0)
- Multi-factor hardware security key (FIDO2/WebAuthn) authentication (planned for V2.0).
- Biometric facial recognition and video-based proctoring.
- Third-party LMS LTI integrations (e.g., Canvas, Moodle).

---

## 4. Stakeholders
- **University Examination Office / Academic Administration**: Requires audit compliance, grade integrity, and system availability.
- **Course Instructors / Faculty**: Requires intuitive exam creation, question management, and dependable automated grading.
- **Students / Examinees**: Requires a fair, reliable, accessible examination taking interface with unambiguous timing and prompt feedback.
- **System Administrators / Security Auditors**: Requires full visibility into system events, access logs, account governance, and zero unmitigated vulnerabilities.

---

## 5. Actors & Permissions Overview
| Actor | Description | High-Level Permissions |
| :--- | :--- | :--- |
| **Student** | Enrolled candidate taking exams | View published exams, attempt permitted exams, submit answers, view own results. |
| **Faculty** | Course instructor / Examiner | Create, update, publish, and delete owned exams; create and manage questions; view student submissions for owned exams. |
| **Administrator** | System auditor and governance officer | Manage all users, change user roles, activate/deactivate accounts, oversee all exams, view immutable audit logs. |

---

## 6. Functional Requirements (FR)

### 6.1 Student Functional Requirements
- **FR-STU-01**: The system shall allow a student to register with a unique email, full name, and strong password.
- **FR-STU-02**: The system shall allow a student to authenticate and receive a secure JWT access token.
- **FR-STU-03**: The system shall allow a student to view only active, published examinations.
- **FR-STU-04**: The system shall display exam instructions, duration, total marks, and passing criteria before the student begins an attempt.
- **FR-STU-05**: The system shall allow a student to initiate an examination attempt, recording an authoritative server-side start time.
- **FR-STU-06**: The system shall present questions one by one or in a navigable list with Single-Choice options.
- **FR-STU-07**: The system shall allow students to select, change, and clear options before submission.
- **FR-STU-08**: The system shall allow manual submission of the examination before timer expiration.
- **FR-STU-09**: The system shall allow a student to view their own result (score, percentage, completion timestamp) upon submission or when grades are published.
- **FR-STU-10**: The system shall prevent a student from accessing answer explanations until the examination window is closed or permitted by faculty.
- **FR-STU-11**: The system shall restrict a student to one attempt per exam unless explicit retakes are authorized by faculty.

### 6.2 Faculty Functional Requirements
- **FR-FAC-01**: The system shall allow authenticated faculty to access the Faculty Studio dashboard.
- **FR-FAC-02**: The system shall allow faculty to create a new examination (Title, Description, Duration in minutes, Total Marks, Start/End availability window).
- **FR-FAC-03**: The system shall allow faculty to edit or delete examinations they created (owned resources).
- **FR-FAC-04**: The system shall allow faculty to create Multiple Choice Questions (MCQs) for an exam, including question prompt, 4 options, indicator of correct option, mark weight, and optional pedagogical explanation.
- **FR-FAC-05**: The system shall allow faculty to edit or remove questions prior to exam commencement.
- **FR-FAC-06**: The system shall allow faculty to preview the formatted examination paper as it will appear to candidates.
- **FR-FAC-07**: The system shall allow faculty to transition exam status between `DRAFT`, `PUBLISHED`, and `CLOSED`.
- **FR-FAC-08**: The system shall allow faculty to view candidate attempt lists, submission timestamps, and calculated scores for exams they own.

### 6.3 Administrator Functional Requirements
- **FR-ADM-01**: The system shall provide an administrative command dashboard.
- **FR-ADM-02**: The system shall allow administrators to view all registered users with their active status and assigned role.
- **FR-ADM-03**: The system shall allow administrators to activate or deactivate user accounts.
- **FR-ADM-04**: The system shall allow administrators to assign or modify user roles (`STUDENT`, `FACULTY`, `ADMIN`).
- **FR-ADM-05**: The system shall allow administrators to inspect and search all system examinations.
- **FR-ADM-06**: The system shall provide a filtered viewer for security audit logs, including event timestamp, actor ID, IP address, event type, and outcome.

---

## 7. Non-Functional Requirements (NFR)

### 7.1 Performance Requirements (NFR-PERF)
- **NFR-PERF-01**: The API shall respond to 95% of standard read requests in under 200 milliseconds under a nominal load of 100 concurrent users.
- **NFR-PERF-02**: Examination submission and server-side score evaluation shall complete in under 500 milliseconds.
- **NFR-PERF-03**: Client frontend bundle size shall not exceed 500 KB gzipped to ensure rapid load times over restricted mobile/campus networks.

### 7.2 Availability & Resilience (NFR-AVAIL)
- **NFR-AVAIL-01**: The system shall achieve 99.5% uptime during active academic examination windows.
- **NFR-AVAIL-02**: In the event of a brief client network disconnection during an active exam, the client interface shall automatically cache selected answers locally and synchronize upon reconnection without resetting the server-side timer.

### 7.3 Usability & Accessibility (NFR-USE)
- **NFR-USE-01**: The user interface shall adhere to WCAG 2.1 Level AA accessibility standards, supporting full keyboard navigation and high-contrast color schemes.
- **NFR-USE-02**: The interface shall be fully responsive across mobile (>= 360px), tablet, and desktop viewports.
- **NFR-USE-03**: The exam taking interface shall provide high-visibility status indicators: remaining time, question palette (answered, unanswered, marked for review), and submission confirmation modals.

### 7.4 Maintainability & Code Quality (NFR-MAINT)
- **NFR-MAINT-01**: Backend codebase shall adhere to PEP 8 standards enforced via Ruff and Black with 0 blocking linter errors.
- **NFR-MAINT-02**: Automated test coverage across business logic, authentication, and security endpoints shall exceed 85%.
- **NFR-MAINT-03**: The system architecture shall enforce modular separation between Presentation (React), API Controllers (FastAPI), Service Logic, and Persistence (SQLAlchemy ORM).

### 7.5 Privacy Requirements (NFR-PRIV)
- **NFR-PRIV-01**: User personal information (email, name) and exam grades shall be accessible only to the owner and authorized academic personnel.
- **NFR-PRIV-02**: Passwords shall never be stored, logged, or returned in API responses under any circumstances.

### 7.6 Deployment Requirements (NFR-DEP)
- **NFR-DEP-01**: The entire application stack (Frontend, Backend, Database) shall be containerized via Docker and orchestratable with a single `docker compose up` command.
- **NFR-DEP-02**: Containers shall run with non-root privileges (`appuser`, UID 10001).

---

## 8. Explicit Security Requirements (SEC)

The following security requirements will be directly traced through Threat Modeling (STRIDE), Architecture, Implementation, and Security Testing.

### 8.1 Authentication Security
- **SEC-AUTH-01 (Password Hashing)**: All passwords shall be hashed using Argon2id (or bcrypt with work factor >= 12). Plaintext passwords shall never touch persistence media.
- **SEC-AUTH-02 (Password Policy)**: The system shall enforce a minimum password length of 10 characters containing at least one uppercase letter, one lowercase letter, one digit, and one special character.
- **SEC-AUTH-03 (Account Enumeration Prevention)**: Login endpoints shall return generic error responses (`Invalid email or password`) regardless of whether the account exists or the password was incorrect.
- **SEC-AUTH-04 (Brute Force Protection)**: Authentication endpoints shall enforce rate limiting of no more than 5 failed attempts per minute per IP address.

### 8.2 Authorization & Access Control (RBAC)
- **SEC-RBAC-01 (Server-Side Role Enforcement)**: Every API endpoint requiring elevated privileges shall enforce role checks on the server side using cryptographically validated JWT claims. Client-side role claims shall never be trusted.
- **SEC-RBAC-02 (Vertical Privilege Escalation Prevention)**: Students attempting to invoke faculty endpoints (e.g., `POST /api/v1/exams`) or admin endpoints (e.g., `GET /api/v1/admin/users`) shall be immediately rejected with HTTP 403 Forbidden and an audit event logged.

### 8.3 Insecure Direct Object Reference (IDOR / BOLA) Prevention
- **SEC-IDOR-01 (Horizontal Privilege Escalation Prevention)**: When a student requests exam attempt results (`GET /api/v1/attempts/{id}`), the server shall explicitly verify that `attempt.student_id == current_user.id`. Requests for another candidate''s attempt shall return HTTP 403/404.
- **SEC-IDOR-02 (Faculty Resource Ownership)**: When a faculty member updates or deletes an exam (`PUT /api/v1/exams/{id}`), the server shall verify that `exam.created_by == current_user.id` (or user is Admin). Unauthorized modification shall be rejected.

### 8.4 Input Validation & Sanitization
- **SEC-VAL-01 (Strict Schema Validation)**: All incoming payloads shall be strictly validated using Pydantic v2 schemas. Extraneous fields shall be stripped or rejected (`extra = "forbid"`).
- **SEC-VAL-02 (Type & Boundary Checks)**: Duration must be an integer between 1 and 360 minutes. Marks must be positive integers or decimals >= 0.

### 8.5 SQL Injection (SQLi) Prevention
- **SEC-SQLI-01 (ORM Parameterization)**: All database queries shall be executed through SQLAlchemy 2.0 ORM or parameterized prepared statements. Raw dynamic string concatenation of user input into SQL statements is strictly prohibited.

### 8.6 Cross-Site Scripting (XSS) Prevention
- **SEC-XSS-01 (Input Sanitization)**: Rich text or markdown fields in exam questions, choices, and explanations shall be sanitized on the backend using `bleach` to remove unsafe HTML tags (`<script>`, `<iframe>`, `onload`, etc.).
- **SEC-XSS-02 (Context-Aware Output Encoding)**: The React frontend shall render dynamic text using native JSX bindings which automatically escape HTML entities. Direct injection via `dangerouslySetInnerHTML` is prohibited unless explicitly sanitized.

### 8.7 Cross-Site Request Forgery (CSRF) Protection
- **SEC-CSRF-01**: API authentication shall use bearer tokens transmitted via the `Authorization: Bearer <token>` header, immune to cross-origin ambient cookie transmission attacks. Where cookies are utilized, `SameSite=Strict`, `HttpOnly`, and `Secure` flags shall be mandated.

### 8.8 Rate Limiting & DoS Mitigation
- **SEC-RATE-01 (Global & Endpoint Rate Limiting)**: The API shall enforce rate limits via SlowAPI: 100 requests/minute for general authenticated endpoints, and 10 requests/minute for sensitive authentication endpoints. Exceeding thresholds shall return HTTP 429 Too Many Requests.

### 8.9 Security Headers
- **SEC-HDR-01**: Every HTTP response shall include security headers:
  - `Content-Security-Policy: default-src ''self''; frame-ancestors ''none'';`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (when in HTTPS mode)

### 8.10 Cross-Origin Resource Sharing (CORS)
- **SEC-CORS-01**: CORS middleware shall strictly specify trusted origin domains (e.g., `http://localhost:5173`). Wildcard `*` origins are strictly forbidden when authentication credentials are exchangeable.

### 8.11 Authoritative Server-Side Exam Timer
- **SEC-TIMER-01**: When an exam attempt starts, the server shall calculate `expires_at = started_at + exam.duration_minutes`.
- **SEC-TIMER-02**: The frontend timer shall be treated purely as a visual aid.
- **SEC-TIMER-03**: Upon receiving an answer submission or exam finalization payload, the backend shall check `server_now <= expires_at + grace_period` (15 seconds network allowance). Submissions received after expiration shall be rejected with HTTP 400 (`Exam attempt has expired`) and automatically marked submitted with answers recorded up to the expiration moment.

### 8.12 Server-Side Score Evaluation & Result Security
- **SEC-SCORE-01**: The client shall never transmit scores, marks, or indicators of correctness.
- **SEC-SCORE-02**: The server `EvaluationService` shall query the database for correct option IDs, compare candidate choices, calculate total marks obtained, compute percentage, and seal the result record.
- **SEC-SCORE-03**: Result records shall be marked read-only upon submission; no endpoint shall permit students or unauthorized faculty to mutate a generated score.

### 8.13 Audit Logging & Accountability
- **SEC-AUDIT-01**: The system shall log security-relevant events into an append-only `AuditLogs` table:
  - `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`
  - `EXAM_CREATED`, `EXAM_UPDATED`, `EXAM_DELETED`, `EXAM_PUBLISHED`, `EXAM_UNPUBLISHED`
  - `ATTEMPT_STARTED`, `ATTEMPT_SUBMITTED`, `ATTEMPT_EXPIRED`
  - `UNAUTHORIZED_ACCESS_ATTEMPT`, `ROLE_CHANGED`, `USER_STATUS_CHANGED`
- **SEC-AUDIT-02**: Audit log records shall contain timestamp (UTC), user ID, actor role, IP address, action code, resource ID, and outcome status.
- **SEC-AUDIT-03**: Audit logs shall never record sensitive credentials, passwords, session tokens, or private keys.

### 8.14 Secure Session & Token Handling
- **SEC-SESS-01**: JWT access tokens shall have a maximum lifespan of 60 minutes.
- **SEC-SESS-02**: JWT signing shall use HMAC-SHA256 with a minimum 256-bit cryptographically secure pseudorandom secret key. The `none` algorithm shall be explicitly rejected.

### 8.15 Dependency Security
- **SEC-DEP-01**: All third-party Python dependencies shall be pinned to exact versions in `requirements.txt`.
- **SEC-DEP-02**: CI/CD pipelines shall execute `pip-audit` and `npm audit` to fail the build if any dependency contains a known High or Critical CVSS vulnerability.

### 8.16 Container & Deployment Security
- **SEC-CONT-01**: Container images shall be based on minimal base images (Alpine / Debian Slim).
- **SEC-CONT-02**: Containers shall run under an unprivileged user (`appuser`, UID 10001).
- **SEC-CONT-03**: The database service shall reside on an internal Docker network, inaccessible from public ingress.

---

## 9. Constraints & Assumptions

### 9.1 Constraints
- **CON-01**: Technology stack constrained to FastAPI (Python 3.13) backend, PostgreSQL relational database, React/TypeScript/Tailwind CSS frontend, and Docker orchestration.
- **CON-02**: Academic Course Delivery Plan (CDP) mandates demonstrating a formal Client Change Request (Phase 38: introduction of negative marking) and demonstrating measurable dependency reduction (Phase 36).
- **CON-03**: Zero tolerance for fabricated security metrics, fake SonarQube reports, or simulated vulnerabilities.

### 9.2 Assumptions
- **ASM-01**: Students and faculty possess modern web browsers with JavaScript enabled (Chrome, Firefox, Safari, Edge).
- **ASM-02**: Faculty author questions in fair, unambiguous language and verify correct answer keys prior to exam publication.
- **ASM-03**: The server environment maintains accurate network time synchronization (NTP) to guarantee authoritative timer precision.

---

## 10. Acceptance Criteria (AC)

| Req ID | Acceptance Criteria | Verification Method |
| :--- | :--- | :--- |
| **SEC-AUTH-01** | Passwords stored in `users.hashed_password` begin with `$argon2id$` and cannot be decrypted. | Automated Unit Test |
| **SEC-AUTH-02** | Registration payload with password `weak` returns HTTP 422 with specific complexity guidance. | Automated Unit Test |
| **SEC-AUTH-03** | Attempting login with non-existent email returns HTTP 401 with generic message `Invalid email or password`. | Automated Integration Test |
| **SEC-RBAC-01** | Student token requesting `POST /api/v1/exams` returns HTTP 403 Forbidden. | Automated Security Test |
| **SEC-IDOR-01** | Student A requesting `GET /api/v1/attempts/{Student B Attempt ID}` returns HTTP 403 Forbidden. | Automated Security Test |
| **SEC-IDOR-02** | Faculty A attempting to edit Faculty B''s exam returns HTTP 403 Forbidden. | Automated Security Test |
| **SEC-TIMER-01** | Exam attempt submitted `expires_at + 20s` later is rejected with HTTP 400 Expired. | Automated Security Test |
| **SEC-SCORE-01** | Student submitting answers `[{question_id: 1, option_id: 2, score: 999}]` has `score` field ignored by server; server calculates verified score. | Automated Security Test |
| **SEC-SQLI-01** | Passing injection payload `'' OR 1=1 --` into exam search endpoint executes safely as a parameterized literal. | Automated Security Test |
| **SEC-XSS-01** | Question prompt containing `<script>alert(1)</script>` is sanitized to strip script tags upon ingestion. | Automated Security Test |
| **SEC-RATE-01** | Exceeding 10 login attempts within 60 seconds returns HTTP 429 Too Many Requests. | Automated Security Test |
| **SEC-AUDIT-01** | Creating an exam inserts an immutable record in `audit_logs` table with action `EXAM_CREATED`. | Automated Integration Test |

---

## 11. Course Outcome (CO) Traceability Matrix
- **CO1 (Develop secure system models)**: Addressed via Problem Statement (Sec. 1), Stakeholders & Actors (Sec. 4-5), Functional Requirements (Sec. 6), Security Requirements (Sec. 8), and Acceptance Criteria (Sec. 10).
- **CO2 (Apply threat modeling)**: Addressed via Explicit Security Requirements (SEC-AUTH through SEC-AUDIT) which directly map to STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).
- **CO3 (Security economics & containerization)**: Addressed via Non-Functional Deployment Requirements (Sec. 7.6) and Container Security Requirements (SEC-CONT-01 to 03).
- **CO4 (Security testing, governance & compliance)**: Addressed via Acceptance Criteria (Sec. 10), Audit Logging (SEC-AUDIT), Dependency Security (SEC-DEP), and testable verification methods.
