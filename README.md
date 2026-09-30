# SecureExam — Secure Online Examination Management System

[![Tests: 28 Passing](https://img.shields.io/badge/Tests-28%20Passing-brightgreen.svg)]()
[![Code Coverage: 71.2%](https://img.shields.io/badge/Coverage-71.2%25-green.svg)]()
[![Quality Gate: Passed](https://img.shields.io/badge/SonarQube-Gate%20Passed-brightgreen.svg)]()
[![Known Vulnerabilities: 0](https://img.shields.io/badge/Vulnerabilities-0%20(Clean)-success.svg)]()
[![Python: 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)]()
[![React: 18](https://img.shields.io/badge/React-18-cyan.svg)]()

> **Academic Project**  
> **Institution**: Amrita School of Computing — Department of Computer Science & Engineering  
> **Course**: Secure Software Engineering (SSE)  
> **Outcomes Satisfied**: CO1 (Secure Modeling), CO2 (Threat Modeling), CO3 (Defensive Coding), CO4 (Security Testing & DevSecOps)  

---

## 1. Project Overview
**SecureExam** is a secure, full-stack, enterprise-grade online examination management platform engineered to prevent examination fraud, cheating, and tampering. The platform replaces vulnerable client-centric designs with a zero-trust, server-authoritative architecture where all timers, answer keys, scoring algorithms, and role boundaries are enforced exclusively on the backend.

### Key Security Capabilities
- **Server-Authoritative Timer**: Exam deadlines are tracked immutably in the database. Submissions beyond a 15-second network latency grace period are automatically marked `EXPIRED` and rejected.
- **Server-Side-Only Grading Engine**: The client transmits only selected option IDs. Scoring logic (positive marking or negative marking) executes 100% on the server against verified database keys.
- **Confidential Question Banking**: Student test sessions receive sanitized question schemas (`QuestionCandidateOut`) with `is_correct` and faculty explanations stripped.
- **Memory-Hard Cryptography**: Passwords are protected using **Argon2id** (`m=19MB, t=2, p=1`) with constant-time verification against user enumeration.
- **Broken Object-Level Authorization (IDOR/BOLA) Defense**: Enforced row-level ownership checks prevent students or faculty from accessing peer examinations or results.
- **Strategy Pattern Scoring (CR-2026-004)**: Supports both Standard positive-only marking and configurable **Negative Marking** with underflow floor protection (`max(0.0, score)`).
- **Hardened DevSecOps**: Multi-stage non-root Docker containers (`appuser` UID 10001, `nginx`), isolated internal database network (`db-net`), and automated CI/CD security audits.

---

## 2. Technology Stack

| Layer | Technologies | Security Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React | Contextual JSX auto-escaping (XSS defense), strict static types |
| **Backend API** | Python 3.13, FastAPI, Pydantic v2, SlowAPI, Bleach | Declarative schema validation, sliding-window rate limiting |
| **Persistence** | PostgreSQL 16 (Production) / SQLite Async (Testing), SQLAlchemy 2.0 ORM | Parameterized query statements (100% SQLi immunity) |
| **Cryptography** | Argon2id (`argon2-cffi`), PyJWT (`HS256`) | Memory-hard hashing, tamper-evident session signatures |
| **Containerization**| Docker, Docker Compose, NGINX Alpine | Non-root runtime, isolated bridge networks |
| **DevSecOps** | Pytest, pytest-cov, Ruff AST Linter, pip-audit, npm audit, GitHub Actions | Continuous static and dynamic verification |

---

## 3. Seeded Accounts & Credentials

The system initializes with three default accounts for immediate role testing:

| Role | Email Address | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@secureexam.edu` | `Admin@123456` | Full platform oversight, audit log streams, user activation/roles |
| **Faculty Member** | `faculty@secureexam.edu` | `Faculty@123456` | Create/edit owned exams, question banking, view candidate results |
| **Student** | `student@secureexam.edu` | `Student@123456` | Discover published exams, take timed attempts, view personal results |

---

## 4. Quickstart Guide

### 4.1 Running with Docker Compose (Recommended)
Launch the entire containerized architecture (Frontend, Backend, and PostgreSQL) with one command:
```bash
docker compose up --build
```
- **Web Application UI**: `http://localhost` (or `http://localhost:80`)
- **API Swagger Documentation**: `http://localhost/api/docs`
- **Backend Health Check**: `http://localhost/api/v1/health`

### 4.2 Running Locally for Development

#### Backend Setup
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate     # Linux / macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run database initializer and seed script
python -m backend.app.db.init_db

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access the application at `http://localhost:5173`.

---

## 5. Verification & Testing Commands

### Run Full Pytest Suite (28 Tests + Coverage)
```bash
$env:PYTHONPATH="."; .\venv\Scripts\pytest tests/ -v --cov=backend.app --cov-report=term-missing
```
*Current Result*: **28 Passed in 2.60s (71.2% Code Coverage)**.

### Run AST Linting (Ruff)
```bash
.\venv\Scripts\ruff check backend/app tests/
```
*Current Result*: **All checks passed! (0 errors)**.

### Run Dependency Vulnerability Scans
```bash
# Backend scan
python -c "import truststore; truststore.inject_into_ssl(); from pip_audit._cli import audit; import sys; sys.argv=['pip-audit']; sys.exit(audit())"
# Frontend scan
cd frontend && npm audit
```
*Current Result*: **0 Known Vulnerabilities**.

---

## 6. Project Documentation Sitemap

All formal engineering specifications, models, and academic reports are preserved in `docs/` and `diagrams/`:

| Document | Description |
| :--- | :--- |
| [`docs/final-report.md`](docs/final-report.md) | Master 41-section Academic Project Report |
| [`docs/co-mapping.md`](docs/co-mapping.md) | Comprehensive Course Outcomes (CO1–CO4) Evidence Matrix |
| [`docs/threat-model.md`](docs/threat-model.md) | Formal STRIDE Threat Model & 12 Threat Scenarios Register |
| [`docs/requirements.md`](docs/requirements.md) | Software Requirements Specification (SRS) with testable SEC-REQs |
| [`docs/architecture.md`](docs/architecture.md) | 7-Tier System Architecture & Trust Boundary Specification |
| [`docs/use-cases.md`](docs/use-cases.md) | 25 Detailed Use Case Specifications across Actors |
| [`docs/database-design.md`](docs/database-design.md) | Relational Database Schema & Constraint Definitions |
| [`docs/client-change-request.md`](docs/client-change-request.md) | Change Request CR-2026-004 (Negative Marking) Specification |
| [`docs/code-smells-and-refactoring.md`](docs/code-smells-and-refactoring.md) | Strategy Pattern Refactoring & Complexity Analysis |
| [`docs/sonarqube.md`](docs/sonarqube.md) | SonarQube SAST Profile & Quality Gate Thresholds |
| [`docs/dependency-security.md`](docs/dependency-security.md) | Direct & Transitive Dependency Inventory & Audit Logs |
| [`docs/container-security.md`](docs/container-security.md) | Non-root Multi-stage Docker Hardening Architecture |
| [`docs/secure-sdlc.md`](docs/secure-sdlc.md) | S-SDLC Framework Alignment across Development Phases |
| [`docs/security-economics.md`](docs/security-economics.md) | Gordon-Loeb Cost-Benefit & ROSI Trade-Off Analysis |
| [`docs/governance.md`](docs/governance.md) | Security Governance, Policies & Incident Response Plan |
| [`docs/risk-register.md`](docs/risk-register.md) | 15+ Enterprise Risks Matrix & Residual Risk Posture |
| [`docs/compliance-mapping.md`](docs/compliance-mapping.md) | OWASP Top 10, ASVS v4.0, and NIST SSDF Traceability |

---

## 7. License & Academic Attribution
Developed for academic assessment at **Amrita School of Computing, Amrita Vishwa Vidyapeetham**.  
Authorized strictly for educational, evaluation, and research purposes.