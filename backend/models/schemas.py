"""Pydantic request models (validation happens BEFORE any business logic runs)."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"
    invite_code: str | None = None  # required only for the teacher role

    @field_validator("role")
    @classmethod
    def role_ok(cls, v):
        if v not in ("student", "teacher"):
            raise ValueError("role must be 'student' or 'teacher'")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CourseIn(BaseModel):
    course_name: str = Field(min_length=2, max_length=150)


class AssignmentIn(BaseModel):
    course_id: str
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    deadline: datetime
    max_marks: float = Field(gt=0, le=1000)
    allowed_file_types: str = "pdf"
    max_file_size_mb: int = Field(default=10, ge=1, le=50)
    allow_late: bool = True
    allow_resubmission: bool = True


class AssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    deadline: datetime | None = None
    max_marks: float | None = Field(default=None, gt=0, le=1000)
    allowed_file_types: str | None = None
    max_file_size_mb: int | None = Field(default=None, ge=1, le=50)
    allow_late: bool | None = None
    allow_resubmission: bool | None = None


class GradeIn(BaseModel):
    marks: float = Field(ge=0)
    feedback: str = Field(default="", max_length=5000)
