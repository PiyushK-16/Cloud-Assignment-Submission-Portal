# 3. Cloud Computing Concepts - and where each appears

| Concept | Where it appears in this project |
|---|---|
| **Cloud computing** | App, DB and files run on provider infrastructure (Render/Supabase/S3), reachable over the internet, billed by use / free tier |
| **SaaS** | The finished portal is delivered to students/teachers through a browser - nothing to install (they consume software as a service) |
| **PaaS** | Render/Railway/Vercel run the code without managing servers; Supabase gives managed Postgres + storage + auth |
| **IaaS** | Choosing EC2 / a VM or raw S3 buckets (Option C) - you manage OS/runtime yourself; the `Dockerfile` makes the app run on any IaaS VM |
| **Cloud database** | `cloud/database_service.py` - identical code targets SQLite or managed PostgreSQL via `DATABASE_URL` |
| **Object storage** | `cloud/storage_service.py` - `S3Storage` (AWS S3, Cloudflare R2, Supabase Storage, MinIO) |
| **Authentication** | `cloud/auth_service.py` (bcrypt + JWT), `POST /api/login` |
| **Authorization / RBAC** | `backend/middleware/auth.py::require_role`, ownership checks in `services/*` |
| **REST API** | `backend/routes/*` - resources, verbs, status codes, JSON |
| **Client-server** | React SPA (client) <-> FastAPI (server) over HTTPS |
| **Serverless** | `backend` is stateless and can run as AWS Lambda (via Mangum) / Cloud Run / Azure Functions; file processing (virus scan) would be a serverless function triggered by bucket events |
| **Scalability** | Stateless API + external DB/storage lets you add instances horizontally (doc 10) |
| **Elasticity** | Autoscaling (Cloud Run / ECS / Render) grows near deadlines and shrinks afterwards |
| **Availability** | Managed DB replicas, multi-AZ storage, `/api/health` for health checks |
| **Load balancing** | Managed LB / platform router in front of API instances; the app keeps no local session state so any instance can serve any request |
| **CDN** | Frontend `dist/` served through Vercel/Netlify/CloudFront edge caches |
| **API Gateway** | AWS API Gateway / Azure API Management in Option C - throttling, auth, routing to functions |
| **Environment variables** | `backend/config.py` + `.env.example`; nothing secret in code |
| **Secrets management** | Platform secret stores (Render env, AWS Secrets Manager, GCP Secret Manager); `.env` git-ignored |
| **Logging** | `backend/utils/logger.py`, access log middleware, audit events -> CloudWatch / Cloud Logging |
| **Monitoring** | `/api/health` + uptime monitor (UptimeRobot), platform metrics, alerts on 5xx |
| **Backup** | Managed DB daily backups/PITR; bucket versioning; `pg_dump` in docs |
| **CI/CD** | `.github/workflows/ci.yml` runs tests + build; hosting platforms auto-deploy on push to `main` |
| **Cloud deployment** | doc 08 |
