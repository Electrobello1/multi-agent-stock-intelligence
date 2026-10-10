import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from Backend.api.routes import (
    auth_router,
    session_router,
    chat_router
)

from Backend.api.exception_handlers import (
    register_exception_handlers
)

from Backend.api.security.security_headers import (
    SecurityHeadersMiddleware
)


app = FastAPI(
    title="Stock Analysis AI API",
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000"
).split(",")

cors_origins = [
    origin.strip()
    for origin in cors_origins
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type"
    ]
)


# ---------------------------------------------------------
# Trusted Hosts
# ---------------------------------------------------------

allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")

allowed_hosts = [
    host.strip()
    for host in allowed_hosts
    if host.strip()
]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)


# ---------------------------------------------------------
# Security Headers
# ---------------------------------------------------------

app.add_middleware(
    SecurityHeadersMiddleware
)


# ---------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(auth_router)
app.include_router(session_router)
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }

