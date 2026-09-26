"""AUTH routes: register, login, logout, me."""
import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.middleware.auth import get_current_user, get_token_payload
from backend.middleware.rate_limit import auth_limiter
from backend.models.db_models import RevokedToken, User
from backend.models.schemas import LoginIn, RegisterIn
from backend.utils.errors import ServiceError
from backend.utils.logger import audit
from backend.utils.serializers import user_out
from backend.utils.timeutils import utcnow
from backend.utils.validators import validate_password
from cloud.auth_service import create_access_token, hash_password, verify_password
from cloud.database_service import get_db

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", status_code=201, dependencies=[Depends(auth_limiter)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    validate_password(body.password)
    if body.role == "teacher":
        # Teachers need the invite code, otherwise anyone could register as a teacher and grade work.
        expected = settings.teacher_invite_code
        if not expected or not hmac.compare_digest(body.invite_code or "", expected):
            raise ServiceError(403, "A valid teacher invite code is required")
    email = body.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise ServiceError(409, "An account with this email already exists")
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    audit("user_registered", user_id=user.user_id, role=user.role)
    return user_out(user)


@router.post("/login", dependencies=[Depends(auth_limiter)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower()).first()
    # Same error for "no such user" and "wrong password" -> no user enumeration
    if not user or not verify_password(body.password, user.password_hash):
        audit("login_failed", email=body.email.lower())
        raise ServiceError(401, "Invalid email or password")
    token, _, _ = create_access_token(user.user_id, user.role)
    audit("login_success", user_id=user.user_id)
    return {"access_token": token, "token_type": "bearer", "user": user_out(user)}


@router.post("/logout")
def logout(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    expires = datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None)
    db.merge(RevokedToken(jti=payload["jti"], expires_at=expires))
    # opportunistic cleanup of expired blacklist rows
    db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete()
    db.commit()
    audit("logout", user_id=payload["sub"])
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)
