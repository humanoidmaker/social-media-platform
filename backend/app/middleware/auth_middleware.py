"""Authentication middleware and dependencies."""

from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.tokens import decode_access_token

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extract and validate the current user from the JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """Extract the current user ID from the JWT token."""
    return current_user["user_id"]


def require_roles(allowed_roles: List[str]):
    """Create a dependency that checks if the user has one of the allowed roles."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker


require_admin = require_roles(["superadmin", "admin"])
require_creator = require_roles(["superadmin", "admin", "creator"])
require_any_authenticated = require_roles(["superadmin", "admin", "creator", "user"])
