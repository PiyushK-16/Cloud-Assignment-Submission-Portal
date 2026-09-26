# 18. Local / Virtual Simulation (no paid cloud needed)

**Step 1 - Install:** Python 3.11+, Node.js 18+, Git. Check: `python --version`, `node --version`.
**Step 2 - Virtual env:**
```bash
cd Cloud-Assignment-Submission-Portal
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```
**Step 3 - Backend deps:** `pip install -r requirements.txt` (ends with `Successfully installed ...`).
**Step 4 - Frontend deps:** `cd frontend && npm install && cd ..`
**Step 5 - Configure:** `cp .env.example .env` (Windows: `copy .env.example .env`). Edit `.env`:
`JWT_SECRET=` output of `python -c "import secrets; print(secrets.token_urlsafe(48))"`, and `TEACHER_INVITE_CODE=MYCODE123`. Keep `DATABASE_URL=sqlite:///./portal.db`, `STORAGE_BACKEND=local`.
**Step 6 - Start backend:** `uvicorn backend.app:app --reload`
Expected: `Uvicorn running on http://127.0.0.1:8000` and `Portal started (env=development, storage=local)`. Open http://localhost:8000/docs (Swagger UI) and http://localhost:8000/api/health -> `{"status":"ok"}`.
**Step 7 - Start frontend** (new terminal): `cd frontend && npm run dev` -> `Local: http://localhost:5173/`.
**Step 8 - Create Teacher:** open http://localhost:5173/register -> role Teacher, invite code `MYCODE123` -> redirected to Login. (Wrong/missing code -> error "A valid teacher invite code is required".)
**Step 9 - Create Student:** register again as Student (e.g. `Test Student`, `student1@example.com`, password `Student123`).
**Step 10 - Teacher creates assignment:** login as teacher -> Assignments -> add course "Cloud Computing" -> fill the assignment form (deadline tomorrow, allowed types `pdf`) -> "Assignment created".
**Step 11 - Student logs in:** logout, login as student -> Student Dashboard.
**Step 12 - Student views assignment:** Assignments page -> click **Enroll** on the course -> assignment card appears with status NOT SUBMITTED.
**Step 13 - Upload:** choose `sample_files/sample_assignment.pdf` -> message `Uploaded "sample_assignment.pdf" (1 KB) - status: SUBMITTED`.
**Step 14 - Verify file storage:**
```bash
find uploads -type f
# uploads/assignments/<assignment_id>/<student_id>/<uuid>_sample_assignment.pdf
```
**Step 15 - Verify metadata:**
```bash
sqlite3 portal.db "select submission_id,file_name,submission_status,attempt_count from submissions;"
```
(or open `portal.db` with DB Browser for SQLite). One row, status `SUBMITTED`.
**Step 16 - Teacher views:** login as teacher -> Assignments -> **Review** -> student row; **Download** returns the same PDF.
**Step 17 - Grade:** enter marks (e.g. 85) + feedback -> **Save grade** -> "Grade saved", status GRADED. Marks above max are rejected (422).
**Step 18 - Student sees result:** login as student -> My Submissions shows `Marks: 85 / 100` and feedback; Dashboard shows Graded 1 and Recent feedback.

## Fast path with dummy data
```bash
python -m backend.utils.seed_data
# Seeded demo data. Accounts (password Demo@12345): teacher@demo.edu, admin@demo.edu, asha@demo.edu, ravi@demo.edu, meera@demo.edu
```
## Simulate the *cloud* locally (optional)
Run MinIO (S3-compatible) with Docker and point the app at it:
```bash
docker run -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin123 quay.io/minio/minio server /data --console-address ":9001"
# create bucket "assignments" in http://localhost:9001, then in .env:
# STORAGE_BACKEND=s3  S3_BUCKET=assignments  S3_ENDPOINT_URL=http://localhost:9000
# S3_ACCESS_KEY_ID=minioadmin  S3_SECRET_ACCESS_KEY=minioadmin123
```
(Use your own local dev credentials; never reuse them anywhere real.) Likewise run `postgres` in Docker and set `DATABASE_URL=postgresql+psycopg2://...` to test the cloud DB path.
