# SecureExam — Regulatory & Industry Security Standards Compliance Mapping

## 1. Executive Summary
This document establishes comprehensive compliance traceability between SecureExam's security controls and leading cybersecurity frameworks:
1. **OWASP Top 10: 2021** (Web Application Security Risks)
2. **OWASP Application Security Verification Standard (ASVS) v4.0** (Level 2 Target)
3. **NIST SP 800-218** (Secure Software Development Framework - SSDF v1.1)

---

## 2. OWASP Top 10 (2021) Traceability Matrix

| OWASP 2021 Category | Specific Threat / Vulnerability | SecureExam Architectural Control | Verifying Artifact / Test |
| :--- | :--- | :--- | :--- |
| **A01: Broken Access Control** | Horizontal/vertical escalation, IDOR on exam results | Declarative `require_role()` dependency + row-level ownership checks (`attempt.student_id == user.id`) | `tests/test_rbac.py`, `tests/test_security_exploits.py` |
| **A02: Cryptographic Failures** | Weak password storage, credential exposure in transit | Argon2id hashing (`m=19456, t=2`), HMAC-SHA256 JWT, TLS 1.3 in transit | `backend/app/core/security.py`, `tests/test_auth.py` |
| **A03: Injection** | SQL Injection in queries, XSS in question text | 100% SQLAlchemy 2.0 ORM parameterized queries; Bleach HTML sanitization; React JSX escaping | `tests/test_security_exploits.py` (`test_sqli_*`, `test_xss_*`) |
| **A04: Insecure Design** | Client-side score calculation, exam clock evasion | Server-authoritative design: timer persisted in DB, grading executed 100% on server | `backend/app/services/evaluation_service.py` |
| **A05: Security Misconfiguration** | Missing security headers, exposed database ports | CSP, HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff; `db-net` unexposed to host | `backend/main.py`, `frontend/nginx.conf`, `docker-compose.yml` |
| **A06: Vulnerable Components** | Known CVEs in third-party libraries | Pinned version lockfiles, automated `pip-audit` & `npm audit` in CI/CD pipeline | `docs/dependency-security.md`, `.github/workflows/ci.yml` |
| **A07: Identification & Auth** | Credential stuffing, brute-force, weak passwords | Strict 10-char complexity validation, SlowAPI rate limiting (5/min), generic login errors | `backend/app/core/security.py`, `tests/test_auth.py` |
| **A08: Software & Data Integrity**| Tampered exam submissions, replay attacks | Single-submission state machine, atomic database transaction commits | `backend/app/services/evaluation_service.py` |
| **A09: Logging & Monitoring** | Forensic blindness, repudiation of exam actions | Append-only `audit_logs` capturing actor ID, role, action, resource ID, IP, status, timestamp | `backend/app/services/audit_service.py`, `api/v1/audit.py` |
| **A10: SSRF** | Unauthorized internal service access | Zero outbound HTTP fetch requests accepted from user input; isolated internal network | Architecture boundary TB-4 |

---

## 3. OWASP ASVS v4.0 Verification Mapping

| ASVS Section | Control ID | Control Description | SecureExam Implementation |
| :--- | :--- | :--- | :--- |
| **V1 Architecture** | V1.1.1 | Secure SDLC in place | Documented in `docs/secure-sdlc.md` |
| **V2 Authentication** | V2.1.1 | Verify password minimum length and complexity | `validate_password_strength` enforces 10 chars, uppercase, lowercase, digit, symbol |
| **V2 Authentication** | V2.4.1 | Passwords hashed using memory-hard algorithm | Argon2id implementation in `backend/app/core/security.py` |
| **V3 Session Management** | V3.2.1 | Cryptographically signed session tokens | JWT with HS256 and verified `exp`, `sub`, `role` claims |
| **V4 Access Control** | V4.1.1 | Principle of least privilege enforced server-side | `require_role(STUDENT, FACULTY, ADMIN)` in FastAPI dependencies |
| **V4 Access Control** | V4.1.3 | Access control cannot be bypassed by changing parameters | Row-level checks on attempt ownership in `ResultService` |
| **V5 Input Validation** | V5.1.1 | Input validation before processing | Pydantic v2 schemas enforce types, ranges, regex constraints |
| **V5 Input Validation** | V5.3.1 | Output encoding to prevent XSS | React 18 JSX engine context-aware output encoding |
| **V10 Malicious Code** | V10.2.1 | Upstream dependency vulnerability monitoring | `pip-audit` and `npm audit` verification |
| **V14 Configuration** | V14.4.1 | HTTP security headers present | CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options |

---

## 4. NIST SP 800-218 (SSDF v1.1) Practices Mapping
- **Prepare the Organization (PO)**: Defined security roles, governance, and review policies in `docs/governance.md`.
- **Protect the Software (PS)**: Repository integrity protected via Git commit signing and CI/CD automated gates.
- **Produce Well-Secured Software (PW)**: Threat modeling via STRIDE (`docs/threat-model.md`), memory-safe runtimes, and defensive coding against OWASP vulnerabilities.
- **Respond to Vulnerabilities (RV)**: Security Incident Response Plan, continuous dependency patching, and automated vulnerability scanning.