# Backend API Documentation

<cite>
**Referenced Files in This Document**
- [apps/api/src/main.py](file://apps/api/src/main.py)
- [apps/api/src/api/v1/router.py](file://apps/api/src/api/v1/router.py)
- [apps/api/src/api/deps.py](file://apps/api/src/api/deps.py)
- [apps/api/src/config.py](file://apps/api/src/config.py)
- [apps/api/src/api/v1/auth.py](file://apps/api/src/api/v1/auth.py)
- [apps/api/src/schemas/auth.py](file://apps/api/src/schemas/auth.py)
- [apps/api/src/services/auth.py](file://apps/api/src/services/auth.py)
- [apps/api/src/models/user.py](file://apps/api/src/models/user.py)
- [apps/api/src/api/v1/brands.py](file://apps/api/src/api/v1/brands.py)
- [apps/api/src/schemas/brand.py](file://apps/api/src/schemas/brand.py)
- [apps/api/src/models/brand.py](file://apps/api/src/models/brand.py)
- [apps/api/src/services/brand.py](file://apps/api/src/services/brand.py)
- [apps/api/src/api/v1/stores.py](file://apps/api/src/api/v1/stores.py)
- [apps/api/src/schemas/store.py](file://apps/api/src/schemas/store.py)
- [apps/api/src/models/store.py](file://apps/api/src/models/store.py)
- [apps/api/src/services/store.py](file://apps/api/src/services/store.py)
- [apps/api/src/api/v1/salespeople.py](file://apps/api/src/api/v1/salespeople.py)
- [apps/api/src/schemas/salesperson.py](file://apps/api/src/schemas/salesperson.py)
- [apps/api/src/models/salesperson.py](file://apps/api/src/models/salesperson.py)
- [apps/api/src/services/salesperson.py](file://apps/api/src/services/salesperson.py)
- [apps/api/src/api/v1/recordings.py](file://apps/api/src/api/v1/recordings.py)
- [apps/api/src/schemas/recording.py](file://apps/api/src/schemas/recording.py)
- [apps/api/src/models/recording.py](file://apps/api/src/models/recording.py)
- [apps/api/src/services/recording.py](file://apps/api/src/services/recording.py)
- [apps/api/src/api/v1/conversations.py](file://apps/api/src/api/v1/conversations.py)
- [apps/api/src/schemas/conversation.py](file://apps/api/src/schemas/conversation.py)
- [apps/api/src/models/conversation.py](file://apps/api/src/models/conversation.py)
- [apps/api/src/services/conversation.py](file://apps/api/src/services/conversation.py)
- [apps/api/src/api/v1/search.py](file://apps/api/src/api/v1/search.py)
- [apps/api/src/services/search.py](file://apps/api/src/services/search.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document describes the Xsamaa AI Pipeline backend API. It covers all RESTful endpoints grouped by functional domains: Authentication, Brand Management, Store Operations, Salesperson Management, Recording Processing, Conversation Analysis, and Search. For each endpoint, you will find HTTP methods, URL patterns, request/response schemas using Pydantic models, authentication requirements, and error responses. It also documents the dependency injection system, request/response validation patterns, error handling strategies, JWT token management, role-based access control, rate limiting considerations, API versioning strategy, and integration guidelines for client applications.

## Project Structure
The backend is a FastAPI application with a modular structure:
- Application entrypoint initializes the ASGI app, CORS middleware, and mounts the API v1 router.
- API v1 groups endpoints by domain (auth, brands, stores, salespeople, recordings, conversations, search).
- Domain routers depend on shared dependency injection helpers for authentication and authorization.
- Services encapsulate business logic and interact with SQLAlchemy async sessions.
- Schemas define request/response models validated by Pydantic.
- Models define ORM entities and relationships.
- Configuration centralizes environment-driven settings including JWT, storage, and NVIDIA integration.

```mermaid
graph TB
A["apps/api/src/main.py<br/>FastAPI app, CORS, include_router"] --> B["apps/api/src/api/v1/router.py<br/>APIRouter(prefix='/api/v1')"]
B --> C["apps/api/src/api/v1/auth.py"]
B --> D["apps/api/src/api/v1/brands.py"]
B --> E["apps/api/src/api/v1/stores.py"]
B --> F["apps/api/src/api/v1/salespeople.py"]
B --> G["apps/api/src/api/v1/recordings.py"]
B --> H["apps/api/src/api/v1/conversations.py"]
B --> I["apps/api/src/api/v1/search.py"]
J["apps/api/src/api/deps.py<br/>get_current_user, RoleChecker"] --> C
J --> D
J --> E
J --> F
J --> G
J --> H
K["apps/api/src/config.py<br/>Settings"] --> A
```

**Diagram sources**
- [apps/api/src/main.py:1-29](file://apps/api/src/main.py#L1-L29)
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)

**Section sources**
- [apps/api/src/main.py:1-29](file://apps/api/src/main.py#L1-L29)
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)

## Core Components
- FastAPI Application: Initializes app metadata, CORS, and mounts the API v1 router. Includes a health endpoint.
- API v1 Router: Prefixes all routes under /api/v1 and includes domain routers.
- Dependency Injection:
  - HTTP Bearer authentication via get_current_user.
  - Role-based access control via RoleChecker with prebuilt checkers for roles.
- Configuration: Centralized settings for database, Redis, JWT, storage, NVIDIA integration, CORS, and app runtime.
- Services: Encapsulate CRUD and analytics operations for each domain.
- Schemas: Pydantic models for request/response validation.
- Models: SQLAlchemy ORM entities with relationships.

**Section sources**
- [apps/api/src/main.py:1-29](file://apps/api/src/main.py#L1-L29)
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)

## Architecture Overview
The backend follows a layered architecture:
- Presentation Layer: FastAPI routers and endpoints.
- Domain Layer: Services implementing business logic.
- Persistence Layer: SQLAlchemy async ORM with Postgres.
- External Integrations: NVIDIA APIs for STT/diarization/LLM/embeddings.
- Security: JWT bearer tokens, bcrypt password hashing, role-based access control.

```mermaid
graph TB
subgraph "Presentation"
R1["Auth Router"]
R2["Brands Router"]
R3["Stores Router"]
R4["Salespeople Router"]
R5["Recordings Router"]
R6["Conversations Router"]
R7["Search Router"]
end
subgraph "Domain Services"
S1["Auth Service"]
S2["Brand Service"]
S3["Store Service"]
S4["Salesperson Service"]
S5["Recording Service"]
S6["Conversation Service"]
S7["Search Service"]
end
subgraph "Persistence"
P1["SQLAlchemy Async Session"]
P2["PostgreSQL"]
end
subgraph "Security"
C1["JWT Config"]
C2["Password Hashing"]
C3["RBAC"]
end
R1 --> S1
R2 --> S2
R3 --> S3
R4 --> S4
R5 --> S5
R6 --> S6
R7 --> S7
S1 --> P1
S2 --> P1
S3 --> P1
S4 --> P1
S5 --> P1
S6 --> P1
S7 --> P1
P1 --> P2
C1 --> S1
C2 --> S1
C3 --> R1
C3 --> R2
C3 --> R3
C3 --> R4
C3 --> R5
C3 --> R6
C3 --> R7
```

**Diagram sources**
- [apps/api/src/main.py:1-29](file://apps/api/src/main.py#L1-L29)
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/services/auth.py:1-55](file://apps/api/src/services/auth.py#L1-L55)
- [apps/api/src/services/brand.py:1-38](file://apps/api/src/services/brand.py#L1-L38)
- [apps/api/src/services/store.py:1-142](file://apps/api/src/services/store.py#L1-L142)
- [apps/api/src/services/salesperson.py](file://apps/api/src/services/salesperson.py)
- [apps/api/src/services/recording.py](file://apps/api/src/services/recording.py)
- [apps/api/src/services/conversation.py](file://apps/api/src/services/conversation.py)
- [apps/api/src/services/search.py](file://apps/api/src/services/search.py)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)

## Detailed Component Analysis

### Authentication
- Purpose: User login, token issuance, token refresh, and logout.
- Endpoints:
  - POST /api/v1/auth/login
    - Request: LoginRequest (email, password)
    - Response: LoginResponse (access_token, refresh_token, user)
    - Validation: Pydantic models enforce field presence and types.
    - Authentication: No prior auth required.
    - Errors: 401 Unauthorized for invalid credentials.
  - POST /api/v1/auth/refresh
    - Request: RefreshRequest (refresh_token)
    - Response: TokenResponse (access_token, refresh_token)
    - Validation: Pydantic models.
    - Authentication: Requires a valid refresh token.
    - Errors: 401 Unauthorized for invalid/expired refresh token.
  - POST /api/v1/auth/logout
    - Response: MessageResponse (message)
    - Notes: Stateless JWT; client discards tokens. Production-grade blocklisting recommended.
- JWT Management:
  - Access token expiry configured via settings.
  - Refresh token expiry configured via settings.
  - Tokens encoded with HS256 and secret key from settings.
- RBAC:
  - Subsequent endpoints use get_current_user and RoleChecker to enforce permissions.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Auth as "Auth Router"
participant Service as "Auth Service"
participant DB as "AsyncSession"
Client->>Auth : POST /api/v1/auth/login
Auth->>Service : authenticate_user(email, password)
Service->>DB : SELECT user WHERE email
DB-->>Service : User
Service-->>Auth : User or None
alt Valid credentials
Auth->>Service : create_access_token(sub)
Auth->>Service : create_refresh_token(sub)
Auth-->>Client : LoginResponse(access_token, refresh_token, user)
else Invalid credentials
Auth-->>Client : 401 Unauthorized
end
```

**Diagram sources**
- [apps/api/src/api/v1/auth.py:24-48](file://apps/api/src/api/v1/auth.py#L24-L48)
- [apps/api/src/services/auth.py:44-49](file://apps/api/src/services/auth.py#L44-L49)

**Section sources**
- [apps/api/src/api/v1/auth.py:1-82](file://apps/api/src/api/v1/auth.py#L1-L82)
- [apps/api/src/schemas/auth.py:1-36](file://apps/api/src/schemas/auth.py#L1-L36)
- [apps/api/src/services/auth.py:1-55](file://apps/api/src/services/auth.py#L1-L55)
- [apps/api/src/models/user.py:1-48](file://apps/api/src/models/user.py#L1-L48)
- [apps/api/src/api/deps.py:12-38](file://apps/api/src/api/deps.py#L12-L38)

### Brand Management
- Purpose: Manage brands (list/create/read/update).
- Endpoints:
  - GET /api/v1/brands
    - Response: List of BrandResponse
    - Authentication: Super Admin required.
  - POST /api/v1/brands
    - Request: BrandCreate (name, description?)
    - Response: BrandResponse
    - Authentication: Brand Admin or Super Admin required.
  - GET /api/v1/brands/{brand_id}
    - Path param: brand_id (UUID string)
    - Response: BrandResponse
    - Authentication: Brand Admin or Super Admin required.
    - Errors: 404 Not Found if brand does not exist.
  - PUT /api/v1/brands/{brand_id}
    - Path param: brand_id (UUID string)
    - Request: BrandUpdate (name?, description?)
    - Response: BrandResponse
    - Authentication: Super Admin required.
    - Errors: 404 Not Found if brand does not exist.
- Validation:
  - Requests validated by Pydantic BrandCreate/BrandUpdate.
  - Responses validated by BrandResponse (from_attributes enabled).
- Error Handling:
  - 404 Not Found for missing resources.

```mermaid
flowchart TD
Start(["GET /brands"]) --> CheckRole["RoleChecker: require_super_admin"]
CheckRole --> |Authorized| List["Service.list_brands()"]
CheckRole --> |Forbidden| Forbidden["403 Forbidden"]
List --> Ok["200 OK with list"]
Forbidden --> End(["End"])
Ok --> End
```

**Diagram sources**
- [apps/api/src/api/v1/brands.py:13-18](file://apps/api/src/api/v1/brands.py#L13-L18)
- [apps/api/src/api/deps.py:55-56](file://apps/api/src/api/deps.py#L55-L56)

**Section sources**
- [apps/api/src/api/v1/brands.py:1-53](file://apps/api/src/api/v1/brands.py#L1-L53)
- [apps/api/src/schemas/brand.py:1-22](file://apps/api/src/schemas/brand.py#L1-L22)
- [apps/api/src/models/brand.py:1-26](file://apps/api/src/models/brand.py#L1-L26)
- [apps/api/src/services/brand.py:1-38](file://apps/api/src/services/brand.py#L1-L38)
- [apps/api/src/api/deps.py:55-56](file://apps/api/src/api/deps.py#L55-L56)

### Store Operations
- Purpose: Manage stores, list with optional filtering, read store details, compute store metrics.
- Endpoints:
  - GET /api/v1/stores
    - Query: brand_id (optional UUID string)
    - Response: List of StoreResponse
    - Authentication: Store Manager Up required.
  - POST /api/v1/stores
    - Request: StoreCreate (name, brand_id, location?, working_hours?)
    - Response: StoreResponse
    - Authentication: Brand Admin or Super Admin required.
  - GET /api/v1/stores/{store_id}
    - Path param: store_id (UUID string)
    - Response: StoreResponse
    - Authentication: Store Manager Up required.
    - Errors: 404 Not Found if store does not exist.
  - GET /api/v1/stores/{store_id}/metrics
    - Path param: store_id (UUID string)
    - Response: StoreMetricsResponse
    - Authentication: Store Manager Up required.
    - Errors: 404 Not Found if store does not exist.
- Metrics:
  - Total salespeople, total recordings, total conversations.
  - Average performance score (average confidence from conversation analysis).
  - Conversion rate (percentage of SALE_MADE outcomes).
  - Top objection (most frequent objection across conversations).
- Validation:
  - Requests validated by StoreCreate/StoreUpdate.
  - Responses validated by StoreResponse and StoreMetricsResponse.
- Error Handling:
  - 404 Not Found for missing stores.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Stores as "Stores Router"
participant Service as "Store Service"
participant DB as "AsyncSession"
Client->>Stores : GET /api/v1/stores/{store_id}/metrics
Stores->>Service : get_store_metrics(store_id)
Service->>DB : SELECT store, counts, avg confidence, conversions, objections
DB-->>Service : Aggregated metrics
Service-->>Stores : StoreMetricsResponse
Stores-->>Client : 200 OK
alt Store not found
Stores-->>Client : 404 Not Found
end
```

**Diagram sources**
- [apps/api/src/api/v1/stores.py:43-52](file://apps/api/src/api/v1/stores.py#L43-L52)
- [apps/api/src/services/store.py:53-141](file://apps/api/src/services/store.py#L53-L141)

**Section sources**
- [apps/api/src/api/v1/stores.py:1-53](file://apps/api/src/api/v1/stores.py#L1-L53)
- [apps/api/src/schemas/store.py:1-38](file://apps/api/src/schemas/store.py#L1-L38)
- [apps/api/src/models/store.py:1-32](file://apps/api/src/models/store.py#L1-L32)
- [apps/api/src/services/store.py:1-142](file://apps/api/src/services/store.py#L1-L142)

### Salesperson Management
- Purpose: Manage salespeople associated with stores.
- Endpoints:
  - GET /api/v1/salespeople
    - Query: store_id (optional UUID string)
    - Response: List of SalespersonResponse
    - Authentication: Salesperson Up required.
  - POST /api/v1/salespeople
    - Request: SalespersonCreate (name, email, store_id, ...)
    - Response: SalespersonResponse
    - Authentication: Brand Admin or Super Admin required.
  - GET /api/v1/salespeople/{salesperson_id}
    - Path param: salesperson_id (UUID string)
    - Response: SalespersonResponse
    - Authentication: Salesperson Up required.
    - Errors: 404 Not Found if salesperson does not exist.
  - PUT /api/v1/salespeople/{salesperson_id}
    - Path param: salesperson_id (UUID string)
    - Request: SalespersonUpdate (...)
    - Response: SalespersonResponse
    - Authentication: Brand Admin or Super Admin required.
    - Errors: 404 Not Found if salesperson does not exist.
- Validation:
  - Requests validated by SalespersonCreate/Update.
  - Responses validated by SalespersonResponse.
- Error Handling:
  - 404 Not Found for missing salespeople.

**Section sources**
- [apps/api/src/api/v1/salespeople.py](file://apps/api/src/api/v1/salespeople.py)
- [apps/api/src/schemas/salesperson.py](file://apps/api/src/schemas/salesperson.py)
- [apps/api/src/models/salesperson.py](file://apps/api/src/models/salesperson.py)
- [apps/api/src/services/salesperson.py](file://apps/api/src/services/salesperson.py)

### Recording Processing
- Purpose: Manage audio recordings linked to salespeople.
- Endpoints:
  - GET /api/v1/recordings
    - Query: salesperson_id (optional UUID string)
    - Response: List of RecordingResponse
    - Authentication: Salesperson Up required.
  - POST /api/v1/recordings
    - Request: RecordingCreate (salesperson_id, file metadata, ...)
    - Response: RecordingResponse
    - Authentication: Brand Admin or Super Admin required.
  - GET /api/v1/recordings/{recording_id}
    - Path param: recording_id (UUID string)
    - Response: RecordingResponse
    - Authentication: Salesperson Up required.
    - Errors: 404 Not Found if recording does not exist.
  - PUT /api/v1/recordings/{recording_id}
    - Path param: recording_id (UUID string)
    - Request: RecordingUpdate (...)
    - Response: RecordingResponse
    - Authentication: Brand Admin or Super Admin required.
    - Errors: 404 Not Found if recording does not exist.
- Validation:
  - Requests validated by RecordingCreate/Update.
  - Responses validated by RecordingResponse.
- Error Handling:
  - 404 Not Found for missing recordings.

**Section sources**
- [apps/api/src/api/v1/recordings.py](file://apps/api/src/api/v1/recordings.py)
- [apps/api/src/schemas/recording.py](file://apps/api/src/schemas/recording.py)
- [apps/api/src/models/recording.py](file://apps/api/src/models/recording.py)
- [apps/api/src/services/recording.py](file://apps/api/src/services/recording.py)

### Conversation Analysis
- Purpose: Manage conversations derived from recordings and analyze insights.
- Endpoints:
  - GET /api/v1/conversations
    - Query: recording_id (optional UUID string)
    - Response: List of ConversationResponse
    - Authentication: Salesperson Up required.
  - GET /api/v1/conversations/{conversation_id}
    - Path param: conversation_id (UUID string)
    - Response: ConversationResponse
    - Authentication: Salesperson Up required.
    - Errors: 404 Not Found if conversation does not exist.
  - GET /api/v1/conversations/{conversation_id}/analysis
    - Path param: conversation_id (UUID string)
    - Response: ConversationAnalysisResponse
    - Authentication: Salesperson Up required.
    - Errors: 404 Not Found if conversation does not exist.
- Validation:
  - Responses validated by ConversationResponse and ConversationAnalysisResponse.
- Error Handling:
  - 404 Not Found for missing conversations.

**Section sources**
- [apps/api/src/api/v1/conversations.py](file://apps/api/src/api/v1/conversations.py)
- [apps/api/src/schemas/conversation.py](file://apps/api/src/schemas/conversation.py)
- [apps/api/src/models/conversation.py](file://apps/api/src/models/conversation.py)
- [apps/api/src/services/conversation.py](file://apps/api/src/services/conversation.py)

### Search Functionality
- Purpose: Provide search capabilities across relevant entities.
- Endpoints:
  - GET /api/v1/search
    - Query: q (search term), type (filter by entity type), limit (optional)
    - Response: List of SearchResult
    - Authentication: Salesperson Up required.
- Validation:
  - Requests validated by SearchRequest (defined in service).
  - Responses validated by SearchResult.
- Error Handling:
  - Standard HTTP errors based on query conditions.

**Section sources**
- [apps/api/src/api/v1/search.py](file://apps/api/src/api/v1/search.py)
- [apps/api/src/services/search.py](file://apps/api/src/services/search.py)

## Dependency Analysis
- Router Composition:
  - API v1 router aggregates domain routers under /api/v1.
- Authentication Dependencies:
  - get_current_user validates bearer token and loads active user.
  - RoleChecker enforces role gates using prebuilt checkers.
- Configuration:
  - Settings provide JWT secrets, expiry, CORS origins, storage, and NVIDIA integration parameters.
- Service Coupling:
  - Services depend on AsyncSession and Pydantic schemas.
  - Services encapsulate SQL queries and aggregations.
- External Integrations:
  - NVIDIA APIs configured via settings; used by AI workers.

```mermaid
graph LR
Main["apps/api/src/main.py"] --> V1["apps/api/src/api/v1/router.py"]
V1 --> AuthR["apps/api/src/api/v1/auth.py"]
V1 --> BrandsR["apps/api/src/api/v1/brands.py"]
V1 --> StoresR["apps/api/src/api/v1/stores.py"]
V1 --> SalespR["apps/api/src/api/v1/salespeople.py"]
V1 --> RecR["apps/api/src/api/v1/recordings.py"]
V1 --> ConvR["apps/api/src/api/v1/conversations.py"]
V1 --> SearchR["apps/api/src/api/v1/search.py"]
AuthR --> Deps["apps/api/src/api/deps.py"]
BrandsR --> Deps
StoresR --> Deps
SalespR --> Deps
RecR --> Deps
ConvR --> Deps
SearchR --> Deps
Deps --> Conf["apps/api/src/config.py"]
AuthR --> AuthSvc["apps/api/src/services/auth.py"]
AuthSvc --> ModelsU["apps/api/src/models/user.py"]
```

**Diagram sources**
- [apps/api/src/main.py:1-29](file://apps/api/src/main.py#L1-L29)
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)
- [apps/api/src/services/auth.py:1-55](file://apps/api/src/services/auth.py#L1-L55)
- [apps/api/src/models/user.py:1-48](file://apps/api/src/models/user.py#L1-L48)

**Section sources**
- [apps/api/src/api/v1/router.py:1-20](file://apps/api/src/api/v1/router.py#L1-L20)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)
- [apps/api/src/config.py:1-52](file://apps/api/src/config.py#L1-L52)

## Performance Considerations
- Asynchronous Database: SQLAlchemy async sessions reduce blocking during I/O.
- Aggregation Queries: Store metrics compute counts and averages efficiently using SQL aggregation.
- Pagination: Consider adding pagination to list endpoints to avoid large payloads.
- Caching: Introduce Redis caching for frequently accessed entities (brands, stores) to reduce DB load.
- Rate Limiting: Implement rate limiting at the gateway or middleware level to protect endpoints.
- Background Processing: Use Celery workers for heavy AI tasks (transcription, diarization, scoring) to keep API responsive.
- Connection Pooling: Configure database connection pool sizes according to expected concurrency.

## Troubleshooting Guide
- Authentication Failures:
  - 401 Unauthorized on auth endpoints indicates invalid credentials or token issues.
  - 401 Unauthorized after login suggests token decoding failure or wrong token type.
  - 403 Forbidden indicates insufficient permissions; verify role requirements.
- Resource Not Found:
  - 404 Not Found for GET endpoints usually means the resource ID does not exist.
- Validation Errors:
  - Pydantic validation errors occur when request fields are missing or mismatched types.
- Health Check:
  - GET /health returns application status and environment.

**Section sources**
- [apps/api/src/api/v1/auth.py:24-48](file://apps/api/src/api/v1/auth.py#L24-L48)
- [apps/api/src/api/v1/auth.py:51-74](file://apps/api/src/api/v1/auth.py#L51-L74)
- [apps/api/src/api/v1/brands.py:36-39](file://apps/api/src/api/v1/brands.py#L36-L39)
- [apps/api/src/api/v1/stores.py:37-41](file://apps/api/src/api/v1/stores.py#L37-L41)
- [apps/api/src/api/deps.py:12-38](file://apps/api/src/api/deps.py#L12-L38)
- [apps/api/src/main.py:26-29](file://apps/api/src/main.py#L26-L29)

## Conclusion
The Xsamaa AI Pipeline backend provides a well-structured, secure, and extensible API surface. It leverages FastAPI’s automatic OpenAPI generation, robust dependency injection, Pydantic validation, and role-based access control. The modular design supports future enhancements such as rate limiting, Redis caching, and Celery-backed asynchronous processing.

## Appendices

### Authentication Flow and RBAC
- JWT Token Lifecycle:
  - Login issues access and refresh tokens with configured expirations.
  - Refresh endpoint renews tokens using a refresh token of specific type.
  - Logout is stateless; clients should discard tokens; consider blocklisting in production.
- Role-Based Access Control:
  - get_current_user loads the active user from the access token.
  - RoleChecker enforces allowed roles per endpoint.
  - Prebuilt checkers:
    - require_super_admin
    - require_brand_admin_up
    - require_store_manager_up
    - require_salesperson_up

```mermaid
sequenceDiagram
participant Client as "Client"
participant Auth as "Auth Router"
participant Service as "Auth Service"
participant RBAC as "RoleChecker"
participant Endpoint as "Domain Endpoint"
Client->>Auth : POST /api/v1/auth/login
Auth->>Service : authenticate_user()
Service-->>Auth : User
Auth-->>Client : LoginResponse
Client->>Endpoint : GET /api/v1/... (with Authorization : Bearer)
Endpoint->>RBAC : require_* role checker
RBAC->>Service : get_user_by_id()
Service-->>RBAC : User
RBAC-->>Endpoint : Authorized User
Endpoint-->>Client : Response
```

**Diagram sources**
- [apps/api/src/api/v1/auth.py:24-48](file://apps/api/src/api/v1/auth.py#L24-L48)
- [apps/api/src/services/auth.py:44-54](file://apps/api/src/services/auth.py#L44-L54)
- [apps/api/src/api/deps.py:12-38](file://apps/api/src/api/deps.py#L12-L38)
- [apps/api/src/api/deps.py:41-51](file://apps/api/src/api/deps.py#L41-L51)

**Section sources**
- [apps/api/src/api/v1/auth.py:1-82](file://apps/api/src/api/v1/auth.py#L1-L82)
- [apps/api/src/services/auth.py:1-55](file://apps/api/src/services/auth.py#L1-L55)
- [apps/api/src/api/deps.py:1-63](file://apps/api/src/api/deps.py#L1-L63)

### API Versioning Strategy
- Versioning: All endpoints are prefixed with /api/v1.
- Migration Plan: Future breaking changes should introduce /api/v2 while maintaining /api/v1 for backward compatibility.

**Section sources**
- [apps/api/src/api/v1/router.py:11-19](file://apps/api/src/api/v1/router.py#L11-L19)

### Integration Guidelines for Client Applications
- Authentication:
  - Use POST /api/v1/auth/login to obtain access and refresh tokens.
  - Attach Authorization: Bearer <access_token> to protected requests.
  - On receiving 401 Unauthorized, use POST /api/v1/auth/refresh with a valid refresh token to renew tokens.
- Error Handling:
  - Clients should parse 400/401/403/404 responses and surface user-friendly messages.
- CORS:
  - Ensure the frontend origin is included in allowed origins.
- Rate Limiting:
  - Implement client-side retries with exponential backoff on 429 responses.
- Health Monitoring:
  - Poll GET /health to verify service availability.

**Section sources**
- [apps/api/src/main.py:15-21](file://apps/api/src/main.py#L15-L21)
- [apps/api/src/api/v1/auth.py:24-48](file://apps/api/src/api/v1/auth.py#L24-L48)
- [apps/api/src/api/v1/auth.py:51-74](file://apps/api/src/api/v1/auth.py#L51-L74)
- [apps/api/src/main.py:26-29](file://apps/api/src/main.py#L26-L29)