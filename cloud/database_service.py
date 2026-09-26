"""
Cloud database service.

The SAME code runs on SQLite (local) or managed PostgreSQL (Supabase / Neon / Render / AWS RDS)
by changing only DATABASE_URL. That is the point of an ORM: the app is portable across providers.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str):
    kwargs = {"pool_pre_ping": True}  # drop dead connections (managed DBs close idle ones)
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create tables if they do not exist (use Alembic migrations in a larger project)."""
    from backend.models import db_models  # noqa: F401  (registers tables on Base)

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: one DB session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
