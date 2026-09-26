# 1. Project Explanation & 2. Industry Relevance

## What is it?
A **Cloud-Based Student Assignment Submission & Feedback Portal** is a web application, hosted on cloud infrastructure, where teachers publish assignments and students submit files online. Teachers grade and comment; students see results - all in one place, from any device.

## Problem it solves
Assignments sent by email/WhatsApp/pen-drives get lost, deadlines are disputed, feedback is scattered, teachers cannot see who has not submitted, and nothing is auditable.

## Why cloud computing suits it
| Need | Cloud answer |
|---|---|
| Access from anywhere | App and data are on internet-reachable servers, not on one college PC |
| Deadline-night traffic spikes | Elastic compute (autoscaling / serverless) |
| Growing file storage | Object storage scales to petabytes, pay-per-use |
| Safe data | Managed backups, replication, encryption |
| Central management | One database + one bucket = one source of truth |

## A. Simple explanation
Think of a digital classroom drawer. The teacher puts a task in the drawer (with a due date). Each student drops their file in their own locked box. The teacher opens the boxes, writes marks and comments on a card, and the student reads that card later. The "drawer" (database) remembers *information*; the "locked boxes" (object storage) keep the *files*.

## B. Technical explanation
- **Compute:** stateless FastAPI service (container / serverless function).
- **Database (PostgreSQL):** users, courses, assignments, submission *metadata*, marks, feedback. Relational integrity, indexes, transactions.
- **Object storage (S3-compatible):** the actual PDF/DOCX/ZIP bytes under `assignments/<assignment>/<student>/<uuid>_<name>`. Cheap, durable (11 nines on S3), private by default.
- **Auth:** JWT issued at login; RBAC enforced on every request.
- **Why not files in the DB?** Binary blobs bloat and slow the DB, inflate backups, and cost far more per GB; object storage streams big files, supports signed URLs and lifecycle rules.
- **Why metadata in a DB?** You need queries (“late submissions for assignment X”), joins, constraints and transactions - not possible on a bucket.

## Workflow
```
Teacher -> Creates Assignment -> Cloud Database -> Student Dashboard
Student -> Uploads Assignment -> Cloud Object Storage -> Submission Metadata Saved (DB)
Teacher -> Reviews Submission -> Marks + Feedback -> Cloud Database -> Student Views Feedback
```
1. `POST /api/assignments` inserts a row in `assignments`.
2. `GET /api/assignments` (student) joins enrollments -> shows it.
3. `POST /api/assignments/{id}/submit` validates, writes the file to storage, then inserts/updates `submissions` (status SUBMITTED or LATE from the **server clock**).
4. `GET /api/assignments/{id}/submissions` (teacher) lists them; `/download` streams the file after authorization.
5. `POST /api/submissions/{id}/grade` stores `marks`, `feedback`, `graded_at`, sets GRADED.
6. `GET /api/submissions/{id}/feedback` (student) reads them back.

## Industry relevance
The same pattern - *identity + relational metadata + object storage + REST API + CDN-hosted UI* - powers:

| Domain | Example use |
|---|---|
| Learning Management Systems | Moodle, Canvas, Google Classroom, Blackboard assignment modules |
| Universities / Schools | Coursework submission, exam script upload, thesis submission |
| Corporate training | Compliance course evidence uploads, manager review |
| Online certification | Capstone project submission and grading |
| Employee training portals | Onboarding tasks with reviewer feedback |
| Bootcamps | Weekly project reviews with mentor comments |
| EdTech platforms | Coursera/Udemy-style graded assignments at massive scale |

## Business benefits
Centralized data | remote accessibility | scalable storage | automated submission tracking (LATE/GRADED) | far less paperwork | feedback kept with the work | secure role-based access | backup and high availability.
