# 19. Cloud Deployment
> Free-tier limits and UI labels change - confirm on each provider's pricing page before relying on them.

## Approach A - Free-tier / student friendly
| Layer | Service | Steps |
|---|---|---|
| Database | **Supabase** or **Neon** (PostgreSQL) | Create project -> copy the Postgres connection string -> `DATABASE_URL=postgresql+psycopg2://...` (tables auto-created at startup) |
| Storage | **Supabase Storage** (S3-compatible) or **Cloudflare R2** | Create a **private** bucket -> create S3 access keys -> set `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` |
| Backend | **Render** web service (Docker) | New Web Service from GitHub repo -> Runtime Docker (uses `Dockerfile`) -> add env vars (JWT_SECRET, TEACHER_INVITE_CODE, DATABASE_URL, S3_*, `APP_ENV=production`, `CORS_ORIGINS=https://<frontend-url>`) -> health check path `/api/health` |
| Frontend | **Vercel** or **Netlify** | Import repo -> root `frontend` -> build `npm run build`, output `dist` -> env `VITE_API_BASE_URL=https://<render-url>/api`; add an SPA rewrite of all routes to `/index.html` |
| Authentication | JWT built into the API (or swap to Supabase Auth / Firebase Auth - only `cloud/auth_service.py` + token verification middleware change) |
| CI/CD | GitHub Actions runs tests; Render/Vercel auto-deploy on push to `main` |

Deployment checklist: set env vars in the dashboard (never commit them) -> deploy backend -> open `/docs` -> deploy frontend -> update `CORS_ORIGINS` to the real frontend URL -> register teacher/student -> run the full flow -> take screenshots (dashboards + live URL).

## Approach B - AWS / Azure / GCP mapping
| Component | AWS | Azure | GCP |
|---|---|---|---|
| Frontend + CDN | S3 + CloudFront | Static Web Apps / Blob + Front Door | Cloud Storage + Cloud CDN / Firebase Hosting |
| Backend | Lambda (Mangum) / App Runner / ECS / EC2 | Functions / Container Apps / App Service | Cloud Functions / Cloud Run |
| API layer | API Gateway | API Management | API Gateway / Cloud Endpoints |
| Database | RDS PostgreSQL / DynamoDB | Azure DB for PostgreSQL / Cosmos DB | Cloud SQL / Firestore |
| Files | S3 (SSE, private, presigned URLs) | Blob Storage (SAS tokens) | Cloud Storage (signed URLs) |
| Auth | Cognito | Entra External ID (B2C) | Identity Platform / Firebase Auth |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| Logs/metrics | CloudWatch | Azure Monitor | Cloud Logging/Monitoring |

AWS example: build frontend -> `aws s3 sync frontend/dist s3://<bucket>`; API as container on App Runner using the `Dockerfile`; `DATABASE_URL` -> RDS; `STORAGE_BACKEND=s3` with an **IAM role** (no keys needed - boto3 uses the role); Cognito issues JWTs verified in middleware; CloudWatch alarms on 5xx and latency.

## Local development vs cloud deployment
| | Local | Cloud |
|---|---|---|
| DB | SQLite file | Managed PostgreSQL (backups, replicas) |
| Files | `./uploads` | Private bucket |
| Run | `uvicorn --reload` | Container behind HTTPS + load balancer |
| Secrets | `.env` | Platform secret store / IAM roles |
| Scale | 1 process | Autoscaled instances |
| URL | localhost | Public HTTPS domain |
