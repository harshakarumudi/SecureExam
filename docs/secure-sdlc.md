# Secure Software Development Life Cycle (S-SDLC) Framework

## 1. Introduction & Course Outcomes Alignment
Secure Software Engineering requires integrating security into every phase of the software engineering lifecycle rather than treating security as an afterthought or late penetration testing phase.

SecureExam operationalizes the Secure SDLC across all stages, directly satisfying the Amrita School of Computing Course Delivery Plan:
- **CO1**: Security Requirements Engineering, Threat Classification, Security Metrics
- **CO2**: Secure Design, Threat Modeling (STRIDE/DREAD), Architecture Segmentation
- **CO3**: Defensive Implementation, Memory Safety, Cryptographic Primitives, Input Sanitization
- **CO4**: Security Testing, SonarQube Quality Gates, DevSecOps CI/CD, Governance & Compliance

---

## 2. Secure SDLC Phase-by-Phase Integration

```
[ Phase 1: Requirements ]  ──► Misuse Cases, Security Requirements (docs/requirements.md)
           │
[ Phase 2: Secure Design ] ──► STRIDE Threat Modeling, Trust Boundaries (docs/threat-model.md)
           │
[ Phase 3: Secure Coding ] ──► Defensive Coding, Argon2id, ORM Parameterization, Bleach XSS Filter
           │
[ Phase 4: Testing & QA  ] ──► Automated Security Tests, IDOR/SQLi Exploits, Pytest (tests/)
           │
[ Phase 5: CI/CD Pipeline] ──► Automated Linting (Ruff), Dependency Scanning (pip-audit), Docker
           │
[ Phase 6: Monitoring & Ops] ──► Immutable Audit Trails, Rate Limiting, Role Governance
```

### Phase 1: Requirements Engineering (CO1)
- **Activity**: Derivation of Functional and Non-Functional Security Requirements.
- **Artifacts**: `docs/requirements.md`.
- **Key Milestones**: Formulated 12 explicit security requirements (`SEC-REQ-01` through `SEC-REQ-12`) covering authentication, RBAC, IDOR/BOLA prevention, timer integrity, and auditability.
- **Abuse & Misuse Modeling**: Created adversarial personas (unauthorized student, inquisitive faculty, automated botnet).

### Phase 2: Architecture & Secure Design (CO2)
- **Activity**: System decomposition, attack surface mapping, and threat modeling.
- **Artifacts**: `docs/architecture.md`, `diagrams/dfd.mmd`, `diagrams/stride-threat-model.mmd`.
- **Key Milestones**:
  - Partitioned system into 4 distinct Trust Zones separated by 4 Trust Boundaries.
  - Implemented 12 formal STRIDE threat scenarios with DREAD scoring and CVSS v3.1 ratings.
  - Established Server-Authoritative Architecture: Client machine clocks and client code have zero authority over examination time limits or score calculations.

### Phase 3: Defensive Implementation (CO3)
- **Activity**: Safe code construction using secure coding standards.
- **Artifacts**: `backend/app/core/`, `backend/app/services/`.
- **Key Milestones**:
  - Cryptography: Argon2id password hashing with constant-time verification.
  - Session Security: High-entropy HMAC-SHA256 JWT tokens.
  - Injection Defense: 100% SQLAlchemy 2.0 ORM parameterized query statements.
  - Sanitization: Dual-layer XSS defense via `bleach` server-side HTML cleaning and React 18 contextual JSX escaping.

### Phase 4: Security Verification & Testing (CO4)
- **Activity**: Automated dynamic test execution and static code analysis.
- **Artifacts**: `tests/`, `sonar-project.properties`, `docs/sonarqube.md`.
- **Key Milestones**:
  - Created 23 automated tests covering authentication, RBAC, full exam lifecycle, and explicit exploit vectors (SQLi, XSS, BOLA/IDOR, timer expiry, replay).
  - Enforced SonarQube Quality Gate with 71.2% measured coverage and zero open vulnerabilities.

### Phase 5: DevSecOps & Containerization (CO4)
- **Activity**: Build automation, dependency security, container isolation.
- **Artifacts**: `.github/workflows/ci.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`.
- **Key Milestones**:
  - Non-root container runtime (`appuser` UID 10001, `nginx`).
  - Isolated internal database network (`db-net`).
  - Automated dependency vulnerability scans with `pip-audit` and `npm audit`.

### Phase 6: Security Governance & Risk Management (CO1, CO4)
- **Activity**: Risk monitoring, incident handling, and regulatory compliance.
- **Artifacts**: `docs/governance.md`, `docs/risk-register.md`, `docs/compliance-mapping.md`.
- **Key Milestones**:
  - Append-only security audit logs tracking IP, actor, role, status, and details.
  - Structured change management via Client Change Request RFCs.