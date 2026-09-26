# 4. Technology Options & 5. User Roles

## Option A - Beginner (local)
- **Stack:** HTML/CSS/JS + Flask + SQLite + local `uploads/` folder.
- **Architecture:** Browser -> Flask -> SQLite file + folder on disk.
- **Difficulty:** Easy. **Cost:** free.
- **Concepts shown:** client-server, REST, auth basics, DB vs file separation.
- **Advantages:** zero setup, easy to learn. **Limitations:** single machine, no real cloud, files lost if disk dies, not scalable.
- *This repo's `STORAGE_BACKEND=local` + `sqlite` mode runs exactly this way, so you can start here.*

## Option B - Recommended cloud version (**implemented in this repo**)
- **Stack:** React (Vite) + FastAPI + SQLAlchemy; auth = JWT (swap for Supabase Auth/Firebase Auth); DB = Supabase/Neon PostgreSQL; storage = Supabase Storage or Cloudflare R2 (S3 API) ; hosting = Vercel/Netlify (UI) + Render (API).
- **Architecture:** CDN-hosted SPA -> REST API container -> managed Postgres + object bucket.
- **Difficulty:** Medium. **Cost:** free tiers (watch sleep/limit rules, verify current pricing).
- **Concepts:** PaaS, managed DB, object storage, CDN, env-based secrets, CI/CD.
- **Advantages:** real cloud proof, portable (no vendor lock-in since S3 API + SQL), free. **Limitations:** free API tier cold-starts; single region.
- *Firebase variant:* Firebase Auth + Firestore (NoSQL) + Firebase Storage - faster to set up but you lose relational joins; the relational model here is a better fit for grading queries.

## Option C - Advanced (AWS/Azure/GCP)
- **Stack:** Next.js/React on S3+CloudFront, API Gateway -> Lambda (FastAPI + Mangum), RDS/DynamoDB, S3, Cognito, CloudWatch.
- **Difficulty:** High. **Cost:** mostly pay-per-use; small but watch NAT gateways/RDS hours.
- **Concepts:** serverless, API gateway, IAM, CDN, monitoring, autoscaling.
- **Advantages:** industry-standard, highly scalable. **Limitations:** steep learning curve, billing risk, cold starts, IAM complexity.

**Recommendation for students:** build/run on Option A mode first, deploy Option B, and *describe/map* Option C in the report (or deploy it using the AWS free tier if you have it).

## 5. Roles & Permission table
| Permission | Student | Teacher | Admin (optional) |
|---|:-:|:-:|:-:|
| Register / login | Y | Y (invite code) | seeded |
| View assigned coursework & deadlines | Y (enrolled) | Y (own) | Y |
| Upload / resubmit assignment | Y | N | N |
| View own submissions / marks / feedback | Y | - | - |
| Download own submission | Y | - | - |
| Create / update / delete assignment | N | Y (own course) | Y |
| Set deadline & policies | N | Y | Y |
| View / download students' submissions | N | Y (own course) | Y |
| Give marks & feedback | N | Y (own course) | Y |
| View submission statistics | N | Y | Y |
| Manage users / courses / assign roles | N | N | Y (admin UI is a future extension; role exists in the API and seed script) |
