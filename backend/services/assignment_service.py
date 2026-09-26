"""Assignment + course business logic (authorization checks live here so every route reuses them)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.db_models import Assignment, Course, Enrollment, Submission, User
from backend.models.schemas import AssignmentIn, AssignmentUpdate
from backend.utils.errors import ServiceError
from backend.utils.logger import audit, get_logger
from backend.utils.timeutils import to_utc_naive, utcnow
from backend.utils.validators import parse_allowed_types
from cloud.storage_service import StorageError, get_storage

log = get_logger(__name__)


# ---------- access control helpers ----------
def can_manage_course(course: Course, user: User) -> bool:
    return user.role == "admin" or (user.role == "teacher" and course.teacher_id == user.user_id)


def is_enrolled(db: Session, course_id: str, student_id: str) -> bool:
    return db.query(Enrollment).filter_by(course_id=course_id, student_id=student_id).first() is not None


def get_assignment_or_404(db: Session, assignment_id: str) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a:
        raise ServiceError(404, "Assignment not found")
    return a


def get_viewable_assignment(db: Session, assignment_id: str, user: User) -> Assignment:
    a = get_assignment_or_404(db, assignment_id)
    if user.role == "student":
        if not is_enrolled(db, a.course_id, user.user_id):
            raise ServiceError(403, "You are not enrolled in this course")
    elif not can_manage_course(a.course, user):
        raise ServiceError(403, "You do not have access to this course")
    return a


def get_managed_assignment(db: Session, assignment_id: str, user: User) -> Assignment:
    a = get_assignment_or_404(db, assignment_id)
    if not can_manage_course(a.course, user):
        raise ServiceError(403, "You can only manage assignments in your own courses")
    return a


# ---------- courses ----------
def create_course(db: Session, teacher: User, name: str) -> Course:
    course = Course(course_name=name.strip(), teacher_id=teacher.user_id)
    db.add(course)
    db.commit()
    return course


def enroll(db: Session, student: User, course_id: str) -> None:
    if not db.get(Course, course_id):
        raise ServiceError(404, "Course not found")
    if is_enrolled(db, course_id, student.user_id):
        return  # idempotent
    db.add(Enrollment(course_id=course_id, student_id=student.user_id))
    db.commit()


# ---------- assignments ----------
def create_assignment(db: Session, teacher: User, data: AssignmentIn) -> Assignment:
    course = db.get(Course, data.course_id)
    if not course:
        raise ServiceError(404, "Course not found")
    if not can_manage_course(course, teacher):
        raise ServiceError(403, "You can only create assignments in your own courses")
    deadline = to_utc_naive(data.deadline)
    if deadline <= utcnow():
        raise ServiceError(422, "Deadline must be in the future")
    types = parse_allowed_types(data.allowed_file_types)
    a = Assignment(
        course_id=course.course_id, title=data.title.strip(), description=data.description,
        deadline=deadline, max_marks=data.max_marks, allowed_file_types=",".join(types),
        max_file_size_mb=data.max_file_size_mb, allow_late=data.allow_late,
        allow_resubmission=data.allow_resubmission, created_by=teacher.user_id,
    )
    db.add(a)
    db.commit()
    audit("assignment_created", assignment_id=a.assignment_id, by=teacher.user_id)
    return a


def update_assignment(db: Session, teacher: User, assignment_id: str, data: AssignmentUpdate) -> Assignment:
    a = get_managed_assignment(db, assignment_id, teacher)
    changes = data.model_dump(exclude_unset=True)
    if "deadline" in changes and changes["deadline"] is not None:
        a.deadline = to_utc_naive(changes.pop("deadline"))
    if "allowed_file_types" in changes and changes["allowed_file_types"] is not None:
        a.allowed_file_types = ",".join(parse_allowed_types(changes.pop("allowed_file_types")))
    if changes.get("max_marks") is not None:
        top = db.query(func.max(Submission.marks)).filter_by(assignment_id=a.assignment_id).scalar()
        if top is not None and changes["max_marks"] < top:
            raise ServiceError(422, f"max_marks cannot be lower than marks already awarded ({top})")
    for field, value in changes.items():
        if value is not None:
            setattr(a, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    audit("assignment_updated", assignment_id=a.assignment_id, by=teacher.user_id)
    return a


def delete_assignment(db: Session, teacher: User, assignment_id: str) -> None:
    a = get_managed_assignment(db, assignment_id, teacher)
    storage = get_storage()
    for s in db.query(Submission).filter_by(assignment_id=a.assignment_id).all():
        try:
            storage.delete(s.storage_path)
        except StorageError as exc:  # do not block deletion; orphan cleanup job can retry
            log.warning("orphan file left in storage: %s (%s)", s.storage_path, exc)
        db.delete(s)
    db.delete(a)
    db.commit()
    audit("assignment_deleted", assignment_id=assignment_id, by=teacher.user_id)


def list_assignments(db: Session, user: User, course_id: str | None = None) -> list[dict]:
    """Returns rows shaped for the dashboard: (assignment, my_submission | submission_count)."""
    q = db.query(Assignment).join(Course)
    if course_id:
        q = q.filter(Assignment.course_id == course_id)
    if user.role == "student":
        q = q.join(Enrollment, Enrollment.course_id == Assignment.course_id).filter(Enrollment.student_id == user.user_id)
    elif user.role == "teacher":
        q = q.filter(Course.teacher_id == user.user_id)
    rows = q.order_by(Assignment.deadline.asc()).all()
    result = []
    for a in rows:
        if user.role == "student":
            sub = db.query(Submission).filter_by(assignment_id=a.assignment_id, student_id=user.user_id).first()
            result.append((a, sub, None))
        else:
            count = db.query(func.count(Submission.submission_id)).filter_by(assignment_id=a.assignment_id).scalar()
            result.append((a, None, count))
    return result
