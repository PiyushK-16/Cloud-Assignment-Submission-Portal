# 24, 26, 27. GitHub Strategy, 13-Day Proof Plan, Screenshot Checklist

## Repository
- **Name:** `Cloud-Based-Assignment-Submission-Portal`
- **Description:** Cloud-based student assignment submission and feedback platform featuring role-based authentication, cloud database integration, object storage, assignment management, secure file submission, grading, and feedback workflows.
- **Topics:** cloud-computing, edtech, python, fastapi, flask, react, cloud-storage, firebase, database, rest-api, full-stack, authentication

## Git commands
```bash
cd Cloud-Assignment-Submission-Portal
git init -b main
git add .gitignore README.md requirements.txt .env.example
git commit -m "Initialize cloud assignment portal"
# create an EMPTY repo on github.com first (no README), then:
git remote add origin https://github.com/<your-username>/Cloud-Based-Assignment-Submission-Portal.git
git push -u origin main
```
Check before every push: `git status` shows **no `.env`**, `*.db` or `uploads/`.

## Recommended commits (do them in this order; commands are the same pattern)
```bash
git add <files> && git commit -m "<message>" && git push
```
1 "Initialize cloud assignment portal" | 2 "Create frontend and backend architecture" | 3 "Implement authentication and role management" | 4 "Add assignment management module" | 5 "Integrate cloud database" | 6 "Implement cloud file storage" | 7 "Add student assignment submission workflow" | 8 "Implement deadline validation" | 9 "Add teacher grading and feedback" | 10 "Build student and teacher dashboards" | 11 "Add security and authorization" | 12 "Add automated tests" | 13 "Deploy application to cloud" | 14 "Complete README and documentation".

## 13-day development history
| Day | Files | Functionality | Commit | Screenshot | Proves |
|---|---|---|---|---|---|
| 1 | README skeleton, `.gitignore`, `.env.example`, folders, `docs/06-architecture.md` | Architecture + repo | "Initialize cloud assignment portal" + "Create frontend and backend architecture" | `01-project-folder-structure.png`, `02-architecture-diagram.png` | Planning, cloud design |
| 2 | `cloud/auth_service.py`, `routes/auth.py`, `models/db_models.py` (users), `Login/Register.jsx` | Register/login/logout, JWT | "Implement authentication and role management" | `03-login-page.png`, `04-student-registration.png` | Authentication |
| 3 | `middleware/auth.py`, `ProtectedRoute.jsx` | RBAC, protected routes | same commit series | `20-authorization-error-demo.png` | Authorization |
| 4 | `assignment_service.py`, `routes/assignments.py`, `TeacherAssignments.jsx` | Assignment CRUD + validation | "Add assignment management module" | `06-assignment-creation.png` | Business logic |
| 5 | `cloud/database_service.py`, PostgreSQL URL | SQLite -> managed Postgres | "Integrate cloud database" | `13-database-submission-record.png` | Cloud DB |
| 6 | `cloud/storage_service.py` | Local + S3 bucket | "Implement cloud file storage" | `12-cloud-storage-file.png` | Object storage |
| 7 | `submission_service.py`, `StudentAssignments.jsx` | Upload/resubmit/validate | "Add student assignment submission workflow" | `10-file-selection.png`, `11-successful-upload.png` | File handling |
| 8 | deadline logic in service | SUBMITTED/LATE, policy | "Implement deadline validation" | `14-on-time-status.png`, `15-late-submission-demo.png` | Server-side time |
| 9 | grade endpoints, `TeacherSubmissions.jsx`, `MySubmissions.jsx` | Marks + feedback | "Add teacher grading and feedback" | `16-teacher-submission-list.png`, `18-marks-feedback.png`, `19-student-feedback-page.png` | Workflow |
| 10 | `dashboard_service.py`, dashboards | Stats | "Build student and teacher dashboards" | `05-teacher-dashboard.png`, `07-student-dashboard.png` | Queries |
| 11 | `rate_limit.py`, validators, `tests/` | Security + tests | "Add security and authorization", "Add automated tests" | `22-automated-tests.png`, `21-api-response.png` | Quality |
| 12 | `Dockerfile`, CI, deploy config | Cloud deployment | "Deploy application to cloud" | `23-cloud-deployment-dashboard.png`, `24-live-application.png` | Deployment |
| 13 | README, docs, report | Documentation | "Complete README and documentation" | `25-github-commits.png`, `26-github-repository.png`, `27-readme-preview.png` | Professionalism |

## Screenshot checklist (save in `screenshots/`)
01-project-folder-structure.png | 02-architecture-diagram.png | 03-login-page.png | 04-student-registration.png | 05-teacher-dashboard.png | 06-assignment-creation.png | 07-student-dashboard.png | 08-assignment-list.png | 09-assignment-details.png | 10-file-selection.png | 11-successful-upload.png | 12-cloud-storage-file.png | 13-database-submission-record.png | 14-on-time-status.png | 15-late-submission-demo.png | 16-teacher-submission-list.png | 17-teacher-reviewing-file.png | 18-marks-feedback.png | 19-student-feedback-page.png | 20-authorization-error-demo.png | 21-api-response-swagger.png | 22-automated-tests-pass.png | 23-cloud-deployment-dashboard.png | 24-live-application.png | 25-github-commits.png | 26-github-repository.png | 27-readme-preview.png

Tips: blur/crop any secrets (DB URLs, keys) in dashboard screenshots; show dummy data only; make the late demo by setting a short deadline then waiting (or editing the deadline through `PUT /api/assignments/{id}`).
