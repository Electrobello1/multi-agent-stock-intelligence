# Multi-Agent Stock Intelligence system

A production-oriented **multi-agent stock analysis and conversational intelligence system** built with **FastAPI, LangGraph, PostgreSQL, pgvector, Redis, local embeddings, and LLM orchestration**.

The system combines deterministic financial-data processing with agentic orchestration, persistent conversational memory, semantic retrieval, authentication, reliability controls, automated testing, and performance engineering.

Unlike a simple chatbot that sends every request directly to an LLM, this application routes user requests through specialized workflows and agents based on intent.

---

## Table of Contents

- [Overview](#overview)
- [Core Capabilities](#core-capabilities)
- [System Architecture](#system-architecture)
- [LangGraph Workflows](#langgraph-workflows)
- [Agent Responsibilities](#agent-responsibilities)
- [Memory Architecture](#memory-architecture)
- [RAG and Vector Search](#rag-and-vector-search)
- [Financial Data Layer](#financial-data-layer)
- [LLM Layer](#llm-layer)
- [Reliability Engineering](#reliability-engineering)
- [Authentication and Authorization](#authentication-and-authorization)
- [Database Architecture](#database-architecture)
- [API Design](#api-design)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Database Migrations](#database-migrations)
- [Running the Application](#running-the-application)
- [Testing Strategy](#testing-strategy)
- [Performance Testing](#performance-testing)
- [Performance Findings](#performance-findings)
- [Security](#security)
- [Observability](#observability)
- [Production Considerations](#production-considerations)
- [Current Limitations](#current-limitations)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

---

# Overview

The Multi-Agent Stock Intelligence Platform is designed to provide three major forms of interaction:

1. **Stock analysis**
2. **Conversational follow-up**
3. **Stock discovery/recommendation**

A user can submit requests such as:

```text
Analyse Tesla
```

```text
Can you explain that further?
```

```text
Recommend some stocks
```

The request is first classified by an **Intent Router**, after which LangGraph dynamically routes execution through the appropriate workflow.

The architecture separates:

- deterministic financial analysis;
- external financial-data retrieval;
- LLM reasoning and report generation;
- conversational memory;
- semantic retrieval;
- persistence;
- reliability controls;
- authentication;
- observability;
- automated testing;
- performance engineering.

This design reduces unnecessary LLM usage and creates a more structured, testable, and production-oriented AI application.

---

# Core Capabilities

## Multi-Agent Orchestration

LangGraph coordinates specialized agents instead of relying on one monolithic AI call.

The system currently supports three primary intents:

```text
REPORT
CHAT
RECOMMEND
```

---

## Financial Analysis

The REPORT workflow combines:

- asset resolution;
- historical market data;
- technical analysis;
- fundamental analysis;
- financial news;
- strategy synthesis;
- LLM report generation;
- persistent memory.

---

## Conversational Intelligence

The CHAT workflow supports follow-up questions using:

- previous messages;
- the latest stock analysis;
- semantic retrieval from stored analyses;
- pgvector similarity search;
- LLM-generated conversational responses.

This allows users to ask follow-up questions without manually repeating the entire previous analysis.

---

## Stock Discovery

The RECOMMEND workflow uses a candidate provider to discover stocks that can be presented to the user for further analysis.

The current candidate provider uses Yahoo Finance-based discovery.

Candidate generation is intentionally separated from full stock analysis so that discovery remains lightweight.

---

## Persistent Memory

The platform maintains durable information across sessions using:

```text
PostgreSQL
Redis
pgvector
```

The system can persist:

- users;
- sessions;
- chat messages;
- stock analyses;
- generated reports;
- semantic embeddings;
- vector-searchable analysis context.

---

# System Architecture

```text
                            Client
                              │
                              ▼
                           FastAPI
                              │
                              ▼
                     JWT Authentication
                              │
                              ▼
                          LangGraph
                              │
                       Intent Router
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
          REPORT             CHAT          RECOMMEND
             │                │                │
             ▼                ▼                ▼
      Asset Resolver    Conversation      Candidate
             │              Memory         Provider
             │                │                │
     ┌───────┼────────┐       ▼                ▼
     │       │        │    LLM Chat      Candidate List
     ▼       ▼        ▼       │                │
  Market Fundamentals News    ▼               END
     │       │        │   Save Response
     └───────┼────────┘       │
             ▼                ▼
          Strategy           END
             │
             ▼
         LLM Report
             │
             ▼
           Memory
             │
      ┌──────┼─────────┐
      ▼      ▼         ▼
 PostgreSQL Redis   pgvector
             │
             ▼
            END
```

---

# LangGraph Workflows

## REPORT Workflow

The REPORT path is used when a user requests a new stock analysis.

```text
START
  │
  ▼
Intent Router
  │
  ▼
REPORT
  │
  ▼
Asset Resolver
  │
  ├──────────────┬──────────────┐
  ▼              ▼              ▼
Market      Fundamentals       News
  │              │              │
  └──────────────┼──────────────┘
                 ▼
              Strategy
                 │
                 ▼
             LLM Report
                 │
                 ▼
               Memory
                 │
                 ▼
                END
```

The three analysis branches execute independently:

```text
Market
Fundamentals
News
```

LangGraph then performs a fan-in:

```python
workflow.add_edge(
    [
        "market",
        "fundamentals",
        "news"
    ],
    "strategy"
)
```

This ensures that the strategy node runs only after all required analysis branches complete.

---

## CHAT Workflow

Conversational requests follow a different route:

```text
START
  │
  ▼
Intent Router
  │
  ▼
CHAT
  │
  ▼
Conversation Memory
  │
  ▼
LLM Chat
  │
  ▼
Save Chat Response
  │
  ▼
END
```

The conversation memory layer retrieves:

- recent chat history;
- latest analysis;
- vector-retrieved semantic context.

This context is then supplied to the chat LLM.

---

## RECOMMEND Workflow

Recommendation requests use a lightweight discovery path:

```text
START
  │
  ▼
Intent Router
  │
  ▼
RECOMMEND
  │
  ▼
Recommendation Candidate Agent
  │
  ▼
Candidate Provider
  │
  ▼
Candidate List
  │
  ▼
END
```

This workflow intentionally avoids expensive market, fundamental, news, and LLM analysis until the user selects or requests deeper analysis.

---

# Agent Responsibilities

## Intent Router

Classifies incoming requests into:

```text
REPORT
CHAT
RECOMMEND
```

It controls which LangGraph branch executes.

---

## Asset Resolver Agent

Converts a user-supplied company or ticker query into a normalized asset representation.

Example output:

```json
{
  "ticker": "TSLA",
  "company_name": "Tesla, Inc."
}
```

The resolver works against an asset master stored in PostgreSQL.

---

## Market Agent

Retrieves historical market data and computes technical indicators.

Current analysis includes indicators such as:

- RSI;
- MACD;
- price history.

---

## Fundamentals Agent

Retrieves and summarizes company fundamental information.

Typical data can include:

- valuation metrics;
- sector;
- company profile;
- financial fundamentals.

---

## News Agent

Retrieves relevant stock/company news for the target asset and produces structured news context.

---

## Strategy Agent

Combines:

```text
Market Analysis
+
Fundamentals
+
News
```

into a higher-level strategy view containing investment-relevant strengths, risks, and observations.

---

## LLM Agent

The LLM agent generates:

- final stock-analysis reports;
- conversational answers.

The application currently uses an Ollama Cloud model for generation.

LLM output is validated and written only to the relevant LangGraph state key:

```python
{
    output_key: response
}
```

This avoids accidental full-state overwrites in concurrent LangGraph workflows.

---

## Memory Agent

Runs after a completed REPORT workflow.

It persists:

- query;
- ticker;
- company name;
- market analysis;
- fundamental analysis;
- news analysis;
- strategy analysis;
- generated report.

It also creates a semantic embedding for later retrieval.

---

## Conversation Memory Agent

Prepares memory for follow-up CHAT requests.

It retrieves:

- recent user/assistant messages;
- latest stock analysis;
- semantically related analysis context.

The node returns only the LangGraph fields it owns:

```python
{
    "conversation_history": ...,
    "latest_analysis": ...,
    "retrieved_context": ...
}
```

---

## Recommendation Candidate Agent

Uses the configured candidate provider to discover stock candidates.

Current implementation:

```python
candidates = candidate_provider.get_candidates(
    limit=10
)

return {
    "recommendation_candidates": candidates
}
```

---

# Memory Architecture

The platform uses multiple memory layers because each one solves a different problem.

```text
                MemoryManager
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     PostgreSQL     Redis     VectorMemory
                                │
                                ▼
                             pgvector
```

---

## PostgreSQL Memory

PostgreSQL provides durable storage for:

- users;
- sessions;
- messages;
- analyses;
- vector metadata.

---

## Redis Memory

Redis is used for low-latency memory/cache and operational state.

It is intentionally separated from PostgreSQL so transient data does not need to be permanently persisted.

---

## Vector Memory

Vector memory stores semantic representations of completed analyses.

This allows later queries to retrieve relevant past information based on semantic similarity rather than exact keyword matching.

---

# RAG and Vector Search

The platform implements retrieval-augmented generation using:

```text
BAAI/bge-small-en-v1.5
```

Embeddings are stored in PostgreSQL using:

```text
pgvector
VECTOR(384)
```

The retrieval flow is:

```text
User query
    │
    ▼
EmbeddingService
    │
    ▼
384-dimensional query vector
    │
    ▼
pgvector similarity search
    │
    ▼
Relevant stored analyses
    │
    ▼
ContextBuilder
    │
    ▼
LLM Chat
```

---

## Shared Embedding Service

To prevent the BGE model from being loaded repeatedly for every request, the production application uses a process-level cached embedding service.

Conceptually:

```text
First request
    │
    ▼
Load BGE model
    │
    ▼
Cache EmbeddingService
    │
    ▼
All subsequent requests
    │
    ▼
Reuse existing model
```

This significantly reduces repeated model initialization overhead under concurrent workloads.

---

# Financial Data Layer

The application separates financial providers from agent logic.

This allows:

- provider fallback;
- provider replacement;
- circuit breakers;
- easier testing;
- deterministic mocks.

Providers are responsible for data retrieval, while agents are responsible for analysis and LangGraph state updates.

---

## Asset Master

The application maintains an internal asset master table containing fields such as:

```text
symbol
company_name
exchange
asset_type
```

A synchronization process can populate this table from external reference-ticker data.

The resolver then uses the local asset table to resolve user queries to valid stock symbols.

---

# LLM Layer

LLM generation is intentionally isolated from the deterministic analysis pipeline.

The LLM is used primarily for:

- report synthesis;
- natural-language explanation;
- conversational answers.

It is not responsible for every piece of financial calculation.

---

## LLM Concurrency Control

High-concurrency load testing revealed that external LLM-provider rate limits can become the bottleneck before FastAPI itself.

The production architecture therefore supports application-side concurrency control using a bounded semaphore.

Conceptually:

```text
30 simultaneous chat requests
             │
             ▼
       FastAPI backend
             │
             ▼
       LLM semaphore
       ┌─────┼─────┐
       ▼     ▼     ▼
    LLM 1  LLM 2  LLM 3
             │
             ▼
    Remaining requests wait
```

This prevents an uncontrolled burst of requests from overwhelming the external model provider.

---

# Reliability Engineering

The platform includes or is designed around several production reliability patterns.

## Circuit Breakers

External provider calls can be protected using circuit-breaker logic.

Typical flow:

```text
Agent
  │
  ▼
Circuit Breaker
  │
  ├── healthy ──► External API
  │
  └── open ─────► fallback / controlled failure
```

---

## Retry Handling

External API calls can be retried for transient failures such as:

- timeouts;
- temporary provider failures;
- HTTP 429 responses.

Retries should use bounded retry counts and exponential backoff rather than unlimited retry loops.

---

## Rate Limiting

FastAPI routes are protected against excessive request traffic.

Performance testing is separated into:

```text
Rate-limit testing
```

and:

```text
Backend capacity testing
```

so security controls are not confused with infrastructure limits.

---

## Input Validation

FastAPI and Pydantic validate request structures before LangGraph execution.

For example, the public chat API accepts:

```json
{
  "message": "Analyse Tesla",
  "session_id": "UUID"
}
```

The route converts this into internal LangGraph state:

```python
{
    "query": request.message,
    ...
}
```

---

## Output Validation

LLM responses are validated before being returned to the user.

Guardrails can enforce constraints such as:

- output length;
- expected format;
- missing output handling;
- fallback responses.

---

# Authentication and Authorization

The application implements JWT-based authentication.

Primary authentication flow:

```text
Email + Password
       │
       ▼
POST /auth/login
       │
       ▼
Authentication Service
       │
       ▼
JWT Access Token
       │
       ▼
Authorization: Bearer <token>
```

---

## Swagger OAuth2 Support

Swagger/OpenAPI authentication is supported through:

```text
POST /auth/token
```

using `OAuth2PasswordRequestForm`.

The main frontend can continue using:

```text
POST /auth/login
```

with JSON.

---

## Session Ownership

Users are only allowed to access sessions they own.

Session access is validated using both:

```text
session_id
user_id
```

Unauthorized access raises a controlled session-not-found/authorization failure.

---

# Database Architecture

The application uses PostgreSQL hosted on Supabase.

Primary tables include:

```text
users
sessions
messages
analyses
analysis_vectors
assets
email_verifications
password_reset_tokens
```

---

## User

Stores user authentication and account information.

Typical fields include:

```text
id
username
email
password_hash
is_verified
created_at
last_login
```

Passwords are stored as secure hashes rather than plaintext.

---

## Session

Represents a user's conversation or stock-analysis session.

Typical fields include:

```text
id
user_id
title
ticker
is_deleted
created_at
updated_at
```

---

## Message

Stores conversational messages associated with a session.

Typical data includes:

```text
session_id
user_id
role
content
created_at
```

---

## Analysis

Stores completed structured stock analyses.

Fields include:

```text
id
session_id
ticker
company_name
query
market_analysis
fundamentals_analysis
news_analysis
strategy_analysis
llm_report
created_at
```

Structured analysis components are stored using PostgreSQL JSONB.

---

## AnalysisVector

Stores semantic vectors for completed analyses.

Fields include:

```text
analysis_id
user_id
session_id
embedded_text
embedding VECTOR(384)
created_at
```

---

# API Design

Key endpoints include:

```text
POST /auth/login
POST /auth/token
POST /chat
GET  /health
```

Additional authentication/session endpoints may also be present depending on deployment configuration.

---

## Chat Request

Example:

```json
{
  "message": "Analyse Tesla",
  "session_id": "c5ccd295-3599-43ae-bdfa-5ce9200156fe"
}
```

---

## Authentication Header

```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

---

# Project Structure

A representative structure is:

```text
stockwebapp/
│
├── Backend/
│   │
│   ├── Agents/
│   │   ├── asset_agent.py
│   │   ├── market_agent.py
│   │   ├── fundamental_agent.py
│   │   ├── news_agent.py
│   │   ├── strategy_agent.py
│   │   ├── llm_agent.py
│   │   ├── memory_agent.py
│   │   ├── conversation_agent.py
│   │   ├── intent_agent.py
│   │   └── recommendation_agent.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── dependencies/
│   │   └── exception_handlers.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── user_table.py
│   │   ├── sessions_table.py
│   │   ├── analysis.py
│   │   ├── analysis_vector.py
│   │   ├── email_verification.py
│   │   └── password_reset.py
│   │
│   ├── data_providers/
│   │   └── candidate_provider.py
│   │
│   ├── embeddings/
│   │   ├── embedding_service.py
│   │   └── embedding_provider.py
│   │
│   ├── memory/
│   │   ├── memory_manager.py
│   │   ├── postgres_memory.py
│   │   ├── redis_memory.py
│   │   └── vector_memory.py
│   │
│   ├── models/
│   │   ├── state.py
│   │   └── LLM.py
│   │
│   ├── Routing/
│   │   └── intent.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   └── context_builder.py
│   │
│   ├── tools/
│   │   └── asset_lookup.py
│   │
│   ├── utils/
│   │   └── perf_timer.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   └── performance/
│   │
│   └── graph.py
│
├── alembic/
├── alembic.ini
├── requirements.txt
└── README.md
```

Exact filenames can vary as the project evolves.

---

# Installation

## 1. Clone the Repository

```bash
git clone <repository-url>
cd stockwebapp
```

---

## 2. Create a Virtual Environment

Windows:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Configuration

Create a `.env` file.

Example:

```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256

OLLAMA_API_KEY=...

EMAIL_VERIFICATION_ENABLED=false
```

Performance and connection settings can be configured separately.

Example:

```env
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

LLM_MAX_CONCURRENCY=3
LLM_MAX_RETRIES=2

PERF_TIMING_ENABLED=false
PERF_TEST_MODE=false
```



```gitignore
.env
.env.test
*.key
*.pem
```

---

# Database Migrations

The project uses Alembic for schema migrations.

Apply migrations with:

```bash
alembic upgrade head
```

Generate a migration after model changes:

```bash
alembic revision --autogenerate -m "description"
```

Then review the generated migration before applying it.

---

# Running the Application

Start FastAPI with Uvicorn:

```powershell
py -3.13 -m uvicorn Backend.api.main:app --host 127.0.0.1 --port 8000
```

Development mode can optionally use reload:

```powershell
py -3.13 -m uvicorn Backend.api.main:app --reload
```

---

# Testing Strategy

The project uses pytest and separates tests by scope.

```text
Unit
Integration
E2E
Performance
```

---

## Unit Tests

Unit tests isolate individual agents and services.

Examples include:

- LLM agent output behavior;
- asset agent behavior;
- tool validation.

Run:

```powershell
py -3.13 -m pytest Backend/tests/unit -v
```

---

## Integration Tests

Integration tests verify multiple real components working together.

Coverage includes:

- authentication and user persistence;
- duplicate user protection;
- login;
- JWT validation;
- session ownership;
- HTTP authentication;
- analysis persistence;
- JSONB serialization;
- LangGraph REPORT routing;
- real memory persistence;
- real pgvector embeddings;
- CHAT memory behavior;
- recommendation routing.

Run:

```powershell
py -3.13 -m pytest Backend/tests/integration -v
```

---

## REPORT Integration Test

The REPORT topology test verifies:

```text
Intent Router
→ Asset Resolver
→ Market/Fundamentals/News
→ Strategy
→ LLM Report
→ Memory
→ END
```

It also verifies that the strategy node runs only after all three parallel analysis branches complete.

---

## Real Memory + pgvector Test

The memory integration test verifies:

```text
LangGraph
→ memory_agent
→ PostgresMemory
→ MemoryManager
→ EmbeddingService
→ VectorMemory
→ PostgreSQL
→ pgvector VECTOR(384)
```

The test confirms that both the analysis row and corresponding vector record are persisted.

---

## E2E Tests

End-to-end tests enter the system through FastAPI rather than directly invoking Python functions.

The authenticated REPORT E2E test covers:

```text
HTTP request
    ↓
FastAPI
    ↓
JWT
    ↓
/chat
    ↓
LangGraph
    ↓
REPORT workflow
    ↓
memory
    ↓
PostgreSQL
    ↓
pgvector
    ↓
HTTP response
```

Run:

```powershell
py -3.13 -m pytest Backend/tests/e2e -v
```

---

# Performance Testing

Locust is used for concurrency and load testing.

Install:

```powershell
py -3.13 -m pip install locust
```

Start FastAPI first.

Then run Locust:

```powershell
py -3.13 -m locust `
-f Backend/tests/performance/locustfile.py `
--host http://127.0.0.1:8000
```

---

## Headless Example

```powershell
py -3.13 -m locust `
-f Backend/tests/performance/locustfile.py `
--host http://127.0.0.1:8000 `
--headless `
--users 30 `
--spawn-rate 5 `
--run-time 2m
```

---

## Realistic Session Simulation

To avoid all virtual users hammering the same conversation, the performance suite can create multiple persistent sessions.

Example:

```powershell
py -3.13 -m Backend.tests.performance.create_perf_sessions --count 30
```

Each Locust virtual user is then assigned its own session.

Conceptually:

```text
VU 1  → Session 1
VU 2  → Session 2
VU 3  → Session 3
...
VU 30 → Session 30
```

---

# Performance Findings

Load testing identified several real bottlenecks and led directly to architectural improvements.

## Initial CHAT Baseline

Single-user conversational latency was approximately:

```text
~16–18 seconds
```

Five concurrent users remained stable with zero failures, although tail latency increased.

---

## 10-User Test

At 10 users:

```text
Average latency ≈ 21 seconds
Failures        = 0
```

This showed that the system remained stable but had begun to queue under concurrency.

---

## 30-User Stress Test

The first 30-user test exposed:

```text
SQLAlchemy QueuePool exhaustion
```

with:

```text
pool_size=5
max_overflow=10
```

This allowed a maximum of 15 simultaneous checked-out application connections.

The resulting error was:

```text
sqlalchemy.exc.TimeoutError:
QueuePool limit of size 5 overflow 10 reached,
connection timed out
```

---

## Database Pool Tuning

The SQLAlchemy connection pool was made configurable:

```env
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=15
DB_POOL_TIMEOUT=30
```

The Supabase/Supavisor backend pool was also evaluated separately.

After connection-pool improvements and embedding optimization, performance improved significantly.

A later 30-user run showed approximately:

```text
Median latency   ≈ 5.7 s
Average latency  ≈ 8.0 s
p95              ≈ 15 s
p99              ≈ 19 s
Max              ≈ 20.7 s
```

The application processed substantially more requests than before.

---

## LLM Provider Bottleneck

After database improvements, the next bottleneck became the external LLM provider.

The backend began receiving:

```text
429 Too Many Requests
```

from the Ollama Cloud API.

This demonstrated that the backend could generate outbound LLM requests faster than the provider allowed.

The production response is controlled LLM concurrency and queueing rather than sending every request to the provider simultaneously.

---

# Observability

The application includes optional internal performance timing.

Enable it with:

```powershell
$env:PERF_TIMING_ENABLED="true"
```

Then start FastAPI.

Example performance logs:

```text
PERF step=save_user_message duration_ms=...
PERF step=get_chat_history duration_ms=...
PERF step=get_latest_analysis duration_ms=...
PERF step=retrieve_context duration_ms=...
PERF step=build_context duration_ms=...
PERF step=llm_generate duration_ms=...
PERF step=save_assistant_message duration_ms=...
PERF step=graph_total duration_ms=...
```

This makes it possible to distinguish:

```text
Database latency
Embedding latency
Vector-search latency
LLM latency
Persistence latency
Total graph latency
```

When performance timing is disabled, the instrumentation remains effectively inert.

---

# Security

The platform is designed around backend-controlled database access.

```text
Browser / Client
      │
      ▼
FastAPI
      │
      ▼
Authentication + Authorization
      │
      ▼
PostgreSQL
```



---

## Password Security

Passwords are stored as secure hashes, never plaintext.

Sensitive fields such as:

- `password_hash`;
- password reset tokens;
- email verification tokens;
- email addresses;
- private chat history;

must never be exposed through an unauthenticated database API.

---

## Supabase Row-Level Security

Supabase Security Advisor should be used to detect tables in exposed schemas where Row-Level Security is disabled.

Backend-only tables should be protected through appropriate combinations of:

- RLS;
- revoked `anon` privileges;
- revoked `authenticated` privileges;
- controlled backend database roles.

Typical private tables include:

```text
users
sessions
messages
analyses
analysis_vectors
email_verifications
password_reset_tokens
```

Security policies should be tested after changes to ensure FastAPI backend access remains functional.

---

## Trusted Host Middleware

The application uses trusted-host protections to reject invalid host headers.

This surfaced during E2E testing because FastAPI `TestClient` uses `testserver` by default.

Tests use a trusted host such as:

```text
http://localhost
```

to exercise the full middleware stack correctly.

---

## Rate Limiting

The application uses rate limits to protect sensitive and expensive endpoints.

Load testing distinguishes:

```text
security/rate-limit behavior
```

from:

```text
actual backend capacity
```

Performance-mode configuration should never silently weaken production security.

---

# Production Considerations

## Database Connection Pooling

Application-side SQLAlchemy pooling and Supabase/Supavisor pooling are separate layers.

Example:

```text
FastAPI
   │
   ▼
SQLAlchemy QueuePool
   │
   ▼
Supavisor
   │
   ▼
PostgreSQL
```

Application pool sizing should not simply equal the number of users.

The correct setting depends on:

- simultaneous DB operations;
- transaction duration;
- Supabase compute size;
- pooler mode;
- other services using the same database.

---

## Supavisor

For highly concurrent short database transactions, Supavisor transaction pooling can provide more efficient multiplexing than direct/session-pinned connections.

Application pool size and Supavisor backend pool size should be tuned independently.

---

## LLM Backpressure

Production LLM calls should be guarded by configurable concurrency controls.

Example:

```env
LLM_MAX_CONCURRENCY=3
LLM_MAX_RETRIES=2
```

The correct value depends on provider limits and service tier.

---

## Cold Starts

The platform uses local embedding models.

The first embedding request in a process may require model initialization.

Subsequent requests reuse the shared embedding service.

Cold-start and warm-request performance should therefore be evaluated separately.

---

# Current Limitations

The current platform still has several areas that can be improved.

## Intent Classification

Natural conversational follow-ups must reliably route to CHAT.





---

## External Provider Limits

External financial and LLM providers can impose:

- rate limits;
- request quotas;
- concurrency limits;
- temporary outages.

The application cannot eliminate these external constraints, so provider fallback and backpressure remain important.

---

## LLM Latency

Even with a healthy backend, generation latency remains dependent on the external LLM provider.

---

## Recommendation Scope

The recommendation workflow currently focuses on candidate discovery.

Full multi-agent analysis of all discovered candidates is intentionally not run automatically because it would be expensive and could create unnecessary external API and LLM load.

---

# Roadmap

Potential future improvements include:

- front end
- stronger intent classification;
- multiple LLM provider support;
- automatic provider fallback;
- asynchronous LLM job queues;
- distributed workers;
- Celery/task queues;
- richer stock-screening logic;
- dedicated risk-analysis agents;
- scheduled market scans;
- portfolio tracking;
- watchlists;
- user alerts;
- WebSocket streaming;
- richer observability and tracing;
- OpenTelemetry;
- Prometheus metrics;
- Grafana dashboards;
- structured request IDs;
- CI/CD automation;
- Docker;
- Nginx/reverse proxy deployment;
- increased automated-test coverage;
- LLM evaluation datasets;
- hallucination and factual-consistency evaluation;
- Slack/WhatsApp notifications;
- scheduled recommendation workflows.

---

# Engineering Principles

The project follows several design principles:

### Deterministic logic before LLM reasoning

Financial calculations and data retrieval are handled deterministically.

### Specialized agents over monolithic prompts

Each agent has a focused responsibility.

### Partial state updates

LangGraph nodes return only the state fields they own.

### Explicit synchronization

Parallel branches use explicit fan-in before downstream strategy generation.

### External systems behind abstractions

Providers, memory systems, embeddings, and LLMs are separated from orchestration logic.

### Testability

Dependencies can be injected or mocked without changing production topology.

### Fail safely

External-provider failures, timeouts, throttling, and invalid outputs should fail predictably.

### Measure before optimizing

Locust and internal timing instrumentation are used to identify real bottlenecks rather than relying on assumptions.

---

# Disclaimer

This project is designed to provide AI-powered stock market analysis, investment insights, and decision-support tools for informational and educational purposes only.

All stock analysis, investment recommendations, generated reports, and conversational responses produced by this system do not constitute professional financial or investment advice.

Market conditions can change rapidly, and past performance does not guarantee future results.

All investment decisions and associated risks remain the sole responsibility of the user.
---

## Status

The platform currently includes:

- multi-agent LangGraph orchestration;
- REPORT, CHAT, and RECOMMEND workflows;
- FastAPI backend;
- JWT authentication;
- PostgreSQL persistence;
- Redis integration;
- pgvector semantic memory;
- local BGE embeddings;
- LLM-generated reports and chat;
- candidate discovery;
- database migrations with Alembic;
- unit testing;
- integration testing;
- authenticated E2E testing;
- Locust performance testing;
- internal performance instrumentation;
- connection-pool tuning;
- LLM concurrency/backpressure design.

The project is actively evolving toward a more resilient, observable, and production-ready AI financial intelligence system.


## 👨‍💻 Author

Princewill Bello

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.