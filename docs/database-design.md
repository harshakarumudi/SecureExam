# SecureExam — Database Schema Design and Relational Specification

## Document Information
- **Project**: SecureExam — Secure Online Examination Management System
- **Institution**: Amrita School of Computing
- **Course**: Secure Software Engineering
- **Version**: 1.0.0
- **Status**: Baselined (Milestone 4)
- **Target Course Outcomes**: CO1 (Secure System Models), CO3 (Containerized Deployment)

---

## 1. Overview and Relational Philosophy

The SecureExam persistence layer is designed to enforce **Data Integrity, Least Privilege, Confidentiality, and Non-Repudiation** directly at the database engine level.

### Key Database Design Principles:
1. **Strict Referential Integrity**: All relationships utilize explicit foreign key constraints with appropriate cascade behaviors (`CASCADE` for dependent components, `SET NULL` for optional references).
2. **Authoritative Temporal Control**: Attempt expiration deadlines (`expires_at`) are indexed and evaluated natively, eliminating race conditions or client manipulation.
3. **Sealed Integrity for Academic Records**: The `results` table enforces a unique 1:1 constraint with `exam_attempts` and contains no modification endpoints, rendering generated scores immutable.
4. **Append-Only Auditing**: The `audit_logs` table contains zero foreign key constraints to prevent cascade deletions from destroying historical forensics.

---

## 2. Table Specifications and DDL Mapping

### 2.1 Table: `users`
Stores user identities, credentials, and role assignments.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Normalized login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Salted Argon2id password hash |
| `full_name` | VARCHAR(255) | NOT NULL | Candidate or faculty full name |
| `role` | VARCHAR(50) | NOT NULL, INDEXED | `STUDENT`, `FACULTY`, `ADMIN` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account lock/activation flag |
| `created_at` | TIMESTAMPTZ | NOT NULL | Registration timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last modification timestamp |

### 2.2 Table: `exams`
Stores examination configurations authored by faculty.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique examination identifier |
| `title` | VARCHAR(255) | NOT NULL, INDEXED | Examination title |
| `description` | TEXT | NULLABLE | Detailed instructions & syllabus |
| `duration_minutes`| INTEGER | NOT NULL | Official duration limit |
| `total_marks` | FLOAT | NOT NULL, DEFAULT 100.0 | Maximum score possible |
| `passing_marks` | FLOAT | NOT NULL, DEFAULT 40.0 | Minimum threshold to pass |
| `status` | VARCHAR(50) | NOT NULL, INDEXED | `DRAFT`, `PUBLISHED`, `CLOSED` |
| `created_by` | INTEGER | NOT NULL, FK(`users.id`), INDEXED | Owning faculty member ID |
| `start_time` | TIMESTAMPTZ | NULLABLE | Exam opening window |
| `end_time` | TIMESTAMPTZ | NULLABLE | Exam closing window |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Modification timestamp |

### 2.3 Table: `questions`
Stores individual questions belonging to an examination.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique question identifier |
| `exam_id` | INTEGER | NOT NULL, FK(`exams.id`), INDEXED | Parent examination ID |
| `question_text` | TEXT | NOT NULL | Sanitized prompt text |
| `marks` | FLOAT | NOT NULL, DEFAULT 1.0 | Positive marks awarded |
| `negative_marks`| FLOAT | NOT NULL, DEFAULT 0.0 | Penalty for incorrect choice |
| `explanation` | TEXT | NULLABLE | Pedagogical explanation |
| `order_index` | INTEGER | NOT NULL, DEFAULT 0 | Display sequence order |

### 2.4 Table: `question_options`
Stores choices/alternatives for Multiple Choice Questions.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique choice identifier |
| `question_id` | INTEGER | NOT NULL, FK(`questions.id`), INDEXED | Parent question ID |
| `option_text` | TEXT | NOT NULL | Sanitized choice text |
| `is_correct` | BOOLEAN | NOT NULL, DEFAULT FALSE | Correctness indicator (Confidential) |
| `order_index` | INTEGER | NOT NULL, DEFAULT 0 | Display sequence order |

### 2.5 Table: `exam_attempts`
Authoritative session records for student examinations.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique attempt identifier |
| `student_id` | INTEGER | NOT NULL, FK(`users.id`), INDEXED | Candidate taking the exam |
| `exam_id` | INTEGER | NOT NULL, FK(`exams.id`), INDEXED | Examination being attempted |
| `started_at` | TIMESTAMPTZ | NOT NULL | Server authoritative start time |
| `expires_at` | TIMESTAMPTZ | NOT NULL, INDEXED | Authoritative hard deadline |
| `submitted_at` | TIMESTAMPTZ | NULLABLE | Timestamp of submission |
| `status` | VARCHAR(50) | NOT NULL, INDEXED | `IN_PROGRESS`, `SUBMITTED`, `EXPIRED` |

### 2.6 Table: `student_answers`
Granular selections submitted by students during active attempts.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique answer record |
| `attempt_id` | INTEGER | NOT NULL, FK(`exam_attempts.id`), INDEXED | Target attempt session |
| `question_id` | INTEGER | NOT NULL, FK(`questions.id`), INDEXED | Question answered |
| `selected_option_id`| INTEGER | NULLABLE, FK(`question_options.id`) | Selected option ID |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | Server recording timestamp |

### 2.7 Table: `results`
Sealed academic performance reports computed authoritatively by `EvaluationService`.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique result identifier |
| `attempt_id` | INTEGER | UNIQUE, NOT NULL, FK(`exam_attempts.id`) | 1:1 Reference to attempt |
| `student_id` | INTEGER | NOT NULL, FK(`users.id`), INDEXED | Candidate recipient |
| `exam_id` | INTEGER | NOT NULL, FK(`exams.id`), INDEXED | Examination evaluated |
| `total_score` | FLOAT | NOT NULL | Computed points |
| `max_score` | FLOAT | NOT NULL | Total possible exam points |
| `percentage` | FLOAT | NOT NULL | Percentage achieved |
| `passed` | BOOLEAN | NOT NULL | Binary passing status |
| `evaluated_at` | TIMESTAMPTZ | NOT NULL | Evaluation timestamp |

### 2.8 Table: `audit_logs`
Immutable, tamper-evident security audit trails.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique log entry ID |
| `timestamp` | TIMESTAMPTZ | NOT NULL, INDEXED | Exact UTC time of event |
| `actor_id` | INTEGER | NULLABLE, INDEXED | Authenticated user ID (if present) |
| `actor_role` | VARCHAR(50) | NULLABLE, INDEXED | Role of user at invocation |
| `action` | VARCHAR(100) | NOT NULL, INDEXED | Security action name |
| `resource_id` | VARCHAR(100) | NULLABLE, INDEXED | Identifier of affected entity |
| `ip_address` | VARCHAR(50) | NULLABLE | Remote client IP address |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT "SUCCESS"| `SUCCESS`, `FAILURE`, `BLOCKED` |
| `details` | TEXT | NULLABLE | Non-credential event context |

---

## 3. Database Security Controls

1. **SQL Injection Defense**: Every table is accessed via SQLAlchemy 2.0 ORM query builders using parameterized SQL. Direct SQL string concatenation is forbidden.
2. **Credential Confidentiality**: Passwords are saved strictly as salted Argon2id hashes with 19 MiB memory cost. Plaintext passwords never persist.
3. **Confidentiality of Question Keys**: The `is_correct` field in `question_options` is excluded from all student-facing serialization schemas.
4. **Authoritative Expiration Enforcement**: Database queries filtering active attempts check `expires_at > NOW()`, ensuring expired attempts cannot receive further answer updates.
5. **Database User Least Privilege**: Production PostgreSQL runs with a dedicated user (`secureexam_user`) granted privileges only to `secureexam_db`. Superuser rights are revoked.
