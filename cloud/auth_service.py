"""
Authentication service: password hashing + signed JWT access tokens.

Authentication = "Who are you?"  (proved by password -> token)
Authorization  = "What may you do?" (enforced in backend/middleware/auth.py)

In a managed setup (Firebase Auth / Supabase Auth / AWS Cognito) this file is replaced by the
provider SDK: the provider issues the JWT and the backend only VERIFIES it. The rest of the app is unchanged.
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.config import settings

ALGORITHM = "HS256"


class AuthError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, role: str) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at_utc_naive). jti lets us revoke the token on logout."""
    jti = uuid.uuid4().hex
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "role": role, "jti": jti, "exp": expires}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, jti, expires.replace(tzinfo=None)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid token") from exc
