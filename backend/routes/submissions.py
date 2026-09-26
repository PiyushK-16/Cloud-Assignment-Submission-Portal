"""SUBMISSION routes: my submissions, detail, grade, feedback, download."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.middleware.auth import get_current_user, require_role
from backend.models.db_models import User
from backend.models.schemas import GradeIn
from backend.services import submission_service as svc
from backend.utils.errors import ServiceError
from backend.utils.logger import audit
from backend.utils.serializers import submission_out
from backend.utils.validators import CONTENT_TYPES, extension_of
from cloud.storage_service import get_storage
from cloud.database_service import get_db

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.get("/me")
def my_submissions(student: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    return [submission_out(s) for s in svc.list_my_submissions(db, student)]


@router.get("/{submission_id}")
def get_submission(submission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = svc.get_submission_for_user(db, submission_id, user)
    return submission_out(s, include_student=user.role != "student")


@router.post("/{submission_id}/grade")
def grade_submission(submission_id: str, body: GradeIn, teacher: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    return submission_out(svc.grade(db, submission_id, teacher, body.marks, body.feedback), include_student=True)


@router.get("/{submission_id}/feedback")
def get_feedback(submission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = svc.get_submission_for_user(db, submission_id, user)
    return {
        "submission_id": s.submission_id, "status": s.submission_status,
        "marks": s.marks, "max_marks": s.assignment.max_marks,
        "feedback": s.feedback, "graded_at": submission_out(s)["graded_at"],
    }


@router.get("/{submission_id}/download")
def download(submission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Private download: authorization is checked first, then the file is streamed from storage."""
    s = svc.get_submission_for_user(db, submission_id, user)
    data = svc.read_file(s)
    audit("file_downloaded", submission_id=s.submission_id, by=user.user_id)
    ctype = CONTENT_TYPES.get(extension_of(s.file_name), "application/octet-stream")
    return Response(content=data, media_type=ctype, headers={
        "Content-Disposition": f'attachment; filename="{s.file_name}"',
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
    })


@router.get("/{submission_id}/download-url")
def download_url(submission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Optional: short-lived signed URL (S3 backend only) so big files bypass the API server."""
    s = svc.get_submission_for_user(db, submission_id, user)
    url = get_storage().signed_url(s.storage_path, s.file_name, expires=300)
    if not url:
        raise ServiceError(501, "Signed URLs need STORAGE_BACKEND=s3; use /download instead")
    audit("signed_url_issued", submission_id=s.submission_id, by=user.user_id)
    return {"url": url, "expires_in": 300}
