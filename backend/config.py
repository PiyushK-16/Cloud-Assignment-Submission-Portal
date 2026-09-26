"""Central configuration. Every secret/credential is read from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.jwt_secret = os.getenv("JWT_SECRET", "")
        self.jwt_expire_minutes = _int("JWT_EXPIRE_MINUTES", 60)
        self.teacher_invite_code = os.getenv("TEACHER_INVITE_CODE", "")

        self.bcrypt_rounds = _int("BCRYPT_ROUNDS", 12)  # lower only in tests

        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./portal.db")

        self.storage_backend = os.getenv("STORAGE_BACKEND", "local")
        self.storage_local_dir = os.getenv("STORAGE_LOCAL_DIR", "./uploads")
        self.s3_bucket = os.getenv("S3_BUCKET", "")
        self.s3_region = os.getenv("S3_REGION", "us-east-1")
        self.s3_endpoint_url = os.getenv("S3_ENDPOINT_URL") or None
        self.s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID") or None
        self.s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY") or None

        self.cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
        self.rate_limit_login_per_min = _int("RATE_LIMIT_LOGIN_PER_MIN", 10)
        self.default_max_file_mb = _int("DEFAULT_MAX_FILE_MB", 10)

        self._validate()

    def _validate(self) -> None:
        if not self.jwt_secret:
            raise RuntimeError("JWT_SECRET is not set. Copy .env.example to .env and set it.")
        if self.app_env == "production" and self.jwt_secret.startswith("change-me"):
            raise RuntimeError("Refusing to start in production with the placeholder JWT_SECRET.")


settings = Settings()
