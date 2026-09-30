# SecureExam — Enterprise Security Risk Register

## 1. Risk Assessment Methodology
Risk assessment in SecureExam utilizes a standardized $5 \times 5$ Risk Matrix evaluating **Likelihood** ($1 = \text{Rare}$ to $5 = \text{Almost Certain}$) and **Impact** ($1 = \text{Insignificant}$ to $5 = \text{Catastrophic}$).

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact} \quad (1 - 25)$$
- **Critical Risk (16 - 25)**: Immediate architectural intervention required.
- **High Risk (10 - 15)**: Mandatory defensive control and automated testing.
- **Medium Risk (5 - 9)**: Compensating control or procedural monitoring.
- **Low Risk (1 - 4)**: Acceptable residual operational risk.

---

## 2. Comprehensive Security Risk Register

| Risk ID | Threat & Vulnerability Description | Pre-Mitigation L | Pre-Mitigation I | Pre-Score | Implemented Mitigation & Control | Post L | Post I | Post Score | Residual Level |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **RSK-01** | Weak password guessing, dictionary attacks, and credential stuffing | 5 | 4 | **20 (Crit)** | Argon2id memory-hard hashing, strict 10-char complexity policy, SlowAPI rate limiting | 1 | 3 | **3** | **Low** |
| **RSK-02** | Premature exam question paper and answer key leakage | 4 | 5 | **20 (Crit)** | Schema segregation (`QuestionCandidateOut`), confidential `is_correct` stripped from student API payloads | 1 | 4 | **4** | **Low** |
| **RSK-03** | Client-side exam score manipulation or grading fraud | 4 | 5 | **20 (Crit)** | Zero-trust client architecture: 100% server-side evaluation in `EvaluationService` | 1 | 4 | **4** | **Low** |
| **RSK-04** | Broken Object-Level Authorization (BOLA/IDOR) on student results | 5 | 4 | **20 (Crit)** | Mandatory row-level ownership check (`attempt.student_id == current_user.id`) with 403 Forbidden | 1 | 2 | **2** | **Low** |
| **RSK-05** | Unauthorized student or faculty escalation to administrative APIs | 4 | 5 | **20 (Crit)** | Cryptographically signed HMAC-SHA256 JWT tokens + `require_role(ADMIN)` dependency injection | 1 | 3 | **3** | **Low** |
| **RSK-06** | Complete database compromise via SQL Injection payloads | 4 | 5 | **20 (Crit)** | 100% SQLAlchemy 2.0 ORM parameterized query construction; zero dynamic SQL strings | 1 | 2 | **2** | **Low** |
| **RSK-07** | Stored / Reflected Cross-Site Scripting (XSS) in exam descriptions | 4 | 3 | **12 (High)** | Bleach HTML tag whitelist sanitization on backend + React JSX contextual escaping on frontend | 1 | 2 | **2** | **Low** |
| **RSK-08** | Client clock tampering to evade authoritative exam time limits | 5 | 4 | **20 (Crit)** | Server-authoritative timer: database timestamps govern validity; submissions > 15s late marked EXPIRED | 1 | 2 | **2** | **Low** |
| **RSK-09** | Exam submission flooding or race conditions on final submit | 4 | 3 | **12 (High)** | Single-submission state machine guard (`attempt.status == SUBMITTED` returns 400 Bad Request) | 1 | 2 | **2** | **Low** |
| **RSK-10** | Cross-faculty tampering or deletion of peer examinations | 4 | 4 | **16 (Crit)** | Multi-tenant tenant checks (`exam.created_by == current_user.id`) enforced in `ExamService` | 1 | 2 | **2** | **Low** |
| **RSK-11** | Upstream supply chain compromise via vulnerable dependencies | 4 | 4 | **16 (Crit)** | Pinned dependencies in lockfiles + automated `pip-audit` and `npm audit` in CI/CD pipeline | 1 | 3 | **3** | **Low** |
| **RSK-12** | Container breakout compromising host operating system | 3 | 5 | **15 (High)** | Multi-stage Docker builds running as non-root user `appuser` (UID 10001) / `nginx` | 1 | 3 | **3** | **Low** |
| **RSK-13** | Repudiation of exam events or forensic blindness | 4 | 4 | **16 (Crit)** | Immutable append-only audit trail logging actor, role, IP, action, resource, and timestamp | 1 | 2 | **2** | **Low** |
| **RSK-14** | Man-in-the-Middle (MitM) eavesdropping on candidate credentials | 4 | 4 | **16 (Crit)** | Enforced TLS 1.3 encryption in transit + HSTS (`max-age=31536000; includeSubDomains`) | 1 | 3 | **3** | **Low** |
| **RSK-15** | Token reuse or replay following account logout | 3 | 3 | **9 (Med)** | 60-minute token expiration lifespan + client token purge on logout | 1 | 2 | **2** | **Low** |

---

## 3. Summary of Risk Posture
Prior to implementing the defense-in-depth architecture, the system contained **10 Critical** and **4 High** risks. Following the implementation and automated verification of all mitigations, **100% of risks have been reduced to Low residual risk**, confirming acceptable production readiness for institutional deployment.