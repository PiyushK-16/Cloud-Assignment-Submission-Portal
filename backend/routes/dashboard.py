"""DASHBOARD routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.middleware.auth import require_role
from backend.models.db_models import User
from backend.services import dashboard_service as svc
from cloud.database_service import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/student")
def student(user: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    return svc.student_dashboard(db, user)


@router.get("/teacher")
def teacher(user: User = Depends(require_role("teacher", "admin")), db: Session = Depends(get_db)):
    return svc.teacher_dashboard(db, user)
