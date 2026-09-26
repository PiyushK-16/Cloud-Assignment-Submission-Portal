"""Turn ORM objects into JSON-safe dicts. Password hashes and storage paths are NEVER exposed to students."""
from backend.models.db_models import NOT_SUBMITTED, Assignment, Submission, User
from backend.utils.timeutils import iso


def user_out(u: User) -> dict:
    return {"user_id": u.user_id, "name": u.name, "email": u.email, "role": u.role, "created_at": iso(u.created_at)}


def assignment_out(a: Assignment, submission: Submission | None = None, submission_count: int | None = None) -> dict:
    d = {
        "assignment_id": a.assignment_id, "course_id": a.course_id, "course_name": a.course.course_name,
        "title": a.title, "description": a.description, "deadline": iso(a.deadline),
        "max_marks": a.max_marks, "allowed_file_types": a.allowed_file_types.split(","),
        "max_file_size_mb": a.max_file_size_mb, "allow_late": a.allow_late,
        "allow_resubmission": a.allow_resubmission, "created_by": a.created_by, "created_at": iso(a.created_at),
        "my_status": submission.submission_status if submission else NOT_SUBMITTED,
    }
    if submission_count is not None:
        d["submission_count"] = submission_count
    return d


def submission_out(s: Submission, include_student: bool = False) -> dict:
    d = {
        "submission_id": s.submission_id, "assignment_id": s.assignment_id,
        "assignment_title": s.assignment.title, "max_marks": s.assignment.max_marks,
        "file_name": s.file_name, "file_url": s.file_url, "file_size": s.file_size,
        "submitted_at": iso(s.submitted_at), "submission_status": s.submission_status,
        "is_late": s.is_late, "attempt_count": s.attempt_count,
        "marks": s.marks, "feedback": s.feedback, "graded_at": iso(s.graded_at),
    }
    if include_student:
        d["student_id"], d["student_name"] = s.student_id, s.student.name
    return d
