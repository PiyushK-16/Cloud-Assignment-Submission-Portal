# Cloud-Based Student Assignment Submission & Feedback Portal - Project Report
*(Author: <Your Name> | Course: Cloud Computing | Institution: <Your College> | Date: <Month Year>)*

## Abstract
This project presents a cloud-based portal that lets teachers publish assignments and students submit work online. The system separates concerns the way production cloud systems do: a REST API (FastAPI) for business logic, a managed relational database for metadata, private object storage for files, and JWT-based role-aware authentication. It runs entirely locally for development and deploys to free-tier cloud services by configuration alone. The project demonstrates SaaS/PaaS/IaaS concepts, RBAC, secure file handling, scalability design, failure handling, automated testing and CI/CD.

## 1. Introduction
Digital learning depends on reliable submission and feedback workflows. Cloud computing provides on-demand, scalable, accessible infrastructure, making it ideal for such a system.

## 2. Problem Statement
Manual or ad-hoc submission (email, messaging apps, physical copies) leads to lost files, missed deadlines, no audit trail, scattered feedback, and heavy teacher workload.

## 3. Objectives
Central cloud-hosted platform; role-based access; deadline enforcement; secure file storage; grading & feedback; dashboards; tests; documentation; free-tier deployment.

## 4. Existing System
Email/WhatsApp/Drive links/paper. Limitations: no deadline automation, weak access control, difficult tracking, storage and versioning problems, no analytics.

## 5. Proposed System
A web portal with cloud database + object storage + API + role-based UI, offering automated status tracking (SUBMITTED/LATE/GRADED), private file access, and structured feedback.

## 6. User Roles
Student, Teacher, Admin (optional). See permission table in `docs/03-tech-options-and-roles.md`.

## 7. Cloud Computing Concepts
Mapping of SaaS, PaaS, IaaS, cloud DB, object storage, auth, RBAC, REST, serverless, scalability, elasticity, availability, load balancing, CDN, API gateway, secrets, logging, monitoring, backup and CI/CD - see `docs/02-cloud-concepts.md`.

## 8. Technology Stack
React + Vite, FastAPI, SQLAlchemy, PostgreSQL/SQLite, S3-compatible storage (boto3), PyJWT, bcrypt, pytest, Docker, GitHub Actions; hosting on Render/Vercel/Supabase (free tier) with AWS/Azure/GCP mapping.

## 9. System Architecture
Client -> CDN-hosted SPA -> REST API -> {Managed DB, Object Storage} -> Logging/Monitoring. Advanced variant adds API Gateway, serverless functions and queues (`docs/06-architecture.md`).

## 10. Database Design
Tables users, courses, enrollments, assignments, submissions, revoked_tokens with PK/FK/unique constraints and indexes (`docs/04-database-storage-design.md`).

## 11. Cloud Storage Design
Private bucket; key `assignments/<assignment>/<student>/<uuid>_<name>`; signed URLs; DB stores only references.

## 12. Authentication
bcrypt-hashed passwords; JWT with role and `jti`; logout revocation; teacher invite code; rate limiting.

## 13. Assignment Management
CRUD with validation (title, marks, future deadline, allowed types, size, policies) restricted to the course's teacher.

## 14. Submission Workflow
Select -> validate (auth, enrollment, deadline, extension, size, magic bytes, duplicates, resubmission policy) -> store file -> save metadata -> confirm. Compensating delete on DB failure.

## 15. Deadline Management
Server UTC timestamp compared with UTC deadline; configurable late policy; client clock never trusted.

## 16. Feedback & Grading
Course teacher enters marks (<= max) and feedback; status GRADED; student read-only view; regrade allowed for teachers, resubmission blocked after grading.

## 17. API Design
25 REST endpoints with consistent status codes (`docs/05-api-and-security-design.md`).

## 18. Implementation
Layered backend (routes -> services -> cloud adapters), React SPA with API service layer and auth context, dummy-data seed script, Dockerfile, CI workflow.

## 19. Testing
19 automated pytest tests covering a 25-case matrix (`docs/09-testing.md`); all passed in the recorded run. Manual UI checks documented in `docs/07-local-setup.md`.

## 20. Cloud Deployment
Free-tier: Supabase/Neon (DB), Supabase Storage/R2 (files), Render (API), Vercel/Netlify (UI). Enterprise mapping to AWS/Azure/GCP (`docs/08-deployment.md`).

## 21. Security
Authentication, RBAC, ownership checks, private storage, validation, CORS, rate limiting, audit logs, secrets in env vars, encryption in transit/at rest (`docs/10-security-scalability-failure.md`).

## 22. Scalability
Designs for 10, 1,000 and 100,000 students using load balancing, autoscaling, serverless, managed DB, CDN, caching and queues; deadline-night scenario analysed.

## 23. Results
Working end-to-end flow (register -> assignment -> upload -> grade -> feedback); 19/19 tests passing; local and cloud-ready modes; documented deployment. *(Add your deployed URL and screenshots.)*

## 24. Advantages
Centralized, accessible, secure, scalable, auditable, portable across providers, low cost.

## 25. Limitations
No antivirus scan in local mode; per-instance rate limiter; no notifications; single file per submission; free-tier cold starts; basic UI.

## 26. Future Scope
Notifications, plagiarism detection, malware-scanning workers, presigned direct uploads, Alembic migrations, group work, analytics, LMS (LTI) integration, mobile app, admin console.

## 27. Conclusion
The project shows how core cloud services - identity, database, object storage, compute and delivery - combine into a secure, scalable application, and how the same design can move from a student laptop to production cloud infrastructure.
