# Repository Layer Architecture Guide

This package implements the Data Access / Repository Layer for **Insight Forge V2**. It acts as the sole communication bridge between the database (via SQLAlchemy ORM) and the upcoming Service Layer.

---

## 1. Core Principles

1. **Stateless Operations**: Repositories are completely stateless except for the injected `AsyncSession`.
2. **Transaction Boundaries**: Repositories **never** manage transaction boundaries (do not invoke `commit()` or `rollback()`). Transaction coordination belongs strictly to the Service Layer / Unit of Work.
3. **No HTTP Concepts**: Repositories have no knowledge of FastAPI, request routes, or HTTP status codes. They raise Python/SQLAlchemy exceptions (`RepositoryError`, `EntityNotFoundError`, etc.) which the Service Layer translates later.
4. **Strong Typing**: Implemented using `Generic[ModelType]` and `TypeVar` to ensure complete compiler safety and IDE autocomplete.

---

## 2. API Reference

### BaseRepository

Every concrete repository inherits from `BaseRepository[ModelType]` in [base.py](file:///c:/Users/Neeraj/Downloads/insight-forge-Version_2/insight-forge-Version_2/insight-forge-backend/app/repositories/base.py):

```python
class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession) -> None: ...
```

#### Supported CRUD Operations
- `create(entity: ModelType) -> ModelType`
- `get_by_id(id_: Any) -> ModelType | None`
- `get_one_or_none(**filters: Any) -> ModelType | None`
- `get_all(limit: int = 100, offset: int = 0, order_by: Any = None, **filters: Any) -> Sequence[ModelType]`
- `paginate(limit: int = 20, offset: int = 0, order_by: Any = None, **filters: Any) -> tuple[Sequence[ModelType], int]`
- `update(entity: ModelType, **updates: Any) -> ModelType`
- `delete(entity: ModelType) -> None`
- `exists(**filters: Any) -> bool`
- `count(**filters: Any) -> int`
- `flush() -> None`
- `refresh(entity: ModelType) -> None`

---

## 3. Concrete Domain Repositories

- **TenantRepository** (`tenant.py`): Global institutional partitions.
- **UserRepository** (`user.py`): Identity lookup, email validation, and role filters.
- **SessionRepository** (`session.py`): JWT token lifetime tracking and ingress auditing.
- **CohortRepository** (`cohort.py`): Educational student groups.
- **StudentMetricRepository** (`student_metric.py`): Academic grades and attendance logs.
- **CoachingInterventionRepository** (`coaching_intervention.py`): Academic advisory intervention notes.

---

## 4. Usage Example in Service Layer

```python
from app.repositories import UserRepository
from app.repositories.exceptions import EntityNotFoundError

async def upgrade_user_role(session: AsyncSession, user_id: UUID, new_role: str) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundError("User not found")
        
    await repo.update(user, assigned_role=new_role)
    await repo.flush()
    # Transaction commit is managed outside the repository by the Service
```
