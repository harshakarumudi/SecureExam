# SecureExam — Security Governance, Policies & Incident Response Plan

## 1. Security Governance Framework
Security governance in SecureExam ensures that institutional assessment integrity, candidate privacy, and software security are systematically managed and maintained throughout the application lifecycle.

### 1.1 Stakeholder Roles & Responsibilities
| Role | Primary Responsibilities | Separation of Duty Boundary |
| :--- | :--- | :--- |
| **System Administrator** | User account lifecycle, role assignment, system health monitoring, audit log review. | Cannot author examination questions or take active student exams. |
| **Faculty / Examiner** | Exam definition, question authoring, grade inspection for owned exams. | Cannot modify other faculty members' exams or alter student identity records. |
| **Student / Candidate** | Exam enrollment, question response submission, personal result viewing. | Read-only access to published exams; zero access to answer keys or peer records. |
| **DevSecOps Engineer** | Pipeline maintenance, dependency scanning, container hardening, SonarQube quality gate enforcement. | Production secrets managed via environment variables; zero hardcoded credentials. |

---

## 2. Core Security Policies

### 2.1 Least Privilege & Access Control Policy
- All users authenticate via unique credentials. Sharing of faculty or administrative credentials is strictly prohibited.
- Role-based authorization (`require_role`) is enforced on 100% of non-public API endpoints.
- Object-level ownership (e.g., `exam.created_by == current_user.id`, `attempt.student_id == current_user.id`) is verified on every single read, update, and delete operation.

### 2.2 Secure Coding & Code Review Policy
- All code committed to the repository must pass automated Ruff AST linting and Pytest unit and security suites.
- Direct raw SQL queries are strictly prohibited; all queries must utilize SQLAlchemy ORM.
- All user-supplied HTML content must pass Bleach whitelist sanitization prior to persistence.
- Any change affecting scoring algorithms or authentication requires dual-peer code review and approval.

### 2.3 Vulnerability Management & Patching Policy
- Automated dependency scanning runs on every push and pull request via GitHub Actions.
- Any dependency discovered with a Critical or High CVSS vulnerability must be remediated or patched within 48 hours.
- Base container images (Alpine, Debian Slim) must be rebuilt weekly with upstream security patches.

---

## 3. Security Incident Response Plan (SIRP)

In the event of an alleged security breach, exam tampering, or system compromise, the following five-stage incident response procedure is activated:

```
[ 1. Identification ] ──► Automated Audit Alert (e.g., repeated 403s, expired submission spikes)
           │
[ 2. Containment    ] ──► Immediate Token Invalidation, Account Deactivation via Admin API
           │
[ 3. Eradication    ] ──► Root Cause Vulnerability Remediation, Hotfix Deployment
           │
[ 4. Recovery       ] ──► Verification of Database State, Restore from Sealed Audit Logs
           │
[ 5. Post-Mortem    ] ──► Formal Incident Report, STRIDE Model Update, Policy Revision
```

### Incident Severity Levels
- **P1 (Critical)**: Question bank compromise prior to exam commencement, score ledger tampering. (Action: Immediate exam halt, emergency token revocation).
- **P2 (High)**: Cross-student result disclosure (BOLA/IDOR), repeated administrative login brute-force. (Action: Rate-limiter block, IP ban, forensic audit inspection).
- **P3 (Medium)**: Non-exploitable transitive dependency advisory, minor denial-of-service attempt. (Action: Normal sprint patch cycle).

---

## 4. Audit Log Retention & Compliance
- All sensitive operations (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `EXAM_CREATED`, `ATTEMPT_STARTED`, `EVALUATION_COMPLETED`, `ATTEMPT_EXPIRED_REJECTED`) are persisted to `audit_logs`.
- Logs include: `timestamp`, `actor_id`, `actor_role`, `action`, `resource_id`, `status`, `ip_address`, `details`.
- Audit logs are append-only. No API endpoint exists to update or delete audit log entries.