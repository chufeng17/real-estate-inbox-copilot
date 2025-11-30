from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings, Settings
from app.core.database import get_db
from app.models import models
from app.schemas import schemas

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_settings() -> Settings:
    return settings


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(models.User).filter(models.User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    return current_user

def get_current_admin_user(
    current_user: models.User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings)
) -> models.User:
    """
    Verify that the current user is an admin.
    For demo purposes, admin is defined by matching ADMIN_EMAIL.
    """
    if current_user.email != settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=403, 
            detail="Admin access required"
        )
    return current_user
