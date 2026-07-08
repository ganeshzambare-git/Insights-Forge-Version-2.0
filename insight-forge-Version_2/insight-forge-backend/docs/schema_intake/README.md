# Insight Forge v2.0 — Module Schema Intake

This directory is the controlled intake area for proposed database schemas from module owners.

## Rules

1. Place each module schema only inside the matching module folder.
2. Submit the schema as a Markdown (`.md`) file.
3. Do not modify `app/models/`, `app/db/`, `migrations/`, or production database files.
4. Do not create SQLAlchemy models or Alembic migrations yet.
5. Each schema proposal must include:
   - Table names and purpose
   - Columns
   - PostgreSQL data types
   - Nullability
   - Primary keys
   - Foreign keys
   - Unique constraints
   - Check constraints
   - Relationships
   - Index requirements
   - Expected data volume
   - Cross-module dependencies

## Workflow

Module Schema Proposal
→ Architecture Review
→ Conflict and Dependency Resolution
→ Final Schema Lock
→ SQLAlchemy Models
→ Alembic Migration
→ Neon PostgreSQL
