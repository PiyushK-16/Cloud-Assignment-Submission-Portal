# 6. Database Design & 7. Cloud Storage Design

## Entity relationships
```
users(teacher) 1--* courses 1--* assignments 1--* submissions *--1 users(student)
courses *--* users(student)   via enrollments
```

## Tables (implemented in `backend/models/db_models.py`)
**users**: `user_id` PK, name, email UNIQUE (indexed), password_hash, role, created_at
**courses**: `course_id` PK, course_name, `teacher_id` FK->users (indexed), created_at
**enrollments**: `enrollment_id` PK, `course_id` FK, `student_id` FK, UNIQUE(course_id, student_id)
**assignments**: `assignment_id` PK, `course_id` FK (indexed), title, description, deadline (indexed, UTC), max_marks, allowed_file_types, max_file_size_mb, allow_late, allow_resubmission, `created_by` FK, created_at, updated_at
**submissions**: `submission_id` PK, `assignment_id` FK (indexed), `student_id` FK (indexed), file_name, file_url (private API path), storage_path, file_size, content_hash (sha256), submitted_at, submission_status (indexed), is_late, attempt_count, marks, feedback, graded_at, graded_by FK; UNIQUE(assignment_id, student_id)
**revoked_tokens**: `jti` PK, expires_at (logout blacklist)

## Keys, relationships, indexes
- **Primary keys** are random UUID hex strings: unguessable, so `/submissions/123` style enumeration attacks fail.
- **Foreign keys** keep integrity (no submission without an assignment/student).
- **Unique constraints** enforce "one row per student per assignment" even if two requests race.
- **Indexes** on every FK and on `deadline`, `submission_status`, `email` speed the dashboard and lookup queries (index = sorted lookup structure, like a book index).

## Example cloud-database queries
```sql
-- student's pending assignments
SELECT a.* FROM assignments a
JOIN enrollments e ON e.course_id = a.course_id AND e.student_id = :me
LEFT JOIN submissions s ON s.assignment_id = a.assignment_id AND s.student_id = :me
WHERE s.submission_id IS NULL;

-- teacher: pending reviews / late / graded
SELECT submission_status, COUNT(*) FROM submissions s
JOIN assignments a USING (assignment_id) JOIN courses c USING (course_id)
WHERE c.teacher_id = :teacher GROUP BY submission_status;
```
The dashboards (`backend/services/dashboard_service.py`) compute the same numbers with the ORM.

## Why not store files as DB binary (BLOB/BYTEA)?
Large rows slow queries and replication, backups become huge and slow, DB storage is 10-50x pricier than object storage, streaming/resuming is awkward, and you cannot use CDN/signed URLs/lifecycle rules. Store **bytes in object storage, references in the DB**.

## Cloud database vs cloud object storage
| | Cloud database | Object storage |
|---|---|---|
| Holds | users, assignments, deadlines, submission metadata, marks, feedback | PDF/DOCX/ZIP/images |
| Access | SQL queries, joins, transactions | put/get/delete by key |
| Strength | structure, consistency | cheap, durable, huge files |
| Example | Supabase Postgres, RDS | S3, R2, Supabase Storage |

## Storage layout
```
assignments/
  <assignment_id>/
    <student_id>/
      <uuid>_report.pdf      <- current submission (old file deleted on resubmission)
```
- **File naming:** `uuid + sanitized original name` (`safe_filename`) -> no collisions, no `../` tricks.
- **Unique IDs:** assignment/student IDs are UUIDs; the DB row stores `storage_path`.
- **Upload:** validate -> `storage.save()` -> DB row. **Download:** authorize -> `storage.read()` (or `signed_url` for S3). **Delete:** on assignment deletion and after replacing a file.
- **Access permissions:** bucket **private**; only the backend credentials can read/write; users never receive the bucket key. **Signed URL** = time-limited link (default 300 s) that the backend creates after checking permission.
