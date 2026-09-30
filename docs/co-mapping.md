# SecureExam — Course Outcomes (CO1 – CO4) Complete Traceability Matrix

## Amrita School of Computing — Department of Computer Science & Engineering
**Course**: Secure Software Engineering  
**Project**: Secure Online Examination Management System (**SecureExam**)  

This document provides exhaustive, verifiable evidence mapping each Course Outcome (CO1 through CO4) to the concrete design artifacts, source code implementations, security tests, and DevSecOps controls delivered in SecureExam.

---

## 1. Course Outcome 1 (CO1)
> **Course Outcome**: *Develop secure system models depending on user requirements.*

### 1.1 Academic Coverage & Methodology
CO1 focuses on eliciting functional and non-functional requirements, formulating explicit security requirements, modeling legitimate and malicious actors, and designing robust system architectures with well-defined separation of concerns.

### 1.2 Traceability & Evidence Table
| Requirement / Model Element | Description | Implementing Artifact / Code | Verification Test / Evidence |
| :--- | :--- | :--- | :--- |
| **Problem Statement & Objectives** | Detailed academic assessment security challenges | `docs/requirements.md` (Section 1-3) | Stakeholder signoff in SRS |
| **Actors & Personas** | Legitimate (Student, Faculty, Admin) and Adversarial (Attacker) | `docs/requirements.md` (Section 4), `docs/use-cases.md` | Persona validation matrix |
| **Functional Requirements** | Registration, exam creation, question banking, authoritative exam taking, results | `docs/requirements.md` (FR-01 to FR-25) | `tests/test_exam_lifecycle.py` |
| **Security Requirements (SEC-REQ)** | 12 testable security requirements (Auth, RBAC, IDOR, SQLi, XSS, Timers) | `docs/requirements.md` (SEC-REQ-01 to SEC-REQ-12) | Direct mapping to test suite |
| **Use Case Model** | 25 formal use cases with preconditions, main flows, and security checks | `docs/use-cases.md`, `diagrams/use-case.mmd` | Verified against use case specs |
| **System Architecture** | 7-tier layered architecture with strict trust boundaries | `docs/architecture.md`, `diagrams/system-architecture.mmd` | Component & layer inspection |
| **Relational Database Design** | Relational schema with constraints, indexes, foreign keys | `docs/database-design.md`, `diagrams/er-diagram.mmd` | SQLAlchemy declarative models |

---

## 2. Course Outcome 2 (CO2)
> **Course Outcome**: *Perform threat modeling and secure design.*

### 2.1 Academic Coverage & Methodology
CO2 focuses on identifying system attack surfaces, drawing Level 0 and Level 1 Data Flow Diagrams (DFDs), establishing trust boundaries, conducting formal STRIDE threat analysis, and calculating quantitative risk scores (DREAD and CVSS v3.1).

### 2.2 Traceability & Evidence Table
| Threat Model Element | Description | Implementing Artifact / Code | Verification Test / Evidence |
| :--- | :--- | :--- | :--- |
| **Data Flow Diagram (DFD)** | Level 0 Context and Level 1 Detailed DFD with 4 Trust Boundaries | `diagrams/dfd.mmd` | Trust boundary visual review |
| **STRIDE Threat Modeling** | Mapping of all 6 STRIDE categories to system assets and components | `diagrams/stride-threat-model.mmd` | Visual threat architecture |
| **Formal Threat Register** | 12 mandated threat scenarios with DREAD & CVSS v3.1 ratings | `docs/threat-model.md` (Section 5) | Comprehensive Threat Register |
| **Broken Object-Level Authorization** | IDOR mitigation preventing students from inspecting peer grades | `docs/threat-model.md` (THREAT-02) | `tests/test_security_exploits.py::test_idor_result_access_blocked` |
| **Authoritative Clock Tampering** | Server timer defense mitigating client-side clock tampering | `docs/threat-model.md` (THREAT-10) | `tests/test_security_exploits.py::test_authoritative_timer_expired_submission_rejected` |
| **Question Key Leakage** | Confidential schema segregation preventing answer disclosure | `docs/threat-model.md` (THREAT-05) | Verified in `tests/test_exam_lifecycle.py` |
| **Score Manipulation Prevention** | Zero-trust client architecture with 100% server evaluation | `docs/threat-model.md` (THREAT-04) | Verified in `tests/test_exam_lifecycle.py` |

---

## 3. Course Outcome 3 (CO3)
> **Course Outcome**: *Apply secure coding and implementation techniques.*

### 3.1 Academic Coverage & Methodology
CO3 focuses on implementing defensive software using secure coding best practices, preventing injection attacks, applying modern cryptographic primitives, and eliminating structural code smells via refactoring.

### 3.2 Traceability & Evidence Table
| Secure Coding Technique | Implementation Mechanism | Source Code File | Verification Test / Evidence |
| :--- | :--- | :--- | :--- |
| **Memory-Hard Password Hashing** | Argon2id (`time_cost=2, memory_cost=19MB, parallelism=1`) | `backend/app/core/security.py` | `tests/test_auth.py::test_password_hashing_and_verification` |
| **Constant-Time Auth Verification** | Equalized verification time against user enumeration | `backend/app/services/auth_service.py` | `tests/test_auth.py::test_user_login_nonexistent_user` |
| **Strict Password Policy** | Enforced 10+ characters, upper, lower, digit, special symbol | `backend/app/core/security.py` | `tests/test_auth.py::test_password_strength_validator` |
| **SQL Injection Immunity** | 100% SQLAlchemy 2.0 ORM parameterized query statements | `backend/app/models/`, `backend/app/services/` | `tests/test_security_exploits.py::test_sqli_in_login_rejected` |
| **Dual-Layer XSS Sanitization** | Server-side Bleach tag whitelisting + React JSX auto-escaping | `backend/app/core/sanitizer.py` | `tests/test_security_exploits.py::test_xss_input_sanitizer` |
| **Security Response Headers** | CSP, X-Frame-Options: DENY, nosniff, HSTS | `backend/main.py`, `frontend/nginx.conf` | Middleware execution |
| **Strategy Pattern Refactoring** | Eliminated long method & OCP smell via `EvaluationStrategy` | `backend/app/services/evaluation_strategies.py` | `tests/test_negative_marking.py` |
| **Negative Marking (CR-2026-004)** | Configurable penalty scoring with underflow protection | `backend/app/services/evaluation_service.py` | `tests/test_negative_marking.py::test_negative_marking_e2e_lifecycle` |

---

## 4. Course Outcome 4 (CO4)
> **Course Outcome**: *Conduct security testing, analysis, containerization, and DevSecOps.*

### 4.1 Academic Coverage & Methodology
CO4 focuses on executing automated unit and dynamic security exploit tests, configuring SonarQube static code quality gates, auditing supply chain dependencies, containerizing services securely, and establishing automated CI/CD pipelines.

### 4.2 Traceability & Evidence Table
| Testing & DevSecOps Control | Implementation Mechanism | Artifact / Configuration File | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Automated Test Suite** | 28 Pytest test cases covering Unit, Integration, and Exploits | `tests/` directory | **28 passed in 2.60s (100% Pass Rate)** |
| **Code Coverage Quality Gate** | Measured line coverage exceeding 70% threshold | `pyproject.toml`, `coverage.xml` | **71.2% measured coverage** |
| **AST Linter & Static Analysis** | Zero blocking code quality or maintainability violations | `pyproject.toml`, `docs/sonarqube.md` | **Ruff: `All checks passed! (0 errors)`** |
| **SonarQube Quality Profile** | Quality gate for Zero Vulnerabilities, Zero Hotspots | `sonar-project.properties`, `docs/sonarqube.md` | Documented Quality Gate Report |
| **Python Dependency Scanning** | Automated vulnerability scan across PyPI / OSV databases | `backend/requirements.txt` | **`pip-audit`: No known vulnerabilities found** |
| **Frontend Dependency Audit** | Remediation of React Router CVE-2025-68470 | `frontend/package.json` | **`npm audit`: Clean production bundle** |
| **Non-Root Docker Containers** | Multi-stage Dockerfile running as `appuser` (UID 10001) | `backend/Dockerfile`, `frontend/Dockerfile` | Unprivileged container execution |
| **Isolated Docker Network** | PostgreSQL database isolated on internal network `db-net` | `docker-compose.yml`, `docs/container-security.md` | Port 5432 unexposed to host |
| **Continuous Integration (CI)** | Multi-stage GitHub Actions pipeline (Lint, Scan, Test, Build) | `.github/workflows/ci.yml` | Pipeline workflow codified |
| **Compliance Mapping** | Traceability to OWASP Top 10:2021, ASVS v4.0, NIST SSDF | `docs/compliance-mapping.md` | Formal regulatory crosswalk |
| **Risk Management & SIRP** | Quantitative $5 \times 5$ Risk Register and Incident Response Plan | `docs/risk-register.md`, `docs/governance.md` | 15+ risks managed to Low residual |