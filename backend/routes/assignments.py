"""ASSIGNMENT routes (teacher CRUD; students read) + the submit and list-submissions endpoints."""
from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from backend.middleware.auth import get_current_user, require_role
from backend.models.db_models import User
from backend.models.schemas import AssignmentIn, AssignmentUpdate
from backend.services import assignment_service as svc
from backend.services import submission_service as subs
from backend.utils.errors import ServiceError
from backend.utils.serializers import assignment_out, submission_out
from cloud.database_service import get_db

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", status_code=201)
def create_assignment(body: AssignmentIn, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    return assignment_out(svc.create_assignment(db, teacher, body))


@router.get("")
def list_assignments(course_id: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [assignment_out(a, sub, count) for a, sub, count in svc.list_assignments(db, user, course_id)]


@router.get("/{assignment_id}")
def get_assignment(assignment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = svc.get_viewable_assignment(db, assignment_id, user)
    return assignment_out(a)


@router.put("/{assignment_id}")
def update_assignment(assignment_id: str, body: AssignmentUpdate, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    return assignment_out(svc.update_assignment(db, teacher, assignment_id, body))


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: str, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    svc.delete_assignment(db, teacher, assignment_id)
    return Response(status_code=204)


@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str, response: Response, file: UploadFile = File(...),
    student: User = Depends(require_role("student")), db: Session = Depends(get_db),
):
    a = svc.get_viewable_assignment(db, assignment_id, student)
    limit = a.max_file_size_mb * 1024 * 1024
    data = await file.read(limit + 1)  # never read more than limit+1 bytes into memory
    if len(data) > limit:
        raise ServiceError(413, f"File is larger than the {a.max_file_size_mb} MB limit")
    sub, created = subs.submit(db, a, student, file.filename or "file", data, file.content_type or "")
    response.status_code = 201 if created else 200
    return submission_out(sub)


@router.get("/{assignment_id}/submissions")
def assignment_submissions(assignment_id: str, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    a = svc.get_managed_assignment(db, assignment_id, teacher)
    return [submission_out(s, include_student=True) for s in subs.list_for_assignment(db, a, teacher)]
