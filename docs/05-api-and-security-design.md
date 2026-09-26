# 8-14. Auth, Assignments, Submissions, Deadlines, Grading, Dashboards & REST API

## Authentication vs authorization
- **Authentication - "Who are you?"** `POST /api/login` verifies the bcrypt hash and issues a JWT (`sub`, `role`, `jti`, `exp`).
- **Authorization - "What may you do?"** `require_role()` (role check) + `get_submission_for_user()` / `get_managed_assignment()` (ownership check).

| Protection | Enforced by | Test |
|---|---|---|
| Student cannot open Teacher Dashboard | `require_role("teacher","admin")` -> 403 | `test_dashboards_are_role_protected` |
| Student cannot grade | same on `/grade` -> 403 | `test_grading_flow` |
| Student cannot see another's submission | owner check -> 403 | `test_student_privacy` |
| Teacher only sees own courses | `can_manage_course` -> 403 | `test_grading_flow` (teacher2) |
| No anonymous download | Bearer token required -> 401 | `test_student_privacy` |
| Logout really logs out | `revoked_tokens` -> 401 | `test_logout_revokes_token` |

## Deadline logic (`submission_service.compute_status`)
`submitted_at <= deadline` -> **SUBMITTED**, otherwise **LATE**. Per-assignment `allow_late=false` rejects late uploads with 403 (configurable). Status `GRADED` is set by grading; `NOT_SUBMITTED` is derived when no row exists.
- **Server timestamp:** `utcnow()` on the server. The browser clock can be wrong or deliberately changed, so it is never trusted.
- **Timezones:** everything stored/compared in UTC; the API returns ISO strings with `Z`; React converts to the viewer's local time. Deadlines sent without an offset are treated as UTC (the UI always sends a proper ISO instant).

## Assignment functions -> code
createAssignment/updateAssignment/deleteAssignment/getAssignments/getAssignmentById = `assignment_service.py` (+ `routes/assignments.py`). Validation: title length, `max_marks > 0`, future deadline, allowed types from a whitelist, size 1-50 MB, ownership.
submitAssignment/resubmitAssignment/getMySubmissions/downloadSubmission = `submission_service.submit`, `list_my_submissions`, `routes/submissions.py::download`.
gradeSubmission/getSubmissionFeedback = `submission_service.grade`, `routes/submissions.py::get_feedback`.

## REST API reference
All bodies JSON except upload (`multipart/form-data`, field `file`). Auth = `Authorization: Bearer <token>`.
Common errors: 401 not/invalid/expired token, 403 not allowed, 404 not found, 422 validation, 429 rate limit, 503 storage/DB unavailable.

| Method | Endpoint | Auth / role | Request | Success | Errors |
|---|---|---|---|---|---|
| POST | /api/register | public | `{name,email,password,role,invite_code?}` | 201 user | 403 bad invite code, 409 duplicate email, 422 weak password |
| POST | /api/login | public | `{email,password}` | 200 `{access_token,user}` | 401 invalid credentials, 429 |
| POST | /api/logout | any | - | 200 | 401 |
| GET | /api/me | any | - | 200 user | 401 |
| POST | /api/courses | teacher/admin | `{course_name}` | 201 | 403, 422 |
| GET | /api/courses | any | - | 200 list | 401 |
| POST | /api/courses/{id}/enroll | student | - | 200 | 404 |
| POST | /api/assignments | teacher/admin | `{course_id,title,description,deadline,max_marks,allowed_file_types,max_file_size_mb,allow_late,allow_resubmission}` | 201 | 403 not your course, 404, 422 |
| GET | /api/assignments | any | `?course_id=` | 200 list (role-scoped) | 401 |
| GET | /api/assignments/{id} | enrolled student / course teacher | - | 200 | 403, 404 |
| PUT | /api/assignments/{id} | course teacher | partial fields | 200 | 403, 404, 422 |
| DELETE | /api/assignments/{id} | course teacher | - | 204 (also deletes files) | 403, 404 |
| POST | /api/assignments/{id}/submit | student | file | 201 new / 200 resubmit or idempotent retry | 403 deadline/not enrolled, 409 graded/resubmission off, 413 too large, 415 bad type, 422 empty, 503 |
| GET | /api/submissions/me | student | - | 200 list | 403 |
| GET | /api/assignments/{id}/submissions | course teacher | - | 200 list | 403, 404 |
| GET | /api/submissions/{id} | owner / course teacher | - | 200 | 403, 404 |
| POST | /api/submissions/{id}/grade | course teacher | `{marks,feedback}` | 200 | 403, 404, 422 marks > max |
| GET | /api/submissions/{id}/feedback | owner / course teacher | - | 200 `{marks,max_marks,feedback,status}` | 403, 404 |
| GET | /api/submissions/{id}/download | owner / course teacher | - | 200 file bytes | 403, 404, 503 |
| GET | /api/submissions/{id}/download-url | owner / course teacher | - | 200 signed URL (S3 only) | 501 on local |
| GET | /api/dashboard/student | student | - | 200 stats | 403 |
| GET | /api/dashboard/teacher | teacher/admin | - | 200 stats | 403 |
| GET | /api/health | public | - | 200 | - |

Example:
```bash
curl -X POST http://localhost:8000/api/login -H "Content-Type: application/json" \
  -d '{"email":"asha@demo.edu","password":"Demo@12345"}'
curl -X POST http://localhost:8000/api/assignments/<ID>/submit -H "Authorization: Bearer <TOKEN>" -F "file=@sample_files/sample_assignment.pdf"
```

## Dashboard queries explained
Student: total = assignments in enrolled courses; submitted = my submission rows; pending = total - submitted; late = `is_late` rows; graded = status GRADED; upcoming = pending with `deadline > now` sorted ascending; recent feedback = graded rows by `graded_at DESC`.
Teacher: assignments of own courses; distinct enrolled students; submissions of those assignments; pending reviews = status != GRADED; late = `is_late`; graded; recent uploads = newest 5; upcoming deadlines.
