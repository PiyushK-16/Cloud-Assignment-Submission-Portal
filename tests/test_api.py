"""Automated backend tests (maps to the 25-case matrix in docs/09-testing.md)."""
from datetime import datetime, timedelta, timezone

from cloud import storage_service
from cloud.database_service import SessionLocal
from backend.models.db_models import Assignment
from tests.conftest import PDF, future, login, register


def upload(client, world, who="a", data=PDF, name="report.pdf"):
    return client.post(f"/api/assignments/{world['asg']['assignment_id']}/submit",
                       headers=world[who], files={"file": (name, data, "application/pdf")})


def make_deadline_passed(assignment_id):
    with SessionLocal() as db:
        a = db.get(Assignment, assignment_id)
        a.deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        db.commit()


# T01 registration / T02 teacher login / T03 invalid login
def test_register_and_login(client):
    assert register(client, "Alice", "alice@example.com").status_code == 201
    assert register(client, "Alice", "alice@example.com").status_code == 409  # duplicate email
    assert client.post("/api/login", json={"email": "alice@example.com", "password": "wrong-pass1"}).status_code == 401
    assert client.post("/api/login", json={"email": "nobody@example.com", "password": "x"}).status_code == 401
    assert client.post("/api/register", json={"name": "Weak", "email": "w@example.com", "password": "short"}).status_code == 422


def test_teacher_needs_invite_code(client):
    r = client.post("/api/register", json={"name": "Fake Teacher", "email": "fake@example.com", "password": "Passw0rd!x", "role": "teacher"})
    assert r.status_code == 403
    assert register(client, "Real Teacher", "t@example.com", "teacher").status_code == 201
    assert "access_token" in client.post("/api/login", json={"email": "t@example.com", "password": "Passw0rd!x"}).json()


# T04 / T05 dashboard authorization
def test_dashboards_are_role_protected(client, world):
    assert client.get("/api/dashboard/teacher", headers=world["a"]).status_code == 403
    assert client.get("/api/dashboard/student", headers=world["t"]).status_code == 403
    assert client.get("/api/dashboard/student", headers=world["a"]).status_code == 200
    assert client.get("/api/dashboard/teacher", headers=world["t"]).status_code == 200
    assert client.get("/api/dashboard/student").status_code == 401  # no token


# T06 / T07 assignment creation + visibility
def test_teacher_creates_and_student_views_assignment(client, world):
    r = client.get("/api/assignments", headers=world["a"])
    assert [x["title"] for x in r.json()] == ["Assignment 1"]
    assert r.json()[0]["my_status"] == "NOT_SUBMITTED"
    # student cannot create; validation rejects bad input
    body = {"course_id": world["course"]["course_id"], "title": "Extra Task", "deadline": future(), "max_marks": 10}
    assert client.post("/api/assignments", headers=world["a"], json=body).status_code == 403
    assert client.post("/api/assignments", headers=world["t"], json={**body, "max_marks": -5}).status_code == 422
    assert client.post("/api/assignments", headers=world["t"], json={**body, "deadline": future(-5)}).status_code == 422
    assert client.post("/api/assignments", headers=world["t"], json={**body, "allowed_file_types": "exe"}).status_code == 422
    # a teacher cannot create assignments in someone else's course
    assert client.post("/api/assignments", headers=world["t2"], json=body).status_code == 403


def test_update_and_delete_assignment(client, world):
    aid = world["asg"]["assignment_id"]
    assert client.put(f"/api/assignments/{aid}", headers=world["t"], json={"title": "Renamed"}).json()["title"] == "Renamed"
    assert client.put(f"/api/assignments/{aid}", headers=world["a"], json={"title": "Hack"}).status_code == 403
    assert client.put(f"/api/assignments/{aid}", headers=world["t2"], json={"title": "Hack"}).status_code == 403
    assert client.delete(f"/api/assignments/{aid}", headers=world["t"]).status_code == 204
    assert client.get(f"/api/assignments/{aid}", headers=world["t"]).status_code == 404


# T08 valid upload / T09 bad extension / T10 oversize
def test_valid_upload(client, world):
    r = upload(client, world)
    assert r.status_code == 201
    assert r.json()["submission_status"] == "SUBMITTED" and r.json()["file_name"] == "report.pdf"
    assert "storage_path" not in r.json()


def test_invalid_extension_and_fake_content(client, world):
    assert upload(client, world, name="virus.exe").status_code == 415
    assert upload(client, world, data=b"this is not a pdf", name="fake.pdf").status_code == 415
    assert upload(client, world, data=b"", name="empty.pdf").status_code == 422


def test_oversized_file(client, world):
    big = b"%PDF" + b"0" * (1024 * 1024 + 10)  # limit is 1 MB
    assert upload(client, world, data=big).status_code == 413


# T11 / T12 on-time vs late, configurable policy
def test_late_submission_allowed_marks_late(client, world):
    make_deadline_passed(world["asg"]["assignment_id"])
    r = upload(client, world)
    assert r.status_code == 201 and r.json()["submission_status"] == "LATE" and r.json()["is_late"] is True


def test_late_submission_blocked_when_policy_disallows(client, world):
    aid = world["asg"]["assignment_id"]
    client.put(f"/api/assignments/{aid}", headers=world["t"], json={"allow_late": False})
    make_deadline_passed(aid)
    assert upload(client, world).status_code == 403


# T13 resubmission + idempotency
def test_resubmission_and_idempotent_retry(client, world):
    first = upload(client, world).json()
    same = upload(client, world)  # identical file -> no new attempt
    assert same.status_code == 200 and same.json()["attempt_count"] == 1
    new = upload(client, world, data=PDF + b"v2")
    assert new.status_code == 200 and new.json()["attempt_count"] == 2
    assert new.json()["submission_id"] == first["submission_id"]
    assert len(client.get("/api/submissions/me", headers=world["a"]).json()) == 1


def test_resubmission_disabled(client, world):
    aid = world["asg"]["assignment_id"]
    client.put(f"/api/assignments/{aid}", headers=world["t"], json={"allow_resubmission": False})
    assert upload(client, world).status_code == 201
    assert upload(client, world, data=PDF + b"v2").status_code == 409


# T14 / T15 own vs others' submissions
def test_student_privacy(client, world):
    sid = upload(client, world, "a").json()["submission_id"]
    assert client.get(f"/api/submissions/{sid}", headers=world["a"]).status_code == 200
    assert client.get(f"/api/submissions/{sid}", headers=world["b"]).status_code == 403
    assert client.get(f"/api/submissions/{sid}/download", headers=world["b"]).status_code == 403
    assert client.get(f"/api/submissions/{sid}/feedback", headers=world["b"]).status_code == 403
    assert client.get(f"/api/submissions/{sid}/download").status_code == 401


# T16 teacher views / T17 grades / T18 marks > max / T19 student views feedback / T20 unauthorized grading
def test_grading_flow(client, world):
    sid = upload(client, world).json()["submission_id"]
    aid = world["asg"]["assignment_id"]
    listing = client.get(f"/api/assignments/{aid}/submissions", headers=world["t"])
    assert listing.status_code == 200 and listing.json()[0]["student_name"] == "Alice Student"
    assert client.get(f"/api/assignments/{aid}/submissions", headers=world["a"]).status_code == 403
    assert client.get(f"/api/assignments/{aid}/submissions", headers=world["t2"]).status_code == 403

    assert client.post(f"/api/submissions/{sid}/grade", headers=world["t"], json={"marks": 101, "feedback": "x"}).status_code == 422
    assert client.post(f"/api/submissions/{sid}/grade", headers=world["t"], json={"marks": -1, "feedback": "x"}).status_code == 422
    assert client.post(f"/api/submissions/{sid}/grade", headers=world["a"], json={"marks": 100, "feedback": "self"}).status_code == 403
    assert client.post(f"/api/submissions/{sid}/grade", headers=world["t2"], json={"marks": 1, "feedback": "x"}).status_code == 403

    ok = client.post(f"/api/submissions/{sid}/grade", headers=world["t"], json={"marks": 88.5, "feedback": "Good work"})
    assert ok.status_code == 200 and ok.json()["submission_status"] == "GRADED"
    fb = client.get(f"/api/submissions/{sid}/feedback", headers=world["a"]).json()
    assert fb["marks"] == 88.5 and fb["feedback"] == "Good work" and fb["max_marks"] == 100
    # graded work cannot be replaced by the student
    assert upload(client, world, data=PDF + b"v2").status_code == 409
    # dashboard reflects it
    d = client.get("/api/dashboard/student", headers=world["a"]).json()
    assert d["graded_assignments"] == 1 and d["recent_feedback"][0]["marks"] == 88.5
    td = client.get("/api/dashboard/teacher", headers=world["t"]).json()
    assert td["total_students"] == 2 and td["graded_submissions"] == 1


# T21 file retrieval
def test_teacher_and_owner_can_download(client, world):
    sid = upload(client, world).json()["submission_id"]
    for who in ("a", "t"):
        r = client.get(f"/api/submissions/{sid}/download", headers=world[who])
        assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
    assert client.get(f"/api/submissions/{sid}/download", headers=world["t2"]).status_code == 403


# T22 cloud-storage failure / T23 database failure
def test_storage_failure_returns_503_and_saves_nothing(client, world, monkeypatch):
    def boom(*a, **k):
        raise storage_service.StorageError("simulated outage")
    monkeypatch.setattr(storage_service.get_storage(), "save", boom)
    assert upload(client, world).status_code == 503
    assert client.get("/api/submissions/me", headers=world["a"]).json() == []


def test_db_failure_cleans_up_uploaded_file(client, world, monkeypatch):
    storage = storage_service.get_storage()
    deleted = []
    real_delete = storage.delete
    monkeypatch.setattr(storage, "delete", lambda p: (deleted.append(p), real_delete(p)))
    from sqlalchemy.orm import Session
    monkeypatch.setattr(Session, "commit", lambda self: (_ for _ in ()).throw(RuntimeError("db down")))
    try:
        upload(client, world)
    except RuntimeError:
        pass  # TestClient re-raises unhandled server errors; production returns a JSON 500
    assert deleted, "orphan file must be removed when the DB write fails"


# T24 logout / T25 protected route after logout
def test_logout_revokes_token(client, world):
    assert client.get("/api/me", headers=world["a"]).status_code == 200
    assert client.post("/api/logout", headers=world["a"]).status_code == 200
    assert client.get("/api/me", headers=world["a"]).status_code == 401
    assert client.get("/api/dashboard/student", headers=world["a"]).status_code == 401


def test_bad_and_tampered_tokens(client):
    assert client.get("/api/me", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
    assert client.get("/api/health").json() == {"status": "ok"}
