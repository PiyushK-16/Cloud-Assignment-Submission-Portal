"""Submission, deadline, grading and file-access logic."""
import hashlib

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.db_models import GRADED, LATE, SUBMITTED, Assignment, Submission, User
from backend.services.assignment_service import can_manage_course, is_enrolled
from backend.utils.errors import ServiceError
from backend.utils.logger import audit, get_logger
from backend.utils.timeutils import utcnow
from backend.utils.validators import new_id, safe_filename, validate_upload
from cloud.storage_service import StorageError, get_storage

log = get_logger(__name__)


def compute_status(submitted_at, deadline) -> str:
    """Deadline rule (server clock, UTC): on/before deadline -> SUBMITTED, after -> LATE."""
    return SUBMITTED if submitted_at <= deadline else LATE


def submit(db: Session, a: Assignment, student: User, filename: str, data: bytes, content_type: str) -> tuple[Submission, bool]:
    """Returns (submission, created). created=False means an update (resubmission) or an idempotent retry."""
    if not is_enrolled(db, a.course_id, student.user_id):
        raise ServiceError(403, "You are not enrolled in this course")

    now = utcnow()  # SERVER timestamp - the client clock is never trusted
    status = compute_status(now, a.deadline)
    if status == LATE and not a.allow_late:
        raise ServiceError(403, "The deadline has passed and late submissions are not allowed")

    allowed = a.allowed_file_types.split(",")
    validate_upload(filename, data, allowed)
    digest = hashlib.sha256(data).hexdigest()

    existing = db.query(Submission).filter_by(assignment_id=a.assignment_id, student_id=student.user_id).first()
    if existing:
        if existing.submission_status == GRADED:
            raise ServiceError(409, "This submission has already been graded and cannot be replaced")
        if not a.allow_resubmission:
            raise ServiceError(409, "Resubmission is not allowed for this assignment")
        if existing.content_hash == digest:
            return existing, False  # idempotent: same file sent again (e.g. network retry) -> no duplicate

    clean = safe_filename(filename)
    path = f"assignments/{a.assignment_id}/{student.user_id}/{new_id()}_{clean}"
    storage = get_storage()
    storage.save(path, data, content_type_for(clean))  # StorageError bubbles up -> HTTP 503 (nothing saved in DB)

    old_path = None
    try:
        if existing:
            old_path = existing.storage_path
            sub, created = existing, False
            sub.attempt_count += 1
        else:
            sub, created = Submission(submission_id=new_id(), assignment_id=a.assignment_id, student_id=student.user_id, attempt_count=1), True
        sub.file_name, sub.storage_path, sub.file_size, sub.content_hash = clean, path, len(data), digest
        sub.file_url = f"/api/submissions/{sub.submission_id}/download"
        sub.submitted_at, sub.submission_status, sub.is_late = now, status, status == LATE
        if created:
            db.add(sub)
        db.commit()
    except IntegrityError:
        db.rollback()
        _safe_delete(storage, path)
        raise ServiceError(409, "A submission for this assignment already exists (duplicate request)")
    except Exception:
        db.rollback()
        _safe_delete(storage, path)  # compensate: do not leave an orphan file if the DB write failed
        raise

    if old_path:
        _safe_delete(storage, old_path)
    audit("submission_saved", submission_id=sub.submission_id, student=student.user_id, status=status)
    return sub, created


def content_type_for(filename: str) -> str:
    from backend.utils.validators import CONTENT_TYPES, extension_of
    return CONTENT_TYPES.get(extension_of(filename), "application/octet-stream")


def _safe_delete(storage, path: str) -> None:
    try:
        storage.delete(path)
    except StorageError as exc:
        log.warning("could not delete %s: %s", path, exc)


def get_submission_for_user(db: Session, submission_id: str, user: User) -> Submission:
    """Central access rule: a student sees ONLY their own; a teacher only submissions in THEIR courses."""
    s = db.get(Submission, submission_id)
    if not s:
        raise ServiceError(404, "Submission not found")
    if user.role == "student":
        if s.student_id != user.user_id:
            raise ServiceError(403, "You can only access your own submissions")
    elif not can_manage_course(s.assignment.course, user):
        raise ServiceError(403, "This submission belongs to a course you do not teach")
    return s


def list_my_submissions(db: Session, student: User) -> list[Submission]:
    return db.query(Submission).filter_by(student_id=student.user_id).order_by(Submission.submitted_at.desc()).all()


def list_for_assignment(db: Session, a: Assignment, teacher: User) -> list[Submission]:
    if not can_manage_course(a.course, teacher):
        raise ServiceError(403, "You do not teach this course")
    return db.query(Submission).filter_by(assignment_id=a.assignment_id).order_by(Submission.submitted_at.desc()).all()


def grade(db: Session, submission_id: str, teacher: User, marks: float, feedback: str) -> Submission:
    s = get_submission_for_user(db, submission_id, teacher)  # also enforces "teacher owns this course"
    if marks > s.assignment.max_marks:
        raise ServiceError(422, f"Marks cannot exceed the maximum ({s.assignment.max_marks})")
    s.marks, s.feedback = marks, feedback.strip()
    s.graded_at, s.graded_by, s.submission_status = utcnow(), teacher.user_id, GRADED
    db.commit()
    audit("submission_graded", submission_id=s.submission_id, by=teacher.user_id, marks=marks)
    return s


def read_file(s: Submission) -> bytes:
    return get_storage().read(s.storage_path)
