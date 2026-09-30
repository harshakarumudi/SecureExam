# SecureExam — Container Security & Hardening Architecture

## 1. Overview & Security Principles
Containerization provides reproducible, isolated runtime environments for SecureExam components. In alignment with **CO2, CO3, and CO4**, the container architecture is engineered using defense-in-depth security principles:
1. **Least Privilege**: Zero container runs as root.
2. **Attack Surface Minimization**: Multi-stage builds strip compilers, dev-dependencies, and unnecessary binaries from final images.
3. **Network Isolation**: Strict internal Docker network segmentation preventing public exposure of persistent databases.
4. **Health & Liveness Telemetry**: Automated healthchecks verify application status.

---

## 2. Multi-Stage Build Strategy

### 2.1 Backend Container (`backend/Dockerfile`)
The backend container is structured into two distinct stages:
- **Stage 1 (`builder`)**: Uses `python:3.13-slim` with build dependencies (`build-essential`) to compile native C extensions (e.g., Argon2, Psycopg). Packages are installed to a user-local directory (`/root/.local`).
- **Stage 2 (`runner`)**: Uses clean `python:3.13-slim` without compilers or build utilities. Only the precompiled wheels and Python bytecode are copied over (`/home/appuser/.local`).
- **Non-Root Execution**:
  - Dedicated system user and group created: `appgroup` (GID 10001), `appuser` (UID 10001).
  - Explicit file ownership (`chown -R appuser:appgroup /home/appuser`).
  - Read-execute permissions (`chmod -R 750 /app`).
  - Runtime directive: `USER appuser`.

### 2.2 Frontend Container (`frontend/Dockerfile`)
- **Stage 1 (`builder`)**: Uses `node:20-alpine` to install NPM dependencies and compile TypeScript/React assets into minified production bundles (`/dist`).
- **Stage 2 (`runner`)**: Uses `nginx:alpine`. Zero Node.js runtime, NPM tooling, or TypeScript source code is packaged into the production container.
- **Non-Root Execution**: Operates under standard unprivileged `nginx` user (`USER nginx`) on port 80.

---

## 3. Network Segmentation & Database Isolation

The Docker Compose configuration enforces dual-tier network segmentation:

```
[ Public Traffic / Browser ]
           │
           ▼ (Port 80)
   ┌───────────────┐
   │   Frontend    │
   │ (NGINX Proxy) │
   └───────┬───────┘
           │
           │ (app-net: Bridge Network)
           ▼
   ┌───────────────┐
   │    Backend    │
   │  (FastAPI)    │
   └───────┬───────┘
           │
           │ (db-net: Internal Isolated Network, no host bridge)
           ▼
   ┌───────────────┐
   │  PostgreSQL   │
   │  (Relational) │
   └───────────────┘
```

- **`app-net`**: Connects the reverse proxy frontend to the API backend.
- **`db-net`**: Configured with `internal: true`. PostgreSQL port 5432 is **never** bound to the host network interface (`0.0.0.0:5432`), preventing external port scanning, direct database brute-force, or unauthorized network queries. Only the backend container can reach PostgreSQL.

---

## 4. Container Healthchecks & Liveness Probes
- **PostgreSQL**: Periodically verifies engine readiness via `pg_isready -U secureuser -d secureexam`.
- **Backend API**: Executes lightweight Python HTTP probe to `/api/v1/health` every 15 seconds.
- **Frontend NGINX**: Queries `/healthz` returning HTTP 200 every 15 seconds.
- Dependent startup (`depends_on` with `condition: service_healthy`) guarantees deterministic service initialization order.