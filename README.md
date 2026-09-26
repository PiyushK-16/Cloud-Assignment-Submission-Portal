# Cloud-Based Student Assignment Submission & Feedback Portal

> Cloud-based student assignment submission and feedback platform featuring role-based authentication, cloud database integration, object storage, assignment management, secure file submission, grading, and feedback workflows.

![CI](https://github.com/PiyushK-16/Cloud-Based-Assignment-Submission-Portal/actions/workflows/ci.yml/badge.svg)

## Overview
Teachers publish assignments with deadlines; students upload their work from anywhere; teachers review, grade and leave feedback; students see marks and feedback. Files live in **private cloud object storage**, metadata lives in a **managed relational cloud database**, and access is controlled by **JWT authentication + role-based authorization**. The same code runs 100% locally (SQLite + local folder) or in the cloud (PostgreSQL + S3-compatible bucket) by changing environment variables only.

## Problem Statement
Emailing/WhatsApp-ing assignments causes lost files, unclear deadlines, no audit trail and scattered feedback. A centralized, cloud-hosted portal removes those problems.

## Objectives
1. Build a cloud-hosted full-stack app. 2. Separate metadata (DB) from files (object storage). 3. Enforce RBAC. 4. Implement deadline/late logic on the server. 5. Provide grading + feedback. 6. Show security, scalability, failure handling, testing and CI.

## Features
- **Students:** register/login, enroll in courses, view assignments & deadlines, upload/resubmit (where allowed), see status (NOT_SUBMITTED / SUBMITTED / LATE / GRADED), marks, feedback, download own files, dashboard.
- **Teachers:** create courses, create/update/delete assignments (deadline, max marks, allowed file types, max size, late & resubmission policy), view/download submissions, grade with feedback, dashboard statistics.
- **Platform:** bcrypt passwords, JWT with server-side logout revocation, magic-byte file validation, private files, audit logs, rate limiting, CORS allow-list, idempotent uploads, graceful 503s, CI pipeline.

## User Roles
| Capability | Student | Teacher | Admin |
|---|---|---|---|
| Register / login | Yes | Yes (invite code) | Seeded |
| View assignments | Enrolled courses | Own courses | All |
| Create / edit / delete assignment | No | Own courses | Yes |
| Upload / resubmit | Yes | No | No |
| View / download submission | Own only | Own courses | Yes |
| Grade + feedback | No | Own courses | Yes |
| View own marks & feedback | Yes | - | - |

## Cloud Computing Concepts
SaaS (portal for end users), PaaS (Render/Vercel/Supabase hosting), IaaS (S3/VM-level building blocks), managed cloud database, object storage, authN/authZ + RBAC, REST APIs, client-server, serverless-ready design, scalability/elasticity, availability, load balancing/CDN/API-gateway mapping, environment variables & secrets, logging/monitoring, backup, CI/CD. Full mapping ("where in this project") is in [`docs/02-cloud-concepts.md`](docs/02-cloud-concepts.md).

## Architecture
```
Student / Teacher -> React SPA (CDN-hosted) -> REST API (FastAPI, JWT) -+-> Cloud DB (PostgreSQL / SQLite)
                                                                         +-> Object Storage (S3-compatible / local)
                                                                         +-> Logs / Monitoring
```
Details and the advanced (CDN + API Gateway + serverless) diagram: [`docs/06-architecture.md`](docs/06-architecture.md).

## Technology Stack
React 18 + Vite + React Router | Python FastAPI + SQLAlchemy | PyJWT + bcrypt | SQLite -> PostgreSQL | Local FS -> S3-compatible storage (boto3) | pytest | GitHub Actions | Docker.

## Database Design
Tables: `users`, `courses`, `enrollments`, `assignments`, `submissions`, `revoked_tokens`. Teacher -> Course -> Assignment -> Submission <- Student. See [`docs/04-database-storage-design.md`](docs/04-database-storage-design.md).

## Cloud Storage
Key layout: `assignments/<assignment_id>/<student_id>/<uuid>_<safe_filename>`. Buckets are private; downloads pass an authorization check first (or use short-lived signed URLs on S3).

## Authentication & Authorization
Login returns a signed JWT (`sub`, `role`, `jti`, `exp`). Every protected route uses `require_role(...)`; resource-level checks (own submission / own course) live in the service layer. Logout stores the token `jti` in a blacklist.

## Assignment Workflow
Teacher creates course -> creates assignment (validated) -> row saved in DB -> enrolled students see it on their dashboard.

## Submission Workflow
Select assignment -> select file -> validate (auth, enrollment, deadline policy, extension, size, magic bytes, duplicates) -> upload to storage -> save metadata (compensating delete if DB fails) -> confirmation with status.

## Feedback & Grading
Teacher opens submission -> downloads file -> enters marks (<= max) + feedback -> status becomes GRADED -> student sees both. Students can never write marks/feedback.

## REST APIs
| Method | Endpoint | Who |
|---|---|---|
| POST | /api/register, /api/login | public |
| POST | /api/logout, GET /api/me | any logged-in |
| POST/GET | /api/courses, POST /api/courses/{id}/enroll | teacher / any / student |
| POST/GET | /api/assignments | teacher / any |
| GET/PUT/DELETE | /api/assignments/{id} | any / teacher / teacher |
| POST | /api/assignments/{id}/submit | student |
| GET | /api/assignments/{id}/submissions | teacher |
| GET | /api/submissions/me | student |
| GET | /api/submissions/{id} | owner or course teacher |
| POST | /api/submissions/{id}/grade | course teacher |
| GET | /api/submissions/{id}/feedback | owner or course teacher |
| GET | /api/submissions/{id}/download (`/download-url` on S3) | owner or course teacher |
| GET | /api/dashboard/student, /api/dashboard/teacher | role-specific |
| GET | /api/health | public |

Interactive docs: `http://localhost:8000/docs`. Full reference: [`docs/05-api-and-security-design.md`](docs/05-api-and-security-design.md).

## Folder Structure
```
Cloud-Assignment-Submission-Portal/
├── frontend/ (src/components, pages, services, utils)
├── backend/  (app.py, config.py, routes/, models/, services/, middleware/, utils/)
├── cloud/    (database_service.py, storage_service.py, auth_service.py)
├── tests/  sample_files/  screenshots/  docs/  reports/
├── .github/workflows/ci.yml  Dockerfile
└── README.md  requirements.txt  .env.example  .gitignore
```

## Installation
Prerequisites: Python 3.11+, Node.js 18+, Git.

```bash
git clone https://github.com/<your-username>/Cloud-Based-Assignment-Submission-Portal.git
cd Cloud-Based-Assignment-Submission-Portal
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Environment Variables
Copy `.env.example` to `.env` (backend, project root) and `frontend/.env.example` to `frontend/.env`. Generate a secret:
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.

| Variable | Purpose |
|---|---|
| JWT_SECRET | signs tokens (required, keep secret) |
| TEACHER_INVITE_CODE | code needed to register as teacher |
| DATABASE_URL | `sqlite:///./portal.db` or a PostgreSQL URL |
| STORAGE_BACKEND | `local` or `s3` |
| S3_BUCKET / S3_REGION / S3_ENDPOINT_URL / S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY | S3-compatible storage |
| CORS_ORIGINS | allowed frontend origins |
| RATE_LIMIT_LOGIN_PER_MIN | login/register throttle |

## Local Setup / Running the Application
```bash
# terminal 1 (project root, venv active)
python -m backend.utils.seed_data          # optional dummy data
uvicorn backend.app:app --reload           # http://localhost:8000/docs

# terminal 2
cd frontend && npm run dev                 # http://localhost:5173
```
Demo accounts after seeding (password `Demo@12345`): `teacher@demo.edu`, `asha@demo.edu`, `ravi@demo.edu`, `meera@demo.edu`. Step-by-step walkthrough: [`docs/07-local-setup.md`](docs/07-local-setup.md).

## Testing
```bash
pytest          # 19 automated backend tests covering the 25-case matrix
```
Test matrix: [`docs/09-testing.md`](docs/09-testing.md).

## Cloud Deployment
Free-tier: Vercel/Netlify (frontend) + Render (backend Docker) + Supabase (PostgreSQL + S3-compatible Storage). AWS/Azure/GCP mapping included. See [`docs/08-deployment.md`](docs/08-deployment.md).

## Security
Password hashing (bcrypt), JWT + revocation, RBAC, ownership checks, private storage, extension + size + magic-byte validation, path-traversal guard, CORS allow-list, rate limiting, security headers, audit logs, no secrets in code. See [`docs/10-security-scalability-failure.md`](docs/10-security-scalability-failure.md).

## Scalability
Stateless API behind a load balancer, autoscaling containers/serverless, managed DB with read replicas + indexes, object storage + CDN, queues/workers for scanning & notifications. See same document.

## Failure Handling
Storage down -> 503 with `Retry-After`, nothing saved. DB fails after upload -> uploaded file deleted (compensation). Duplicate/retry -> idempotent via content hash + unique constraint. Expired token -> 401 and automatic logout in the UI.

## Screenshots
Store in `screenshots/` using the names in [`docs/11-github-proof.md`](docs/11-github-proof.md), then embed here:
`![Login](screenshots/03-login-page.png)`

## Results
All 19 automated tests pass. Local end-to-end flow (register -> create assignment -> upload -> grade -> view feedback) verified.

## Limitations
Local demo has no antivirus scan; in-memory rate limiter is per-instance; no email notifications; JWT is stateless with a blacklist table; single-file submission per assignment.

## Future Improvements
Email/SMS notifications, plagiarism check, ClamAV scanning worker, direct-to-S3 presigned uploads, Alembic migrations, group assignments, LTI integration, admin UI.

## Learning Outcomes
Cloud service models, managed DB vs object storage, IAM-style RBAC, secure file handling, REST design, idempotency, CI/CD, deployment and observability.

## Author
`Piyush K. Ahirwar` - `IIP / Diploma E-Placement ` - [GitHub](https://github.com/PiyushK-16) - [LinkedIn](https://www.linkedin.com/in/piyush-k-ahirwar-658633261)
