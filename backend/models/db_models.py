"""SQLAlchemy table definitions (see docs/04-database-storage-design.md for the ER diagram)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.utils.timeutils import utcnow
from backend.utils.validators import new_id
from cloud.database_service import Base

# Submission statuses. NOT_SUBMITTED is derived (no row exists yet).
NOT_SUBMITTED, SUBMITTED, LATE, GRADED = "NOT_SUBMITTED", "SUBMITTED", "LATE", "GRADED"


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10))  # student | teacher | admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Course(Base):
    __tablename__ = "courses"
    course_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_name: Mapped[str] = mapped_column(String(150))
    teacher_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    teacher: Mapped[User] = relationship()


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_enrollment"),)
    enrollment_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.course_id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)


class Assignment(Base):
    __tablename__ = "assignments"
    assignment_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.course_id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[datetime] = mapped_column(DateTime, index=True)  # UTC
    max_marks: Mapped[float] = mapped_column(Float)
    allowed_file_types: Mapped[str] = mapped_column(String(100), default="pdf")
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=10)
    allow_late: Mapped[bool] = mapped_column(Boolean, default=True)  # configurable late policy
    allow_resubmission: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    course: Mapped[Course] = relationship()


class Submission(Base):
    __tablename__ = "submissions"
    # One submission row per (assignment, student): resubmission updates the row.
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_one_submission"),)
    submission_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.assignment_id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(300))  # PRIVATE api path, not a public link
    storage_path: Mapped[str] = mapped_column(String(400))  # key inside the bucket
    file_size: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))  # sha256 -> idempotent retries
    submitted_at: Mapped[datetime] = mapped_column(DateTime)
    submission_status: Mapped[str] = mapped_column(String(15), default=SUBMITTED, index=True)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    graded_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    assignment: Mapped[Assignment] = relationship()
    student: Mapped[User] = relationship(foreign_keys=[student_id])


class RevokedToken(Base):
    """Logout blacklist: a revoked jti can no longer be used even before the JWT expires."""
    __tablename__ = "revoked_tokens"
    jti: Mapped[str] = mapped_column(String(32), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
