# SecureExam — Master Project Checklist

Status Key:
- `[ ]` Not Started
- `[~]` In Progress
- `[x]` Completed
- `[!]` Blocked

---

## 0. Phase 0 — Environment and Project Inspection
- [x] Inspect current working directory
- [x] Inspect available development tools (Node.js, npm, Python, pip, Docker, Git, PostgreSQL)
- [x] Inspect whether an existing repository exists
- [x] Do not destroy existing useful files
- [x] Determine whether project is new or existing (Clean New Project)
- [x] Create PROJECT_STATUS.md
- [x] Create PROJECT_CHECKLIST.md
- [x] Create initial Git repository (.gitignore, .env.example)

---

## A. Requirements
- [x] Problem statement documented
- [x] Project objectives defined
- [x] Scope clearly established
- [x] Stakeholders and actors identified (Student, Faculty, Administrator)
- [x] Functional requirements enumerated
- [x] Non-functional requirements (Security, Performance, Availability, Usability, Maintainability, Privacy)
- [x] Deployment requirements and constraints documented
- [x] Assumptions and acceptance criteria specified
- [x] `docs/requirements.md` created
- [x] `backend/requirements.txt` created with pinned versions

---

## B. Architecture
- [x] Clean separation of concerns (Presentation, API, Services, Repositories, DB)
- [x] Cross-cutting security architecture (Auth, Authz, Validation, Rate Limiter, Audit)
- [x] System architecture diagram created (`diagrams/system-architecture.mmd`)
- [x] Component diagram created (`diagrams/component-diagram.mmd`)
- [x] Module communication diagram created (`diagrams/module-communication.mmd`)
- [x] Deployment diagram created (`diagrams/deployment-diagram.mmd`)
- [x] `docs/architecture.md` created

---

## C. Functional Features
### Student Portal
- [ ] Registration with input validation
- [ ] Login and session management
- [ ] Logout
- [ ] View profile
- [ ] View available published examinations
- [ ] View exam instructions and details
- [ ] Start exam attempt (authoritative timer initiation)
- [ ] Single answer MCQ question interface with navigation
- [ ] Submit examination
- [ ] View immediate result and performance summary
- [ ] View history of previous attempts

### Faculty Studio
- [ ] Login and faculty dashboard
- [ ] Create examinations (title, description, marks, duration, dates)
- [ ] Edit owned examinations
- [ ] Delete owned examinations
- [ ] Create, edit, and delete questions with options and explanations
- [ ] Configure marks per question
- [ ] Publish / unpublish examinations
- [ ] Preview exam paper
- [ ] View student attempts and grade breakdown

### Admin Command Center
- [ ] Login and admin dashboard
- [ ] User management (view, activate, deactivate, role assignment)
- [ ] System-wide exam oversight
- [ ] Security audit log viewer with filtering
- [ ] Security event monitoring

---

## D. Security Controls
- [ ] Password hashing via Argon2id / bcrypt
- [ ] Password strength enforcement (length, casing, digits, special characters)
- [ ] Generic authentication error messages (prevent user enumeration)
- [ ] Session / JWT token expiry and secure handling
- [ ] Server-side RBAC (Student, Faculty, Admin)
- [ ] Object-level authorization / BOLA / IDOR protection
- [ ] Authoritative server-side exam timer (expiry rejection)
- [ ] Server-side score evaluation (tamper-proof)
- [ ] Pydantic v2 strict input validation and sanitization
- [ ] SQL injection defense via SQLAlchemy ORM parameterized queries
- [ ] XSS protection (HTML sanitization and modern React escaping)
- [ ] Security headers (CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS)
- [ ] Secure CORS policy
- [ ] Rate limiting on authentication and sensitive endpoints
- [ ] Tamper-evident audit logging for sensitive actions
- [ ] No passwords, tokens, or secrets in logs or git

---

## E. Threat Modeling
- [ ] Data Flow Diagram (DFD) created (`diagrams/dfd.mmd`)
- [ ] Trust boundaries and attack surface mapped
- [ ] STRIDE threat analysis performed (`diagrams/stride-threat-model.mmd`)
- [ ] 12+ formal threat scenarios documented in Threat Register
- [ ] DREAD / CVSS risk ratings calculated
- [ ] Mitigations and residual risk evaluated
- [ ] `docs/threat-model.md` created

---

## F. Testing
- [ ] Automated unit tests for cryptography and password policies
- [ ] Automated unit tests for authoritative exam timer math and expiry
- [ ] Automated unit tests for score evaluation
- [ ] Automated integration tests for user registration and authentication
- [ ] Automated integration tests for faculty exam authoring and publication
- [ ] Automated integration tests for student attempt, submission, and result generation
- [ ] Automated security tests for IDOR / BOLA authorization bypass
- [ ] Automated security tests for SQL injection attack payloads
- [ ] Automated security tests for XSS attack vectors
- [ ] Automated security tests for rate limiting threshold enforcement
- [ ] Pytest test suite passing 100%

---

## G. SonarQube
- [ ] `sonar-project.properties` configured
- [ ] Quality gate thresholds defined
- [ ] Bugs, vulnerabilities, and security hotspots analyzed
- [ ] Code smell and maintainability metrics tracked
- [ ] Before/after remediation documented in `docs/sonarqube.md`

---

## H. Dependency Security
- [ ] Backend dependency audit using `pip-audit`
- [ ] Frontend dependency audit using `npm audit`
- [ ] Direct and transitive dependency inventory documented
- [ ] Vulnerability remediation documented in `docs/dependency-security.md`
- [ ] Zero critical unmitigated vulnerabilities

---

## I. Docker & Containerization
- [ ] Multi-stage Dockerfile for FastAPI backend
- [ ] Multi-stage Dockerfile for React/Vite frontend (NGINX unprivileged)
- [ ] Non-root container execution (`appuser` UID 10001)
- [ ] `docker-compose.yml` orchestrating Frontend, Backend, and PostgreSQL
- [ ] Isolated Docker network (database not publicly bound)
- [ ] Health checks configured for all services
- [ ] Container security and hardening documented in `docs/container-security.md`

---

## J. CI/CD
- [ ] GitHub Actions workflow `.github/workflows/ci.yml`
- [ ] Linting step (Ruff / ESLint)
- [ ] Automated unit and integration test step
- [ ] Static security and dependency audit step
- [ ] Container build step
- [ ] Pipeline failure enforcement on critical security flaws

---

## K. Secure SDLC
- [ ] Secure SDLC stages documented (Requirements -> Design -> Review -> Testing -> CI/CD -> Monitoring)
- [ ] Security activities aligned to every stage in `docs/secure-sdlc.md`

---

## L. Security Economics
- [ ] Security economics framework documented in `docs/security-economics.md`
- [ ] Analysis of cost, runtime overhead, performance, and maintenance for each control
- [ ] Trade-off matrix: Security vs. Cost vs. Performance vs. Complexity

---

## M. Security Governance
- [ ] Security roles and responsibilities defined
- [ ] Least privilege and access control policies established
- [ ] Secure code review process documented
- [ ] Incident response and vulnerability disclosure plan in `docs/governance.md`

---

## N. Risk Management
- [ ] Comprehensive Risk Register in `docs/risk-register.md`
- [ ] Quantitative/qualitative likelihood and impact matrix
- [ ] Residual risk tracking for all core assets

---

## O. Compliance & Framework Mapping
- [ ] OWASP Top 10 (2021) alignment matrix
- [ ] OWASP ASVS v4.0 verification controls mapped
- [ ] NIST Secure Software Development Framework (SSDF) concepts mapped in `docs/compliance-mapping.md`

---

## P. Module Dependency Analysis
- [ ] Module coupling and cohesion analysis
- [ ] Dependency graph documented in `diagrams/module-dependency.mmd`
- [ ] Documentation created in `docs/dependency-analysis.md`

---

## Q. Dependency Reduction
- [ ] Identification of tight coupling and duplicate dependencies
- [ ] Architectural refactoring for dependency decoupling
- [ ] Measured before vs. after coupling comparison in `docs/dependency-reduction.md`

---

## R. Client Change Request (Negative Marking)
- [ ] Formal Change Request recorded in `docs/client-change-request.md`
- [ ] Threat model and security impact analysis updated
- [ ] Backend evaluation logic updated: Correct = +marks, Incorrect = -negative_marks, Unanswered = 0
- [ ] DB schema updated with migration
- [ ] Automated tests written specifically validating negative marking logic
- [ ] Regression testing completed

---

## S. Code Smells
- [ ] Genuine code smells identified in initial implementation
- [ ] Documented in `docs/code-smells-and-refactoring.md` with cyclomatic complexity and maintainability metrics

---

## T. Refactoring
- [ ] Refactoring executed to eliminate identified code smells
- [ ] Before vs. After metrics demonstrated with zero regression

---

## U. Project Documentation
- [ ] Complete `docs/` repository files
- [ ] Traceability matrix linking requirements to design, threats, controls, and tests
- [ ] Professional `README.md`
- [ ] Academic Final Project Report (`docs/final-report.md`)

---

## V. Course Outcome 1 (CO1)
*Develop secure system models depending on user requirements.*
- [ ] Requirements specification (`docs/requirements.md`)
- [ ] Use cases and diagrams (`docs/use-cases.md`, `diagrams/use-case.mmd`)
- [ ] System architecture (`docs/architecture.md`)
- [ ] Relational ER model (`diagrams/er-diagram.mmd`)
- [ ] Security requirements specification (`docs/security-requirements.md`)

---

## W. Course Outcome 2 (CO2)
*Build analysis models and apply threat modeling.*
- [ ] Data Flow Diagram (`diagrams/dfd.mmd`)
- [ ] STRIDE Threat Model (`diagrams/stride-threat-model.mmd`, `docs/threat-model.md`)
- [ ] Attack surface analysis and trust boundaries
- [ ] 12+ scenario threat register with mitigations and test verification

---

## X. Course Outcome 3 (CO3)
*Understand software security economics and practices in containerized development.*
- [ ] Hardened multi-stage Dockerfiles and unprivileged containers
- [ ] Network segmentation in Docker Compose
- [ ] Container security scanning
- [ ] Software security economics analysis (`docs/security-economics.md`)
- [ ] Cost/performance/security trade-off evaluations

---

## Y. Course Outcome 4 (CO4)
*Develop security testing and understand governance, risk and compliance.*
- [ ] Pytest unit, integration, and security exploit test suites
- [ ] SonarQube static analysis and quality gates
- [ ] Dependency vulnerability scanning
- [ ] Risk register and governance models (`docs/governance.md`, `docs/risk-register.md`)
- [ ] OWASP Top 10, ASVS, and NIST SSDF compliance mapping
- [ ] Secure change management and refactoring validation

---

## Z. Final Verification
- [ ] Full application runs locally and in containers
- [ ] Complete student, faculty, and admin user journeys verified
- [ ] All security exploits verified blocked
- [ ] 100% automated tests passing
- [ ] Documentation and diagrams perfectly match implementation
- [ ] Quality gate passed


