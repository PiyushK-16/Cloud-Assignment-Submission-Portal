"""
Create DUMMY demo data (no real people).   Run from the project root:

    python -m backend.utils.seed_data

Demo password for every account: Demo@12345  (local demos only - never use in production!)
"""
from datetime import timedelta

from backend.models.db_models import Assignment, Course, Enrollment, User
from backend.utils.timeutils import utcnow
from cloud.auth_service import hash_password
from cloud.database_service import SessionLocal, init_db

DEMO_PASSWORD = "Demo@12345"


def main() -> None:
    init_db()
    with SessionLocal() as db:
        if db.query(User).filter_by(email="teacher@demo.edu").first():
            print("Demo data already exists - nothing to do.")
            return
        pw = hash_password(DEMO_PASSWORD)
        teacher = User(name="Prof. Demo Teacher", email="teacher@demo.edu", password_hash=pw, role="teacher")
        admin = User(name="Demo Admin", email="admin@demo.edu", password_hash=pw, role="admin")
        students = [User(name=n, email=e, password_hash=pw, role="student") for n, e in
                    [("Asha Student", "asha@demo.edu"), ("Ravi Student", "ravi@demo.edu"), ("Meera Student", "meera@demo.edu")]]
        db.add_all([teacher, admin, *students])
        db.flush()
        course = Course(course_name="Cloud Computing (Demo)", teacher_id=teacher.user_id)
        db.add(course)
        db.flush()
        db.add_all([Enrollment(course_id=course.course_id, student_id=s.user_id) for s in students])
        db.add_all([
            Assignment(course_id=course.course_id, title="Assignment 1: IaaS vs PaaS vs SaaS", description="Write a 2-page comparison with examples.",
                       deadline=utcnow() + timedelta(days=7), max_marks=100, allowed_file_types="pdf,docx", max_file_size_mb=10, created_by=teacher.user_id),
            Assignment(course_id=course.course_id, title="Assignment 2: Object Storage Lab", description="Submit a ZIP of your lab screenshots.",
                       deadline=utcnow() + timedelta(days=14), max_marks=50, allowed_file_types="pdf,zip", max_file_size_mb=20, created_by=teacher.user_id),
        ])
        db.commit()
    print("Seeded demo data. Accounts (password Demo@12345): teacher@demo.edu, admin@demo.edu, asha@demo.edu, ravi@demo.edu, meera@demo.edu")


if __name__ == "__main__":
    main()
