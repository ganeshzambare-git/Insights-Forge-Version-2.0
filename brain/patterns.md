# Patterns — Insight Forge V2

> Approved implementation patterns. Follow these for all new code.
> Last updated: 2026-07-10

## Repository Pattern

**Location:** `app/repositories/base.py`

Repositories are stateless data access objects. They never commit or rollback transactions.

```python
class BaseRepository(Generic[T]):
    async def get_by_id(self, id: UUID) -> T | None: ...
    async def list(self, *, skip: int = 0, limit: int = 100) -> list[T]: ...
    async def create(self, entity: T) -> T: ...
    async def update(self, entity: T) -> T: ...
    async def delete(self, id: UUID) -> bool: ...
```

**Rules:**
- One repository per entity
- No business logic in repositories
- No transaction management
- Queries are tenant-scoped via RLS (no manual tenant filtering needed when context is set)

## Unit of Work Pattern

**Location:** `app/services/uow.py`

Services use UoW for transaction boundaries:

```python
async with self._uow:
    entity = await self._repo.create(new_entity)
    await self._audit.log_succeeded("create_user", entity.id)
    return ServiceResult.ok(entity)
# auto-commit on clean exit, auto-rollback on exception
```

**Rules:**
- All write operations (commands) go through UoW
- Read operations (queries) do not need UoW
- One UoW per service method invocation

## Command vs Query Pattern

**Location:** `app/services/base.py`

```python
# Commands — mutate state, return ServiceResult
async def create_user(self, data: CreateUserDTO) -> ServiceResult[User]:
    return await self.execute_command(self._do_create, data)

# Queries — read state, return entities directly
async def get_user(self, user_id: UUID) -> User | None:
    return await self._repo.get_by_id(user_id)
```

**ServiceResult structure:**
```python
@dataclass
class ServiceResult(Generic[T]):
    success: bool
    entity: T | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)
```

## Dependency Injection Pattern

**Location:** `app/dependencies/services.py`, `app/dependencies/auth.py`

```python
# Service factory
@router.post("/users")
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
    _roles: None = Depends(RequireRoles(Role.ADMIN)),
):
    result = await service.create_user(data)
    return api_response(data=result.entity, message=result.message)
```

**Rules:**
- Never instantiate services directly in endpoints
- Auth guards are dependencies, not inline checks
- `ServiceContext` bundles session, UoW, audit logger, providers

## API Response Envelope Pattern

**Location:** `app/utils/response.py`

All API responses use a standard envelope:

```python
def api_response(
    data: Any = None,
    message: str = "Success",
    success: bool = True,
    meta: dict | None = None,
    errors: list[str] | None = None,
) -> JSONResponse:
```

**Response shape:**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": { ... },
  "meta": { "page": 1, "total": 50 },
  "errors": []
}
```

## Audit Logging Pattern

**Location:** `app/services/audit.py`

Every service command logs its lifecycle:

```python
await self._audit.log_started("create_user", {"email": data.email})
# ... operation ...
await self._audit.log_succeeded("create_user", entity.id)
# or on failure:
await self._audit.log_failed("create_user", str(error))
```

## Service Exception Pattern

**Location:** `app/services/exceptions.py`, mapped in `app/main.py`

Domain exceptions are raised in services, mapped to HTTP status in exception handlers:

| Exception | HTTP Status |
|-----------|-------------|
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `ValidationError` | 422 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |

**Rules:**
- Services raise domain exceptions, never HTTPException
- Endpoints do not catch exceptions (global handlers do)

## Authentication Pattern

**Flow:**
1. `POST /api/v1/auth/login` with `corporate_email` + password
2. Receive `access_token` (15 min) + `refresh_token` (7 days)
3. Include `Authorization: Bearer <access_token>` on requests
4. Include `X-Tenant-ID: <uuid>` if not embedded in JWT
5. Refresh via `POST /api/v1/auth/refresh` with refresh token
6. Logout via `POST /api/v1/auth/logout` (invalidates JTI)

**Token storage:** JTI in database, not raw tokens. Rotation on refresh.

## RBAC Pattern

**Location:** `app/core/roles.py`, `app/dependencies/auth.py`

```python
class Role(str, Enum):
    ADMIN = "Admin"
    DEAN = "Dean"
    FACULTY = "Faculty"
    STUDENT = "Student"

# Usage in endpoints:
_roles: None = Depends(RequireRoles(Role.ADMIN, Role.DEAN))
```

**Role hierarchy (implicit):** Admin > Dean > Faculty > Student. Each endpoint declares required roles explicitly.

## AI Agent Pattern

**Location:** `app/ai/contracts/agent.py`, `app/ai/context/model.py`

```python
class BaseAIAgent(ABC):
    async def execute(self, context: AIContext) -> AgentResponse: ...

# Context is immutable — evolve, don't mutate:
new_context = context.evolve(
    stage="data_analysis",
    insights=analysis_results,
)
```

**Orchestration:** Sequential pipeline, each agent receives evolved context from previous agent.

## LLM Provider Pattern

**Location:** `app/ai/llm/provider.py`

```python
class BaseLLMProvider(ABC):
    async def generate(self, prompt: str, schema: type[T]) -> T: ...

# Default: mock provider returning structured test data
class DefaultLLMProvider(BaseLLMProvider):
    async def generate(self, prompt: str, schema: type[T]) -> T:
        return schema.model_validate({...})  # mock data
```

**To add a real provider:** Implement `BaseLLMProvider`, inject in `AIService`.

## Provider Injection Pattern

**Location:** `app/services/providers.py`

Swappable providers for testing:

```python
class ClockProvider(Protocol):
    def now(self) -> datetime: ...

class UUIDProvider(Protocol):
    def generate(self) -> UUID: ...
```

Injected via `ServiceContext` — use real implementations in production, mocks in tests.

## Database Migration Pattern

**Location:** `migrations/`

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Rules:**
- One migration per logical change
- Always include RLS policies for new tenant-scoped tables
- Use `EncryptedString` for PII/sensitive fields
- UUID primary keys on all tables

## Testing Pattern

**Location:** `tests/`

```python
# Unit tests mock repositories and providers
@pytest.fixture
def mock_user_repo():
    return AsyncMock(spec=UserRepository)

# Integration tests use real DB (test_docker_setup.py)
```

**Conventions:**
- Test files mirror source: `test_auth.py` for `auth.py`
- Use `pytest` fixtures from `conftest.py`
- Mock external dependencies (LLM, clock, UUID)
- Test service commands AND queries separately

## PATCH Update Pattern

**Never use PUT.** Always PATCH for partial updates:

```python
@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    data: UpdateUserRequest,  # all fields optional
    ...
):
```

Protects RLS policies and avoids accidental full-replacement bugs.
