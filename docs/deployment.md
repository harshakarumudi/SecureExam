# SecureExam — Containerized CI/CD & Deployment Architecture

## 1. Overview & Objectives

In accordance with **CO3, CO4, and DevSecOps principles**, SecureExam implements automated, continuous container building, image publishing, and deployment verification pipelines powered by **GitHub Actions** and **GitHub Container Registry (GHCR)**.

---

## 2. GitHub Workflows Architecture

The repository incorporates two complementary workflows:

1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - Triggers on `push` and `pull_request` to `main`.
   - Executes Ruff AST code linting and TypeScript builds.
   - Performs dependency security scans via `pip-audit` and `npm audit`.
   - Runs automated Pytest suite (30 tests) and verifies test coverage.
   - Validates container builds across all stages.

2. **Continuous Deployment (`.github/workflows/deploy.yml`)**:
   - Triggers on `push` to `main` and on-demand via `workflow_dispatch`.
   - Packages multi-stage hardened production container images.
   - Authenticates to **GitHub Container Registry (GHCR)** (`ghcr.io`) using `GITHUB_TOKEN`.
   - Tags images with `latest` and commit SHA (`${{ github.sha }}`).
   - Deploys container ecosystem (`postgres`, `backend`, `frontend`) using `docker compose`.
   - Executes dynamic HTTP health probes against live endpoints (`/api/v1/health` and `/healthz`).
   - Verifies zero-downtime application startup.

---

## 3. Published Container Images (GHCR)

| Image | Registry Target | Base Image | Security Hardening |
| :--- | :--- | :--- | :--- |
| **Backend API** | `ghcr.io/<owner>/<repo>/backend:latest` | `python:3.13-slim` | Non-root `appuser` (UID 10001), stripped build tools |
| **Frontend UI** | `ghcr.io/<owner>/<repo>/frontend:latest` | `nginx:alpine` | Non-root `nginx` user, static bundle only |

---

## 4. Connecting Your Local Repository to GitHub

To activate the GitHub deployment workflows, link your local repository to your GitHub account:

### Step 1: Create a New Repository on GitHub
1. Go to [https://github.com/new](https://github.com/new).
2. Enter repository name: `SecureExam` (or `secureexam`).
3. Set visibility to **Public** (or **Private**).
4. Do **not** initialize with README or .gitignore (the local repository already contains everything).
5. Click **Create repository**.

### Step 2: Push Local Code to GitHub
In your PowerShell terminal inside `C:\Users\Harsha\.gemini\antigravity\scratch\secureexam`:

```powershell
# Set origin URL to your GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/SecureExam.git

# Ensure default branch is main
git branch -M main

# Push all commits, tags, and workflows
git push -u origin main
```

---

## 5. Automated Pipeline Execution

Once pushed, GitHub Actions immediately kicks off the pipeline:
1. Navigate to the **Actions** tab on your GitHub repository.
2. You will observe both workflows running:
   - **SecureExam DevSecOps Pipeline**: Linting, auditing, and testing.
   - **SecureExam Container Deployment (CD)**: Building, pushing to GHCR, and verifying live container health.
3. Once completed:
   - Under **Packages** on your GitHub repository page, you will see the published `backend` and `frontend` Docker images.
   - Under **Deployments**, you will see the green **production** deployment status.

---

## 6. Manual Triggering (Workflow Dispatch)

You can also trigger a deployment manually at any time without creating a new commit:
1. In your GitHub repository, click **Actions**.
2. Select **SecureExam Container Deployment (CD)** from the left sidebar.
3. Click the **Run workflow** dropdown button.
4. Select `Branch: main` and click **Run workflow**.
