"""
Authentication + Role-Based Access Control (RBAC) as FastAPI dependencies.

Every protected route declares WHO may call it, e.g.  Depends(require_role("teacher")).
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.models.db_models import RevokedToken, User
from cloud.auth_service import AuthError, decode_token
from cloud.database_service import get_db

bearer = HTTPBearer(auto_error=False)


def get_token_payload(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> dict:
    if creds is None:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(creds.credentials)
    except AuthError as exc:
        raise HTTPException(401, str(exc), headers={"WWW-Authenticate": "Bearer"})
    if db.get(RevokedToken, payload["jti"]):
        raise HTTPException(401, "Token has been logged out")
    return payload


def get_current_user(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)) -> User:
    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user


def require_role(*roles: str):
    """Authorization gate: 403 if the logged-in user's role is not in `roles`."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"This action requires role: {' or '.join(roles)}")
        return user
    return checker
