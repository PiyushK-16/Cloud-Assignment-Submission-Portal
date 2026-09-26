# 29. Resume / LinkedIn Proof & 30. Interview Preparation
> Only claim what you actually built, deployed and can explain. Replace the bracketed items with your real deployment/results.

## A. Resume bullets
- Designed and deployed a cloud-based assignment portal using **React, FastAPI, managed PostgreSQL and S3-compatible object storage**, separating file storage from relational metadata for durability and scalability.
- Implemented **JWT authentication with role-based access control**, private-bucket file handling, server-side deadline logic and audit logging; verified with **19 automated pytest cases** and a GitHub Actions CI pipeline.
- Built failure-aware workflows (idempotent uploads, compensating deletes, 503 retry semantics) and documented a **cloud scaling path** (CDN, API gateway, autoscaling, queues) for 100k concurrent students.

## B. Two-line project description
Cloud-hosted assignment submission & feedback platform with role-based access, managed database, private object storage, grading workflow and CI/CD. Deployed on free-tier cloud services with an AWS/Azure/GCP migration mapping.

## C. LinkedIn description
**Cloud-Based Student Assignment Submission & Feedback Portal** - I built a cloud-native portal where teachers create assignments and students submit files securely. Files are stored in private object storage, metadata in a managed PostgreSQL database, and access is controlled with JWT + RBAC. I implemented deadline/late handling on server time, grading and feedback, dashboards, rate limiting, audit logs, automated tests and GitHub Actions CI, and deployed it on [Render/Vercel/Supabase]. I also documented how the architecture maps to AWS (S3, CloudFront, API Gateway, Lambda/RDS, Cognito, CloudWatch). Skills: cloud storage, cloud databases, REST APIs, authentication/authorization, security, CI/CD, scalability design. GitHub: <link>.

## D. Technical skills demonstrated
Cloud computing (SaaS/PaaS/IaaS), object storage (S3 API), managed PostgreSQL, SQLAlchemy, FastAPI, REST design, JWT/bcrypt, RBAC, secure file upload, signed URLs, idempotency, CORS/rate limiting, logging/audit, Docker, GitHub Actions, pytest, React, Git, cloud architecture & scaling.

## E. GitHub project description
Cloud-based student assignment submission and feedback platform featuring role-based authentication, cloud database integration, object storage, assignment management, secure file submission, grading, and feedback workflows.

## 30. Interview Q&A
**1. Explain your project.**
I built a cloud-based assignment portal. Teachers create courses and assignments with deadlines and file rules; students enroll, upload their work, and later see marks and feedback. Architecturally it is a React frontend talking to a FastAPI REST backend. Files go to private object storage, while users, assignments, submission metadata, marks and feedback go to a relational database. Authentication is JWT-based with role-based authorization, deadline status is computed on the server, and I deployed it on free-tier cloud services with tests and CI.

**2. Why object storage for files and a database for metadata?**
They solve different problems. The database is good for structured queries, joins and transactions - for example "late submissions for this assignment". Object storage is cheap, durable and built for large binary files, and supports signed URLs. Putting PDFs in database columns would bloat backups, slow queries and cost more, so I store bytes in the bucket and only the `storage_path` and metadata in the database.

**3. How does your authentication work?**
On login the API verifies the bcrypt password hash and issues a signed JWT with user id, role, expiry and a unique `jti`. The frontend sends it as a Bearer token. A dependency validates signature and expiry on every request. For logout I store the `jti` in a revoked-tokens table so the token stops working immediately. In a managed setup I could replace it with Cognito or Supabase Auth and only verify tokens.

**4. How do you enforce authorization?**
Two layers. First, role checks: `require_role("teacher")` blocks students from teacher endpoints with 403. Second, resource ownership in the service layer: a student can access only their own submission, and a teacher only submissions in their own course. I tested this - for example another student gets 403 on download, and an unauthenticated call gets 401. The React route guard is only for UX; the backend is the real enforcement.

**5. How do file uploads and downloads work securely?**
On upload I check authentication, enrollment, deadline policy, extension whitelist, size limit, and the file's magic bytes so a renamed `.exe` fails. I sanitize the name and store it under a UUID-prefixed key. The bucket is private, so download goes through an authorization check and then streams the file, or issues a 5-minute signed URL on S3. Nobody gets a permanent public link.

**6. How do you handle deadlines and late submissions?**
The server records `submitted_at` in UTC and compares it to the stored UTC deadline: on or before is SUBMITTED, after is LATE. Teachers can choose per assignment whether late uploads are allowed at all. I don't trust the browser clock because users can change it, and storing everything in UTC avoids timezone bugs; the UI converts to local time only for display.

**7. What happens if something fails midway?**
I ordered operations so failures are safe: file first, then database. If storage fails, the API returns 503 and nothing is saved. If the database write fails after the file was uploaded, I delete the uploaded file as compensation. Duplicate or retried requests are idempotent - the same file hash returns the existing submission and a unique constraint stops races. Expired tokens return 401 and the UI sends the user to login.

**8. How would it scale to 100,000 students near a deadline?**
The API is stateless, so I'd run it on autoscaling containers or serverless behind a load balancer/API gateway, with the UI on a CDN. I'd switch to presigned direct-to-S3 uploads so servers don't carry file bytes, use a queue and workers for virus scanning and notifications, Postgres with connection pooling and read replicas, and caching for assignment lists. Rate limiting and retries with backoff protect the system during the spike.

**9. How did you deploy it, and what differs from local?**
Locally it's SQLite and a local uploads folder. In the cloud I changed only environment variables: `DATABASE_URL` points to managed PostgreSQL and `STORAGE_BACKEND=s3` points to a private bucket. The backend runs from the Dockerfile on a PaaS, the frontend is a static build on a CDN host with the API URL configured, and secrets live in the platform's environment settings. GitHub Actions runs tests on every push. I also mapped the design to AWS: S3/CloudFront, API Gateway, Lambda or App Runner, RDS, Cognito and CloudWatch.

**10. How did you test it, and what would you improve?**
I wrote 19 automated pytest tests covering the 25-case matrix: registration, invalid login, RBAC, upload validation, late logic, resubmission, grading limits, another student's access, storage and database failures, and logout revocation. Next I'd add antivirus scanning through a queue worker, email notifications, Alembic migrations, direct-to-S3 uploads, and an admin UI.
