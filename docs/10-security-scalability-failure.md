# 21. Cloud Security, 22. Scalability, 23. Failure Handling

## Security (what is implemented -> where)
| Topic | Implementation |
|---|---|
| Authentication | bcrypt + JWT (`cloud/auth_service.py`) |
| Authorization / RBAC | `require_role`, ownership checks in services |
| HTTPS / encryption in transit | Terminate TLS at platform/CDN/LB (Render, Vercel, CloudFront); never send tokens over HTTP |
| Encryption at rest | Managed DB disk encryption; S3 SSE (`ServerSideEncryption=AES256` set in `S3Storage.save`) |
| Password hashing | bcrypt with per-password salt (cost from `BCRYPT_ROUNDS`); never store plain passwords |
| Secure uploads | whitelist of types, per-assignment size limit, magic-byte check, sanitized names, UUID keys, `nosniff` on download |
| Malware scanning (concept) | S3 event -> serverless function -> ClamAV/cloud scanner -> mark `QUARANTINED`; not run in local mode |
| Signed URLs | `/download-url` (S3) - 300 s expiry, issued only after authorization |
| Storage permissions | private bucket; single service credential; least-privilege IAM (PutObject/GetObject/DeleteObject on one prefix) |
| Database permissions | app DB user without superuser; no public DB access; parameterized ORM queries (no SQL injection) |
| Env vars / secrets | `.env` git-ignored; platform secret store; app refuses placeholder JWT secret in production |
| CORS | explicit origin allow-list, limited methods/headers |
| Rate limiting | login/register limiter (`middleware/rate_limit.py`); API Gateway/WAF for global limits |
| Input validation | Pydantic models + service checks |
| Logging / audit logs | `audit()` events: register, login success/failure, logout, assignment changes, submission saved, graded, file downloaded |
| Backup | managed DB backups/PITR, bucket versioning, periodic `pg_dump` |
| Other | user-enumeration-safe login errors, unguessable IDs, token revocation, security headers |

**Common student mistakes to avoid:** committing `.env`/keys (rotate immediately if it happens); public buckets; `allow_origins=["*"]` with credentials; trusting the frontend for security; storing passwords/tokens in plain text; using the admin DB user in the app; leaving debug mode/default passwords; granting `s3:*` on `*`; no file validation; no billing alerts.

## Scalability
| Scale | Architecture |
|---|---|
| **10 students** | 1 small container + SQLite/free Postgres + local/free bucket. Anything works |
| **1,000 students** | Managed Postgres, S3-compatible storage, 2+ API instances behind a load balancer, CDN for frontend, indexes on FKs/deadline, health checks, basic alerts |
| **100,000 students** | Autoscaled API (Cloud Run/ECS/Lambda) behind API Gateway + WAF, Postgres with read replicas + connection pooling (PgBouncer/RDS Proxy), Redis cache for assignment lists, **direct-to-S3 presigned uploads**, queue (SQS/Pub/Sub) + workers for virus scan/notifications/grade emails, CDN, multi-AZ, monitoring + autoscaling policies |

Tools: **load balancer** spreads requests; **autoscaling** adds/removes instances; **serverless** scales to zero and bursts; **managed DB** gives replicas/failover; **object storage** is effectively unlimited; **CDN** offloads static assets; **caching** cuts repeated reads; **queues/workers** absorb spikes.

**Deadline-night scenario (100,000 uploads in 10 minutes):** (1) CDN serves the UI, so API only handles JSON. (2) Client asks API for a presigned S3 URL (tiny request); browser uploads straight to S3, so the API never streams gigabytes. (3) S3 event -> queue -> worker records the submission and scans it, at a rate the DB can sustain (queue smooths the burst). (4) API autoscales on CPU/request count; DB uses pooling. (5) The user gets an immediate "received" state and the final SUBMITTED/LATE status is based on the server-recorded *upload-confirmation* time. (6) Rate limits and retries with jitter protect the system; dashboards read from replicas/cache.

## Failure handling
| Failure | Behaviour in this project | Client experience |
|---|---|---|
| File upload fails | storage error -> 503 + `Retry-After`; DB untouched | message, user retries |
| DB temporarily unavailable | `OperationalError` -> 503; if it fails after upload, the file is deleted (compensation) | retry later |
| Storage service fails | 503, no half-saved submission | retry |
| Auth token expires | 401 -> UI clears session, redirects to login | log in again |
| Duplicate submission request | same file hash -> idempotent 200 (no new attempt); race on insert -> unique constraint -> 409 | safe double-click/retry |
| Internet drops during upload | request fails client-side ("Cannot reach the server"); nothing recorded because DB write happens only after successful storage write | re-upload |
| Backend server fails | stateless -> LB sends traffic to another instance; health check restarts the failed one; state is in DB/bucket | brief errors, then works |

**Retry strategy:** retry only idempotent/safe operations with exponential backoff + jitter (e.g. 1s, 2s, 4s; max 3-5 tries). **Idempotency:** performing the same request many times has the same effect as once - here guaranteed by the content hash check + unique (assignment, student) constraint; production systems often add an `Idempotency-Key` header.
