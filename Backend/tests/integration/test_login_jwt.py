import pytest

from uuid import uuid4

import Backend.services.auth_service as auth_module


from Backend.database.sessions_table import Session as DBSession
from Backend.memory.postgres_memory import (
    PostgresMemory,
    SessionNotFoundError,
)

# ---------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------

@pytest.fixture
def auth_service(test_db, monkeypatch):

    # Prevent real verification emails during testing.
    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    memory = PostgresMemory(
        db=test_db
    )

    return auth_module.AuthService(
        postgres_memory=memory
    )


@pytest.fixture
def registered_user(auth_service):

    identifier = uuid4().hex[:12]

    credentials = {
        "username": f"loginuser{identifier}",
        "email": f"login{identifier}@gmail.com",
        "password": "TestPassword123!"
    }

    user = auth_service.register(
        **credentials
    )

    return {
        "user": user,
        **credentials
    }


def extract_access_token(login_result):
    """
    Support both dictionary and Pydantic token responses.
    """

    if isinstance(login_result, dict):
        return login_result["access_token"]

    return login_result.access_token


# ---------------------------------------------------------
# TEST 1: VALID LOGIN
# ---------------------------------------------------------

@pytest.mark.integration
def test_login_with_correct_credentials(
    auth_service,
    registered_user
):

    result = auth_service.login(
        email=registered_user["email"],
        password=registered_user["password"]
    )

    token = extract_access_token(result)

    assert isinstance(token, str)
    assert len(token) > 0


# ---------------------------------------------------------
# TEST 2: INCORRECT PASSWORD
# ---------------------------------------------------------

@pytest.mark.integration
def test_login_with_wrong_password(
    auth_service,
    registered_user
):

    with pytest.raises(ValueError):

        auth_service.login(
            email=registered_user["email"],
            password="IncorrectPassword123!"
        )


# ---------------------------------------------------------
# TEST 3: UNKNOWN EMAIL
# ---------------------------------------------------------

@pytest.mark.integration
def test_login_with_unknown_email(
    auth_service
):

    email = f"unknown{uuid4().hex[:12]}@gmail.com"

    with pytest.raises(ValueError):

        auth_service.login(
            email=email,
            password="TestPassword123!"
        )


# ---------------------------------------------------------
# TEST 4: JWT IDENTIFIES THE REGISTERED USER
# ---------------------------------------------------------

@pytest.mark.integration
def test_access_token_identifies_correct_user(
    auth_service,
    registered_user
):

    result = auth_service.login(
        email=registered_user["email"],
        password=registered_user["password"]
    )

    token = extract_access_token(result)

    authenticated_user = (
        auth_service.get_current_user(token)
    )

    assert authenticated_user is not None

    assert (
        authenticated_user.id
        == registered_user["user"].id
    )

    assert (
        authenticated_user.email
        == registered_user["email"]
    )


# ---------------------------------------------------------
# TEST 5: USER CANNOT ACCESS ANOTHER USER'S SESSION
# ---------------------------------------------------------
@pytest.mark.integration
def test_session_ownership(
    auth_service,
    test_db,
    registered_user
):
    owner = registered_user["user"]

    identifier = uuid4().hex[:12]

    other_user = auth_service.register(
        username=f"otheruser{identifier}",
        email=f"other{identifier}@gmail.com",
        password="TestPassword123!"
    )

    chat_session = DBSession(
        user_id=owner.id,
        title="Private Test Conversation"
    )

    test_db.add(chat_session)
    test_db.commit()
    test_db.refresh(chat_session)

    memory = PostgresMemory(
        db=test_db
    )

    # Owner can access the session
    owned_session = memory.get_session(
        session_id=chat_session.id,
        user_id=owner.id
    )

    assert owned_session is not None
    assert owned_session.id == chat_session.id

    # Another user cannot access it
    with pytest.raises(
        SessionNotFoundError,
        match="Session not found"
    ):
        memory.get_session(
            session_id=chat_session.id,
            user_id=other_user.id
        )