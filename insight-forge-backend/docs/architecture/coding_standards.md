# Coding Standards & Quality Rules — Insight Forge V2

This document details backend styling, code format, typing, and logging requirements.

---

## 1. Code Formatting & Linting

We maintain strict quality rules to ensure the codebase remains clean:
- **Black Formatter**: All Python code must be formatted using the configuration specified in `pyproject.toml`.
- **Ruff Linter**: Code must pass ruff analysis checks with zero warnings or errors prior to commit.
- **Run verification**:
  ```bash
  black --check app
  ruff check app
  ```

---

## 2. Typing & Naming Conventions

- **Type Hints**: Fully annotate every function signature, function parameter, and return value. Avoid using `Any` wherever possible.
- **Python Naming**: Use standard `snake_case` for variables, functions, parameters, and database columns.
- **Class Names**: Use `PascalCase` for classes, models, and exception definitions.
- **File Names**: Use `snake_case` filenames that match the ORM class name (e.g. `student_metric.py` for class `StudentMetric`).

---

## 3. Structured Logging Conventions

Log records are serialized as structured JSON strings containing key metadata for centralized parsing:
- **Timestamp**: Formatted strictly to ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SS.mmmZ`).
- **Standard Fields**:
  - `logger`: Name of the logger (e.g. `app.main`).
  - `module`: The python module originating the log.
  - `filename`: Filename.
  - `line_number`: Code line number.
- **Correlation Fields**: Defaulting to `None` if missing:
  - `request_id`
  - `tenant_id`
  - `path`
  - `method`
  - `status_code`
  - `execution_time_ms`
  - `client_ip`
