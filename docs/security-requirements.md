# SecureExam — Formal Security Requirements Specification (SRS-SEC)

## 1. Overview
This document specifies the 12 non-negotiable security requirements for SecureExam, directly derived from the SRS (`docs/requirements.md`), threat model (`docs/threat-model.md`), and Amrita School of Computing Course Delivery Plan.

---

## 2. Testable Security Requirements Specification

| Requirement ID | Requirement Title | Category | Technical Specification | Verifying Pytest Suite |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-REQ-01** | Argon2id Password Hashing | Cryptography | All user passwords must be hashed using Argon2id with memory cost >= 19MB, time cost >= 2, and parallelism >= 1. Plaintext passwords must never be logged or persisted. Constant-time verification must prevent timing enumeration. | `tests/test_auth.py::test_password_hashing_and_verification` |
| **SEC-REQ-02** | Result Object-Level Authorization (IDOR) | Access Control | The platform must enforce strict row-level ownership checks preventing candidates from viewing or modifying attempts or scores owned by other candidates. Violations must return HTTP 403. | `tests/test_security_exploits.py::test_idor_result_access_blocked` |
| **SEC-REQ-03** | Server-Side RBAC Enforcement | Authorization | Administrative and faculty endpoints must be protected server-side via declarative role dependencies (`require_role`). Client-side UI route protection must not be relied upon for security. | `tests/test_rbac.py` |
| **SEC-REQ-04** | Server-Side-Only Grading Engine | Integrity | All examination scoring, penalty calculations, and pass/fail determinations must be calculated strictly on the server. The submission schema must accept only selected option IDs. | `tests/test_exam_lifecycle.py`, `tests/test_negative_marking.py` |
| **SEC-REQ-05** | Question Key Confidentiality | Confidentiality | The student-facing examination attempt payload must omit correct option indicators (`is_correct`) and explanations to eliminate client-side inspection leakage. | `tests/test_exam_lifecycle.py` |
| **SEC-REQ-06** | SQL Injection Immunity | Input Handling | 100% of relational queries must utilize SQLAlchemy 2.0 ORM parameterized statements. Raw SQL strings, dynamic string formatting, or concatenated SQL queries are strictly prohibited. | `tests/test_security_exploits.py::test_sqli_*` |
| **SEC-REQ-07** | Cross-Site Scripting (XSS) Sanitization | Input/Output | User-supplied textual input in titles, descriptions, and question prompts must be sanitized on the server using a strict Bleach tag whitelist. Frontend rendering must utilize JSX contextual auto-escaping. | `tests/test_security_exploits.py::test_xss_input_sanitizer` |
| **SEC-REQ-08** | Authentication Rate Limiting | Availability | Authentication endpoints must enforce sliding-window rate limiting (maximum 5 attempts per minute per IP address) to prevent brute-force attacks and credential stuffing. | `tests/test_auth.py` |
| **SEC-REQ-09** | Multi-Tenant Exam Isolation | Access Control | Faculty members must be prevented from editing, publishing, adding questions to, or deleting examinations created by other faculty members. | `tests/test_rbac.py::test_cross_faculty_tampering_blocked` |
| **SEC-REQ-10** | Server-Authoritative Exam Timer | Integrity | Active attempt durations must be governed by immutable server timestamps. Submissions exceeding the deadline past a 15-second grace window must be marked EXPIRED and rejected with HTTP 400. | `tests/test_security_exploits.py::test_authoritative_timer_expired_submission_rejected` |
| **SEC-REQ-11** | Dependency & Supply Chain Security | Governance | All direct and transitive third-party dependencies must be pinned and continuously audited against known CVE databases. Critical or high vulnerabilities must block CI/CD pipeline builds. | `docs/dependency-security.md`, `.github/workflows/ci.yml` |
| **SEC-REQ-12** | Single-Submission State Machine | Integrity | Active attempts must transition to SUBMITTED upon completion. Replay or duplicate submission attempts must be immediately rejected with HTTP 400 Bad Request. | `tests/test_security_exploits.py::test_resubmission_attack_blocked` |