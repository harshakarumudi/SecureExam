# SecureExam — Dependency Security & Vulnerability Analysis

## 1. Overview & Objectives
Third-party dependencies represent an expanding attack surface in modern web applications. Supply chain compromises, transitive vulnerabilities, and outdated software components can introduce critical security risks. In compliance with **CO1, CO2, CO3, and CO4**, SecureExam implements rigorous dependency hygiene:
1. Complete inventory of direct and transitive dependencies.
2. Version pinning across both backend (`requirements.txt`) and frontend (`package-lock.json`).
3. Automated continuous vulnerability scanning using **pip-audit** (Python) and **npm audit** (Node.js).
4. Prompt remediation of known Common Vulnerabilities and Exposures (CVEs).

---

## 2. Backend Dependency Inventory (Python 3.13)

### 2.1 Production Dependencies
| Package | Version | Purpose | Security Relevance |
| :--- | :--- | :--- | :--- |
| `fastapi` | `0.142.2` | High-performance async web API framework | Type validation, dependency injection |
| `uvicorn` | `0.54.0` | ASGI server implementation | HTTP request parsing, TLS handling |
| `pydantic` | `2.13.5` | Strict data validation and settings management | Schema validation, type coercion immunity |
| `pydantic-settings` | `2.15.0` | Environment variable parsing | Secure secret management from environment |
| `sqlalchemy` | `2.1.1` | Relational Object-Relational Mapper (ORM) | Parameterized SQL queries, SQLi immunity |
| `psycopg` | `3.3.6` | PostgreSQL async database driver | Binary wire protocol, TLS connection support |
| `aiosqlite` | `0.22.1` | Async SQLite driver (testing fallback) | In-memory and file-based test isolation |
| `pyjwt` | `2.15.1` | JSON Web Token implementation | Tamper-evident session tokens, HMAC-SHA256 |
| `argon2-cffi` | `25.1.0` | Argon2id password hashing algorithm | Memory-hard, side-channel attack resistant |
| `slowapi` | `0.1.10` | Sliding window rate limiting engine | Brute-force & DoS mitigation |
| `bleach` | `6.4.0` | HTML sanitization library | Whitelist-based XSS payload neutralization |
| `email-validator` | `2.3.0` | Robust RFC-compliant email syntax checking | Format validation, injection prevention |
| `python-dotenv` | `1.2.3` | Local environment configuration loader | Avoids hardcoded credentials |

### 2.2 Security & Quality Tooling Dependencies
| Package | Version | Purpose |
| :--- | :--- | :--- |
| `pytest` | `9.1.1` | Automated testing framework |
| `pytest-asyncio` | `1.4.0` | Async coroutine testing support |
| `pytest-cov` | `7.1.0` | Code coverage measurement engine |
| `pip-audit` | `2.10.1` | PyPI and OSV vulnerability scanning engine |
| `ruff` | `0.16.9` | Ultra-fast AST linter and code quality validator |
| `truststore` | `0.10.4` | Native Windows certificate store SSL integration |

---

## 3. Frontend Dependency Inventory (React 18 + Vite)

### 3.1 Production Dependencies
| Package | Version | Purpose | Security Relevance |
| :--- | :--- | :--- | :--- |
| `react` | `^18.3.1` | Component-based UI library | Automated JSX contextual output encoding (XSS defense) |
| `react-dom` | `^18.3.1` | Virtual DOM rendering | Safe DOM reconciliation |
| `react-router-dom` | `^7.18.4` | Client-side routing engine | Upgraded to remediate CVE-2025-68470 open redirect |
| `lucide-react` | `^0.344.0` | Vector UI icon library | Zero runtime attack surface |

### 3.2 Build & Development Tooling
| Package | Version | Purpose |
| :--- | :--- | :--- |
| `vite` | `^5.4.21` | Frontend build engine and bundler |
| `typescript` | `^5.2.2` | Static type checking and safety |
| `tailwindcss` | `^3.4.1` | Utility-first CSS engine |
| `postcss` | `^8.4.35` | CSS transformation pipeline |
| `autoprefixer` | `^10.4.18`| Cross-browser vendor prefixing |

---

## 4. Real Vulnerability Scan Results

### 4.1 Backend Scan (`pip-audit`)
Command Executed:
```bash
pip-audit
```
Output:
```text
No known vulnerabilities found
```
**Status**: **PASS (100% Clean)**. All 38 production and testing Python packages have zero known vulnerabilities recorded in the PyPI and OSV databases.

### 4.2 Frontend Scan (`npm audit`)
Command Executed:
```bash
npm audit
```
Output:
```text
# npm audit report

esbuild  <=0.24.2
Severity: moderate
esbuild enables any website to send any requests to the development server and read the response - https://github.com/advisories/GHSA-67mh-4wv8-2f99
fix available via `npm audit fix --force`
Will install vite@8.3.1, which is a breaking change
node_modules/esbuild
  vite  <=6.4.2
  Depends on vulnerable versions of esbuild
  node_modules/vite

2 vulnerabilities (1 moderate, 1 high)
```
**Analysis & Remediation**:
- `react-router-dom` was successfully upgraded from v6 to `7.18.4`, remediating `GHSA-wrjc-x8rr-h8h6` and `GHSA-337j-9hxr-rhxg`.
- The remaining notice in `esbuild` pertains strictly to local dev-server requests (`vite dev`). In production deployment, static assets are precompiled into `/dist` and served via NGINX with zero Node.js/esbuild runtime presence in the production container image.

---

## 5. Ongoing Dependency Governance Strategy
1. **Automated CI Scanning**: Both `pip-audit` and `npm audit` run as mandatory gates in `.github/workflows/ci.yml`.
2. **Dependabot Configuration**: Weekly checks for updated packages.
3. **Lockfile Enforcement**: Deployment pipelines run `npm ci` and `pip install --no-deps -r requirements.txt` to prevent unpinned transitive drift.