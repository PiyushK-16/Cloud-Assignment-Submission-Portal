"""Dashboard aggregates (see docs for the equivalent SQL)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.db_models import GRADED, Assignment, Course, Enrollment, Submission, User
from backend.utils.serializers import assignment_out, submission_out
from backend.utils.timeutils import utcnow


def student_dashboard(db: Session, student: User) -> dict:
    now = utcnow()
    assignments = (
        db.query(Assignment).join(Enrollment, Enrollment.course_id == Assignment.course_id)
        .filter(Enrollment.student_id == student.user_id).all()
    )
    subs = {s.assignment_id: s for s in db.query(Submission).filter_by(student_id=student.user_id).all()}
    pending = [a for a in assignments if a.assignment_id not in subs]
    upcoming = sorted([a for a in pending if a.deadline > now], key=lambda a: a.deadline)[:5]
    graded = sorted([s for s in subs.values() if s.submission_status == GRADED], key=lambda s: s.graded_at, reverse=True)
    return {
        "welcome": f"Welcome, {student.name}",
        "total_assignments": len(assignments),
        "pending_assignments": len(pending),
        "submitted_assignments": len(subs),
        "late_assignments": sum(1 for s in subs.values() if s.is_late),
        "graded_assignments": len(graded),
        "upcoming_deadlines": [assignment_out(a) for a in upcoming],
        "recent_feedback": [submission_out(s) for s in graded[:5]],
    }


def teacher_dashboard(db: Session, teacher: User) -> dict:
    now = utcnow()
    own = db.query(Course.course_id).filter(Course.teacher_id == teacher.user_id) if teacher.role == "teacher" else db.query(Course.course_id)
    assignments = db.query(Assignment).filter(Assignment.course_id.in_(own)).all()
    ids = [a.assignment_id for a in assignments]
    subs_q = db.query(Submission).filter(Submission.assignment_id.in_(ids)) if ids else None
    subs = subs_q.all() if subs_q is not None else []
    students = db.query(func.count(func.distinct(Enrollment.student_id))).filter(Enrollment.course_id.in_(own)).scalar()
    recent = sorted(subs, key=lambda s: s.submitted_at, reverse=True)[:5]
    upcoming = sorted([a for a in assignments if a.deadline > now], key=lambda a: a.deadline)[:5]
    return {
        "welcome": f"Welcome, {teacher.name}",
        "total_assignments": len(assignments),
        "total_students": students or 0,
        "total_submissions": len(subs),
        "pending_reviews": sum(1 for s in subs if s.submission_status != GRADED),
        "late_submissions": sum(1 for s in subs if s.is_late),
        "graded_submissions": sum(1 for s in subs if s.submission_status == GRADED),
        "recent_uploads": [submission_out(s, include_student=True) for s in recent],
        "upcoming_deadlines": [assignment_out(a) for a in upcoming],
    }
