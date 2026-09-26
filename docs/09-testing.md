# 20. Testing Strategy

Run: `pytest` (19 automated tests in `tests/test_api.py`, isolated temp DB + temp storage, dummy data).
**Result recorded on the build machine: `19 passed`.** Re-run on your machine and screenshot it (`screenshots/22-automated-tests-pass.png`). For UI-level confirmation, repeat the scenarios manually using `docs/07-local-setup.md` and note your own observations.

| ID | Scenario | Input | Expected Result | Actual Result (automated) | Pass/Fail |
|---|---|---|---|---|---|
| T01 | Student registration | valid name/email/password | 201; duplicate email -> 409; weak password -> 422 | as expected (`test_register_and_login`) | Pass |
| T02 | Teacher login | teacher with invite code | 201 register; login returns token; no code -> 403 | as expected (`test_teacher_needs_invite_code`) | Pass |
| T03 | Invalid login | wrong password / unknown email | 401 same message | 401 (`test_register_and_login`) | Pass |
| T04 | Student dashboard authorization | student -> /dashboard/teacher; no token | 403; 401 | as expected (`test_dashboards_are_role_protected`) | Pass |
| T05 | Teacher dashboard authorization | teacher -> /dashboard/student | 403; teacher dashboard 200 | as expected | Pass |
| T06 | Teacher creates assignment | valid body; invalid marks/deadline/type; student or other teacher | 201; 422; 403 | as expected (`test_teacher_creates_and_student_views_assignment`) | Pass |
| T07 | Student views assignment | enrolled student GET /assignments | list with `my_status=NOT_SUBMITTED` | as expected | Pass |
| T08 | Valid PDF upload | `report.pdf` (%PDF header) | 201, SUBMITTED, no storage_path leak | as expected (`test_valid_upload`) | Pass |
| T09 | Invalid extension | `virus.exe`; fake `.pdf` with text; empty file | 415; 415; 422 | as expected (`test_invalid_extension_and_fake_content`) | Pass |
| T10 | Oversized file | > 1 MB when limit is 1 MB | 413 | as expected (`test_oversized_file`) | Pass |
| T11 | On-time submission | upload before deadline | status SUBMITTED, `is_late=false` | as expected (`test_valid_upload`) | Pass |
| T12 | Late submission | deadline in the past | LATE (allowed) / 403 (`allow_late=false`) | as expected (`test_late_submission_*`) | Pass |
| T13 | Resubmission | new file; same file again; policy off; after grading | 200 attempt 2; idempotent 200 attempt 1; 409; 409 | as expected (`test_resubmission_*`, `test_grading_flow`) | Pass |
| T14 | Student views own submission | GET own id | 200 | as expected (`test_student_privacy`) | Pass |
| T15 | Student cannot view another's | Bob GET Alice's id (detail/download/feedback) | 403 | as expected | Pass |
| T16 | Teacher views submissions | course teacher; student; other teacher | 200; 403; 403 | as expected (`test_grading_flow`) | Pass |
| T17 | Teacher grades | marks 88.5 + feedback | 200, GRADED | as expected | Pass |
| T18 | Marks above maximum | 101/100; -1 | 422 | as expected | Pass |
| T19 | Student views feedback | GET /feedback | marks + text returned | as expected | Pass |
| T20 | Unauthorized grading | student; other teacher | 403 | as expected | Pass |
| T21 | File retrieval | owner and course teacher download; other teacher | file bytes equal; 403 | as expected (`test_teacher_and_owner_can_download`) | Pass |
| T22 | Cloud-storage failure | storage.save raises | 503, nothing in DB | as expected (`test_storage_failure_returns_503_and_saves_nothing`) | Pass |
| T23 | Database failure | commit raises after upload | uploaded file deleted (no orphan) | as expected (`test_db_failure_cleans_up_uploaded_file`) | Pass |
| T24 | Logout | POST /logout | 200; token revoked | as expected (`test_logout_revokes_token`) | Pass |
| T25 | Protected route after logout | reuse old token | 401 | as expected | Pass |

Extra: `test_update_and_delete_assignment`, `test_bad_and_tampered_tokens`, health check.
Manual/UI tests to add screenshots for: file chooser rejects wrong type, expired-session auto-logout, download button, dashboard numbers.
