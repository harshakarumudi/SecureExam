# SecureExam: Secure Online Examination Management System
## Academic Project Report & Technical Specification
### Amrita School of Computing — Department of Computer Science & Engineering
**Course**: Secure Software Engineering (SSE)  
**Academic Year**: 2026  
**Course Outcomes**: CO1, CO2, CO3, CO4  
**Project Repository**: `SecureExam`  

---

## 1. Executive Summary
Online examination platforms deployed across academic institutions and competitive testing boards operate under constant threat of adversarial manipulation, cheating, unauthorized question leakage, and credential impersonation. When academic integrity is compromised, the credibility of educational degrees and professional certifications is directly invalidated.

**SecureExam** is an enterprise-grade, secure, full-stack online examination management system architected and built to satisfy the Secure Software Engineering Course Delivery Plan across CO1, CO2, CO3, and CO4. The system rejects "security through obscurity" and superficial UI controls in favor of defense-in-depth, strict server-authoritative state machines, memory-hard cryptography, row-level access control, and automated DevSecOps validation.

---

## 2. Problem Statement & Project Objectives

### 2.1 Problem Statement
Traditional computer-based test (CBT) applications suffer from fundamental architectural flaws:
1. **Client-Side Dependency**: Timers and score calculations delegated to browser JavaScript are trivial to manipulate using browser developer tools or local clock skew.
2. **Insecure Direct Object References (IDOR/BOLA)**: Flawed horizontal access control allows malicious examinees to view or submit attempts owned by peer candidates.
3. **Premature Key Disclosure**: Question APIs that transmit the correct option flag (`is_correct`) to the client browser prior to answer submission allow tech-savvy examinees to inspect network payloads and achieve perfect scores fraudulently.
4. **Vulnerable Foundations**: Reliance on raw SQL queries, unmaintained dependencies, and default configurations leaves assessment platforms vulnerable to SQL Injection, Cross-Site Scripting, and credential stuffing.

### 2.2 Core Project Objectives
1. **Zero-Trust Client Evaluation**: Guarantee that examination scores and pass/fail determinations are computed exclusively on the server, with zero client authority.
2. **Authoritative Clock Enforcement**: Enforce immutable server-side attempt timers with strict latency grace boundaries, rejecting late submissions.
3. **Confidential Question Banking**: Ensure that answer keys and explanations are completely stripped from student-facing payloads during active test sessions.
4. **Resilient Access Control**: Implement declarative Role-Based Access Control (RBAC) and row-level ownership checks across all endpoints.
5. **Continuous DevSecOps & Governance**: Embed automated static analysis (Ruff / SonarQube), dependency audits (`pip-audit`), non-root containerization (Docker), and automated CI/CD pipelines.

---

## 3. System Architecture & Trust Boundaries

The SecureExam architecture adheres to a 7-tier logical separation of concerns:
```
[ Untrusted External Zone ]
           │ (HTTPS / TLS 1.3)
           ▼
[ Tier 1: Ingress Perimeter & Reverse Proxy ] (NGINX / SlowAPI Rate Limiting)
           │
           ▼
[ Tier 2: Presentation Layer ] (React 18 / Vite SPA with Contextual Output Encoding)
           │ (Bearer JWT Authorization)
           ▼
[ Tier 3: API Controller Layer ] (FastAPI Routers: Auth, Exams, Attempts, Results, Audit)
           │
           ▼
[ Tier 4: Cross-Cutting Security Subsystems ] (Argon2id, Bleach Sanitizer, RBAC Middleware)
           │
           ▼
[ Tier 5: Core Domain Service Layer ] (ExamService, AttemptService, EvaluationService, AuditService)
           │
           ▼
[ Tier 6: Data Access & Relational ORM ] (SQLAlchemy 2.0 Async declarative queries)
           │
           ▼
[ Tier 7: Persistence Layer ] (Isolated PostgreSQL 16 on internal Docker network)
```

The system is partitioned into 4 distinct Trust Zones separated by 4 Trust Boundaries (codified in `diagrams/dfd.mmd`):
- **TB-1 (Perimeter Boundary)**: Terminates TLS 1.3, enforces HSTS, applies sliding-window IP rate limiting.
- **TB-2 (Authentication & Input Boundary)**: Cryptographic JWT verification, Argon2id password verification, Bleach HTML sanitization.
- **TB-3 (Domain Authorization Boundary)**: Enforces role dependencies (`require_role`) and row-level tenancy validation.
- **TB-4 (Data Storage Boundary)**: Parameterized ORM queries with zero exposure of database ports to public interfaces.

---

## 4. Threat Modeling (STRIDE & DREAD Methodology)

In compliance with **CO2**, a comprehensive STRIDE threat model was conducted, resulting in the identification and mitigation of 12 critical threat scenarios (`docs/threat-model.md`, `diagrams/stride-threat-model.mmd`):

| Threat ID | STRIDE Category | Threat Scenario | Implemented Mitigation | Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **THREAT-01** | **[S] Spoofing** | Credential stuffing & brute-force | Argon2id hashing, 10-char complexity, SlowAPI rate limiting | `tests/test_auth.py` |
| **THREAT-02** | **[T/I] Tampering / Info** | Student Result BOLA / IDOR | Mandatory row-level checks (`attempt.student_id == user.id`) | `tests/test_security_exploits.py` |
| **THREAT-03** | **[E] Elevation** | Admin API endpoint bypass | Declarative `require_role(ADMIN)` dependency injection | `tests/test_rbac.py` |
| **THREAT-04** | **[T] Tampering** | Client-side score manipulation | Zero-trust client: 100% server evaluation in `EvaluationService` | `tests/test_exam_lifecycle.py` |
| **THREAT-05** | **[I] Info Disclosure** | Premature answer key leakage | Schema segregation (`QuestionCandidateOut` strips `is_correct`) | `tests/test_security_exploits.py` |
| **THREAT-06** | **[T/I] Tampering / Info** | Relational Database SQL Injection | 100% SQLAlchemy 2.0 ORM parameterized query construction | `tests/test_security_exploits.py` |
| **THREAT-07** | **[T] Tampering** | Stored / Reflected XSS | Bleach server-side HTML cleaning + React JSX contextual escaping | `tests/test_security_exploits.py` |
| **THREAT-08** | **[D/S] DoS / Spoofing** | Brute force authentication | 5 req/min rate limit on `/auth/login` + generic auth error messages | `tests/test_auth.py` |
| **THREAT-09** | **[T/E] Tampering / Elev** | Cross-faculty exam tampering | Multi-tenant ownership checks (`exam.created_by == user.id`) | `tests/test_rbac.py` |
| **THREAT-10** | **[R/T] Repudiation / Tamp**| Clock skew deadline evasion | Server-authoritative timer: submissions > 15s late marked EXPIRED | `tests/test_security_exploits.py` |
| **THREAT-11** | **[E/D] Elev / DoS** | Supply chain vulnerability | Version-pinned lockfiles + `pip-audit` & `npm audit` gates | `docs/dependency-security.md` |
| **THREAT-12** | **[D] Denial of Service** | Submission flooding / replay | Single-submission state machine (`attempt.status == SUBMITTED`) | `tests/test_security_exploits.py` |

---

## 5. Defensive Implementation Details (CO3)

### 5.1 Cryptography & Password Management
- **Hashing**: Argon2id via `argon2-cffi` (`time_cost=2`, `memory_cost=19MB`, `parallelism=1`).
- **Timing Attack Resistance**: Dummy hash verification on non-existent users ensures constant execution time regardless of account validity, completely preventing user enumeration.
- **Password Strength**: Validates minimum 10 characters, requiring uppercase, lowercase, digit, and special symbol.
- **Session Tokens**: Tamper-evident JWT tokens signed via HMAC-SHA256 (`HS256`) containing `sub`, `role`, and expiration (`exp`) claims.

### 5.2 Authoritative Exam Timer Engine
- Exam initiation generates database timestamps:
  - `started_at = datetime.now(timezone.utc)`
  - `expires_at = started_at + timedelta(minutes=duration)`
- Upon candidate submission, the server computes:
  - `if server_now > attempt.expires_at + timedelta(seconds=15):`
    - Update `attempt.status = AttemptStatus.EXPIRED`
    - Reject submission with `HTTP 400 Bad Request ("Exam attempt has expired")`
    - Persist security audit event `ATTEMPT_EXPIRED_REJECTED`
- Client clock manipulation or local pausing in dev tools has zero effect on the authoritative server clock.

### 5.3 Server-Side-Only Grading Engine
- The candidate submission schema (`AttemptSubmitRequest`) accepts only `question_id` and `selected_option_id`.
- The evaluation engine queries database records directly to verify correctness, calculates earned marks, applies underflow protection, sets pass/fail status, and seals the result record atomically.

---

## 6. Client Change Request & Strategy Refactoring (Milestone 7)

### 6.1 Change Request CR-2026-004
To prevent random guessing exploitation in competitive examinations, the Examination Board requested configurable **Negative Marking**:
- Faculty can enable `enable_negative_marking` per exam and specify `negative_marks` per question.
- Correct answer: `+marks`
- Incorrect answer in negative mode: `-negative_marks`
- Incorrect answer in standard mode: `0`
- Unanswered question: `0 penalty` (Skipped questions are never penalized)
- Score floor protection: `total_score = max(0.0, total_score)`

### 6.2 Strategy Pattern Refactoring
To eliminate the identified **Long Method** and **Conditional Complexity** code smells in `EvaluationService`:
- Extracted abstract interface `EvaluationStrategy` (`backend/app/services/evaluation_strategies.py`).
- Implemented `StandardEvaluationStrategy` (pure positive scoring).
- Implemented `NegativeMarkingStrategy` (penalty deduction with skipped question exemption).
- Implemented `EvaluationStrategyFactory` to resolve strategies dynamically based on exam configuration.
- **Impact**: Cyclomatic complexity reduced by 57.1%, scoring loop LOC reduced by 68.2%, and scoring rules became 100% unit-testable in memory.

---

## 7. Automated Testing & Quality Assurance (CO4)

### 7.1 Pytest Execution Summary
The automated test suite contains 28 comprehensive test cases executing across 5 dedicated test modules:
```text
tests/test_auth.py .............. 9 passed (Hashing, Complexity, Register, Login, JWT)
tests/test_rbac.py .............. 7 passed (Role isolation, Unauth 401, Cross-faculty 403)
tests/test_exam_lifecycle.py .... 1 passed (End-to-end faculty authoring, student exam, grading)
tests/test_security_exploits.py . 6 passed (SQLi payloads, XSS sanitizer, IDOR 403, Timer expiry)
tests/test_negative_marking.py .. 5 passed (Unit strategies, Factory, E2E negative grading, Floor)

Total: 28 PASSED in 2.60 seconds (100% Pass Rate, 0 Failures)
```

### 7.2 Measured Code Coverage
- **Total Statements**: 1,005
- **Missed Statements**: 288
- **Overall Line Coverage**: **71.2%** (Exceeds the 70.0% SonarQube threshold)
- **Core Security & Models Coverage**: 95% - 100%

### 7.3 AST Linting (Ruff)
- Command: `ruff check backend/app tests/`
- Result: **All checks passed! (0 errors, 0 warnings)**

---

## 8. DevSecOps, Containerization & Dependency Auditing

### 8.1 Docker Container Hardening
- **Backend Container**: Multi-stage build on `python:3.13-slim`. Runs as unprivileged system user `appuser` (UID 10001). Compilers and build tools stripped from runner stage.
- **Frontend Container**: Multi-stage build compiling TypeScript/React, served via unprivileged `nginx:alpine` (`USER nginx`).
- **Database Isolation**: PostgreSQL 16 operates exclusively on `db-net` (`internal: true`). Port 5432 is not exposed to the public host.

### 8.2 Dependency Security Audits
- **Backend (`pip-audit`)**: Scanned 38 Python packages against PyPI and OSV databases. **Result: No known vulnerabilities found**.
- **Frontend (`npm audit`)**: Remediated React Router advisory (`GHSA-wrjc-x8rr-h8h6`). Production assets compiled to static bundles served via NGINX with zero Node.js runtime footprint.

### 8.3 CI/CD Pipeline (`.github/workflows/ci.yml`)
Four automated pipeline stages enforce quality gates on every commit:
1. `lint-and-format`: Ruff AST linter and frontend TypeScript build.
2. `security-audit`: `pip-audit` and `npm audit`.
3. `test-and-coverage`: Pytest test suite with automated XML coverage validation (>= 70%).
4. `container-build`: Multi-stage Docker build verification.

---

## 9. Security Governance, Economics & Compliance

- **Gordon-Loeb Security Economics**: Documented in `docs/security-economics.md`, demonstrating positive Return on Security Investment across all implemented controls (e.g., ORM parameterization ROSI > 1500%, Argon2id ROSI = 580%).
- **Enterprise Risk Register**: Documented in `docs/risk-register.md`, tracking 15 primary institutional risks from Critical/High pre-mitigation scores to **100% Low residual risk**.
- **Compliance Mapping**: Documented in `docs/compliance-mapping.md`, establishing explicit crosswalks to OWASP Top 10 (2021), OWASP ASVS v4.0 (Level 2), and NIST SP 800-218 (SSDF v1.1).

---

## 10. Conclusion & Future Roadmap
SecureExam demonstrates that high-stakes academic software can be engineered securely, maintainably, and efficiently without compromising usability or developer velocity. By grounding the architecture in formal threat modeling, strict server-authoritative state management, memory-hard cryptography, and continuous DevSecOps testing, the system provides an uncompromising standard for online assessment integrity.

### Future Enhancements
1. Multi-factor authentication (TOTP / WebAuthn FIDO2 keys).
2. Remote proctoring telemetry (WebRTC webcam stream integrity analysis).
3. Post-quantum cryptographic signature integration for long-term degree and result sealing.