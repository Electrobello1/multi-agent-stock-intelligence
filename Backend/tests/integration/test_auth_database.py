import pytest

from uuid import uuid4

from Backend.memory.postgres_memory import PostgresMemory

import Backend.services.auth_service as auth_module


@pytest.fixture
def auth_service(test_db, monkeypatch):

    # Disable external verification emails during this test.
    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    postgres_memory = PostgresMemory(
        db=test_db
    )

    return auth_module.AuthService(
        postgres_memory=postgres_memory
    )


def unique_user():

    identifier = uuid4().hex[:12]

    return {
        "username": f"testuser{identifier}",
        "email": f"test{identifier}@gmail.com",
        "password": "TestPassword123!"
    }


# ---------------------------------------------------------
# TEST 1: Successful registration
# ---------------------------------------------------------

@pytest.mark.integration
def test_user_registration(
    auth_service,
    test_db
):

    data = unique_user()

    user = auth_service.register(
        username=data["username"],
        email=data["email"],
        password=data["password"]
    )

    assert user is not None
    assert user.id is not None
    assert user.email == data["email"]

    # Confirm that the actual database contains the user.
    memory = PostgresMemory(db=test_db)

    stored_user = memory.get_user_by_email(
        data["email"]
    )

    assert stored_user is not None
    assert stored_user.id == user.id

    # Because verification is disabled for this test.
    assert stored_user.is_verified is True

    # Confirm the application did not store a plain password.
    assert stored_user.password_hash != data["password"]


# ---------------------------------------------------------
# TEST 2: Duplicate email rejection
# ---------------------------------------------------------

@pytest.mark.integration
def test_duplicate_email_rejected(auth_service):

    data = unique_user()

    auth_service.register(**data)

    with pytest.raises(
        ValueError,
        match="Email is already registered"
    ):

        auth_service.register(
            username="anotheruser" + uuid4().hex[:8],
            email=data["email"],
            password=data["password"]
        )


# ---------------------------------------------------------
# TEST 3: Duplicate username rejection
# ---------------------------------------------------------

@pytest.mark.integration
def test_duplicate_username_rejected(auth_service):

    data = unique_user()

    auth_service.register(**data)

    with pytest.raises(
        ValueError,
        match="Username is already taken"
    ):

        auth_service.register(
            username=data["username"],
            email=f"another{uuid4().hex[:12]}@gmail.com",
            password=data["password"]
        )