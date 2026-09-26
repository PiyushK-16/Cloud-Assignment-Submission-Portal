# 15-16. System Architecture & Folder Structure

## Standard architecture (implemented)
```
Student / Teacher
      |
React Web Application (Vite build on CDN)
      |  HTTPS + Bearer JWT
REST API (FastAPI)  <-- Authentication service (cloud/auth_service.py)
      |
Backend application (routes -> services -> cloud adapters)
   /                    \
Cloud DB (PostgreSQL)   Object Storage (S3-compatible)
      |
Logging / Monitoring
```

## Advanced cloud architecture
```
Users -> CDN (CloudFront) -> Frontend hosting (S3 / Vercel)
      -> API Gateway (throttling, JWT authorizer)
      -> Backend / Serverless Functions (Lambda / Cloud Run)
      -> Managed Database (RDS/Aurora) + Object Storage (S3)
      -> Monitoring / Logging (CloudWatch)
Side path: S3 event -> Lambda -> virus scan -> update submission status
```

## Request flow: student uploads a file
1. Browser (React) posts multipart to `/api/assignments/{id}/submit` with the JWT.
2. CDN/gateway/load balancer routes to any healthy API instance.
3. `require_role("student")` validates the token (signature, expiry, blacklist).
4. Service checks enrollment, deadline policy, extension, size, magic bytes.
5. File is written to object storage (`assignments/<a>/<s>/<uuid>_<name>`).
6. Metadata row is inserted/updated (status from server time). If this fails, the file is deleted (compensation).
7. JSON confirmation returned; access + audit logs written.

## Folder structure explained
| Folder | Purpose |
|---|---|
| `frontend/src/pages` | screens (login, dashboards, upload, grading) |
| `frontend/src/components` | reusable UI (navbar, route guard, status badge) |
| `frontend/src/services` | API client + auth context (only place that calls the backend) |
| `frontend/src/utils` | formatting helpers |
| `backend/app.py` | application entry, middleware, error handlers |
| `backend/routes` | thin HTTP layer per resource |
| `backend/services` | business rules (deadline, grading, access control) |
| `backend/models` | DB tables + request schemas |
| `backend/middleware` | authentication/RBAC, rate limiter |
| `backend/utils` | validators, logging, time, serializers, seed script |
| `cloud/` | **cloud adapters**: database, object storage, auth - swap providers here only |
| `tests/` | pytest suite | `sample_files/` dummy PDFs | `screenshots/` proof images | `docs/` documentation | `reports/` project report |
