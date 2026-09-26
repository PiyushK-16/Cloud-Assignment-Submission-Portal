"""COURSE routes (needed so teachers can own assignments and students can enrol)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.middleware.auth import get_current_user, require_role
from backend.models.db_models import Course, Enrollment, User
from backend.models.schemas import CourseIn
from backend.services import assignment_service as svc
from backend.utils.timeutils import iso
from cloud.database_service import get_db

router = APIRouter(prefix="/api/courses", tags=["courses"])


def _course(c: Course, enrolled: bool | None = None) -> dict:
    d = {"course_id": c.course_id, "course_name": c.course_name, "teacher_id": c.teacher_id,
         "teacher_name": c.teacher.name, "created_at": iso(c.created_at)}
    if enrolled is not None:
        d["enrolled"] = enrolled
    return d


@router.post("", status_code=201)
def create_course(body: CourseIn, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    return _course(svc.create_course(db, teacher, body.course_name))


@router.get("")
def list_courses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Course)
    if user.role == "teacher":
        q = q.filter(Course.teacher_id == user.user_id)
    courses = q.order_by(Course.created_at.desc()).all()
    if user.role == "student":
        mine = {e.course_id for e in db.query(Enrollment).filter_by(student_id=user.user_id)}
        return [_course(c, c.course_id in mine) for c in courses]
    return [_course(c) for c in courses]


@router.post("/{course_id}/enroll", status_code=200)
def enroll(course_id: str, student: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    svc.enroll(db, student, course_id)
    return {"message": "Enrolled", "course_id": course_id}
