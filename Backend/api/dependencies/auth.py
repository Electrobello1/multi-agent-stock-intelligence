from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from Backend.database.connection import get_db
from Backend.memory.postgres_memory import PostgresMemory
from Backend.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


def get_auth_service(
    db: Session = Depends(get_db)
) -> AuthService:
    postgres_memory = PostgresMemory(db)

    return AuthService(
        postgres_memory=postgres_memory
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    try:
        user = auth_service.get_current_user(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials.",
                headers={
                    "WWW-Authenticate": "Bearer"
                }
            )

        return user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )