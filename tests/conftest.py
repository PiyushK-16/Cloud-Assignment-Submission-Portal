"""Test setup: isolated temp DB + temp storage; all secrets are dummy test values."""
import os
import tempfile
from datetime import datetime, timedelta, timezone

_tmp = tempfile.mkdtemp()
os.environ.update({
    "APP_ENV": "test", "JWT_SECRET": "test-secret-not-for-production-0123456789",
    "TEACHER_INVITE_CODE": "TEACH-TEST", "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
    "STORAGE_BACKEND": "local", "STORAGE_LOCAL_DIR": f"{_tmp}/uploads",
    "RATE_LIMIT_LOGIN_PER_MIN": "1000", "BCRYPT_ROUNDS": "4",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402
from cloud.database_service import Base, engine  # noqa: E402

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:  # startup event creates tables
        yield c


def register(client, name, email, role="student", pw="Passw0rd!x"):
    body = {"name": name, "email": email, "password": pw, "role": role}
    if role == "teacher":
        body["invite_code"] = "TEACH-TEST"
    return client.post("/api/register", json=body)


def login(client, email, pw="Passw0rd!x"):
    r = client.post("/api/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def world(client):
    """Teacher + course + assignment + two enrolled students (all dummy data)."""
    register(client, "Dr. Test Teacher", "teacher@example.com", "teacher")
    register(client, "Other Teacher", "teacher2@example.com", "teacher")
    register(client, "Alice Student", "alice@example.com")
    register(client, "Bob Student", "bob@example.com")
    t, t2 = login(client, "teacher@example.com"), login(client, "teacher2@example.com")
    a, b = login(client, "alice@example.com"), login(client, "bob@example.com")
    course = client.post("/api/courses", json={"course_name": "Cloud Computing 101"}, headers=t).json()
    for h in (a, b):
        assert client.post(f"/api/courses/{course['course_id']}/enroll", headers=h).status_code == 200
    asg = client.post("/api/assignments", headers=t, json={
        "course_id": course["course_id"], "title": "Assignment 1", "description": "Write a report",
        "deadline": future(24), "max_marks": 100, "allowed_file_types": "pdf,txt", "max_file_size_mb": 1,
    })
    assert asg.status_code == 201, asg.text
    return {"t": t, "t2": t2, "a": a, "b": b, "course": course, "asg": asg.json()}
