from typing import Annotated
from uuid import uuid4

import pytest

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from Backend.api.routes import auth_router
from Backend.api.dependencies.auth import get_current_user
from Backend.database.connection import get_db
from Backend.memory.postgres_memory import PostgresMemory

import Backend.services.auth_service as auth_module


# ---------------------------------------------------------
# TEST APP
# ---------------------------------------------------------

@pytest.fixture
def api_client(
    test_db,
    monkeypatch
):
    """
    Build an isolated FastAPI application containing
    the real authentication routes.

    Database access is redirected to the test database.
    External route-level rate limiting is disabled.
    """

    # -----------------------------------------------------
    # Disable verification email for these tests
    # -----------------------------------------------------

    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    # -----------------------------------------------------
    # Create isolated FastAPI app
    # -----------------------------------------------------

    app = FastAPI()

    app.include_router(
        auth_router
    )

    # -----------------------------------------------------
    # Override database dependency
    # -----------------------------------------------------

    def override_get_db():
        yield test_db

    app.dependency_overrides[
        get_db
    ] = override_get_db

    # -----------------------------------------------------
    # Disable route-level rate-limit dependencies
    #
    # We do not want integration tests using Redis Cloud.
    # Dependencies declared in @router.post(...,
    # dependencies=[...]) have no parameter name.
    # -----------------------------------------------------

    def no_op_dependency():
        return None

    protected_test_paths = {
        "/auth/login",
        "/auth/token",
        "/auth/register",
    }

    for route in app.routes:

        if getattr(
            route,
            "path",
            None
        ) not in protected_test_paths:
            continue

        dependant = getattr(
            route,
            "dependant",
            None
        )

        if dependant is None:
            continue

        for dependency in dependant.dependencies:

            if (
                dependency.name is None
                and dependency.call is not None
            ):
                app.dependency_overrides[
                    dependency.call
                ] = no_op_dependency

    # -----------------------------------------------------
    # Test-only protected endpoint
    #
    # This uses your REAL get_current_user dependency.
    # -----------------------------------------------------

    @app.get(
        "/__test__/protected"
    )
    def protected_endpoint(
        current_user=Depends(
            get_current_user
        )
    ):
        return {
            "id": str(
                current_user.id
            ),
            "email": (
                current_user.email
            )
        }

    client = TestClient(
        app
    )

    yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------
# REGISTERED USER FIXTURE
# ---------------------------------------------------------

@pytest.fixture
def api_registered_user(
    test_db,
    monkeypatch
):

    monkeypatch.setattr(
        auth_module,
        "EMAIL_VERIFICATION_ENABLED",
        False
    )

    memory = PostgresMemory(
        db=test_db
    )

    auth_service = (
        auth_module.AuthService(
            postgres_memory=memory
        )
    )

    identifier = uuid4().hex[:12]

    credentials = {
        "username": (
            f"apiuser{identifier}"
        ),
        "email": (
            f"api{identifier}@gmail.com"
        ),
        "password": (
            "TestPassword123!"
        ),
    }

    user = auth_service.register(
        **credentials
    )

    return {
        "user": user,
        **credentials
    }


# ---------------------------------------------------------
# TEST 1
# FRONTEND JSON LOGIN
# ---------------------------------------------------------

@pytest.mark.integration
def test_json_login_endpoint(
    api_client,
    api_registered_user
):

    response = api_client.post(
        "/auth/login",
        json={
            "email": (
                api_registered_user[
                    "email"
                ]
            ),
            "password": (
                api_registered_user[
                    "password"
                ]
            ),
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body

    assert isinstance(
        body["access_token"],
        str
    )

    assert body[
        "access_token"
    ]

    if "token_type" in body:

        assert (
            body["token_type"].lower()
            == "bearer"
        )


# ---------------------------------------------------------
# TEST 2
# SWAGGER OAUTH2 TOKEN ENDPOINT
# ---------------------------------------------------------

@pytest.mark.integration
def test_oauth2_token_endpoint(
    api_client,
    api_registered_user
):

    response = api_client.post(
        "/auth/token",
        data={
            # OAuth2 calls this field "username",
            # but your application interprets it
            # as the user's email address.
            "username": (
                api_registered_user[
                    "email"
                ]
            ),
            "password": (
                api_registered_user[
                    "password"
                ]
            ),
            "grant_type": "password",
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body

    assert isinstance(
        body["access_token"],
        str
    )

    assert body[
        "access_token"
    ]


# ---------------------------------------------------------
# TEST 3
# JSON LOGIN REJECTS WRONG PASSWORD
# ---------------------------------------------------------

@pytest.mark.integration
def test_json_login_rejects_wrong_password(
    api_client,
    api_registered_user
):

    response = api_client.post(
        "/auth/login",
        json={
            "email": (
                api_registered_user[
                    "email"
                ]
            ),
            "password": (
                "WrongPassword123!"
            ),
        }
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# TEST 4
# OAUTH2 ENDPOINT REJECTS WRONG PASSWORD
# ---------------------------------------------------------

@pytest.mark.integration
def test_oauth2_token_rejects_wrong_password(
    api_client,
    api_registered_user
):

    response = api_client.post(
        "/auth/token",
        data={
            "username": (
                api_registered_user[
                    "email"
                ]
            ),
            "password": (
                "WrongPassword123!"
            ),
            "grant_type": "password",
        }
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# TEST 5
# ACCESS TOKEN WORKS WITH get_current_user
# ---------------------------------------------------------

@pytest.mark.integration
def test_bearer_token_authenticates_user(
    api_client,
    api_registered_user
):

    # First log in.
    login_response = api_client.post(
        "/auth/login",
        json={
            "email": (
                api_registered_user[
                    "email"
                ]
            ),
            "password": (
                api_registered_user[
                    "password"
                ]
            ),
        }
    )

    assert (
        login_response.status_code
        == 200
    )

    access_token = (
        login_response
        .json()[
            "access_token"
        ]
    )

    # Call protected endpoint.
    response = api_client.get(
        "/__test__/protected",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            )
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == (
        api_registered_user[
            "email"
        ]
    )

    assert body["id"] == str(
        api_registered_user[
            "user"
        ].id
    )


# ---------------------------------------------------------
# TEST 6
# INVALID JWT IS REJECTED
# ---------------------------------------------------------

@pytest.mark.integration
def test_invalid_bearer_token_rejected(
    api_client
):

    response = api_client.get(
        "/__test__/protected",
        headers={
            "Authorization": (
                "Bearer definitely-not-a-valid-jwt"
            )
        }
    )

    assert response.status_code == 401


# ---------------------------------------------------------
# TEST 7
# MISSING JWT IS REJECTED
# ---------------------------------------------------------

@pytest.mark.integration
def test_missing_bearer_token_rejected(
    api_client
):

    response = api_client.get(
        "/__test__/protected"
    )

    assert response.status_code in (
        401,
        403,
    )