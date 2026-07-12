```markdown
# Insights-Forge-Version-2.0 Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill covers the development patterns and conventions used in the Insights-Forge-Version-2.0 Python codebase. It is designed to help contributors understand the project's structure, coding style, and typical workflows, ensuring consistency and ease of collaboration.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `dataProcessor.py`, `userManager.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import parseData
    from .models import UserModel
    ```

### Export Style
- Use **default exports** (i.e., define the main class or function at the end of the file).
  - Example:
    ```python
    class DataProcessor:
        pass

    # Default export (main class/function is defined at the end)
    ```

### Commit Patterns
- Commit messages are **freeform**, sometimes prefixed (e.g., `backend:`).
- Average commit message length: **139 characters**.
  - Example:
    ```
    backend: Refactored data ingestion pipeline to improve performance and added error handling for missing fields.
    ```

## Workflows

### Code Update
**Trigger:** When you need to add or modify features or fix bugs.
**Command:** `/code-update`

1. Create a new branch for your changes.
2. Make code changes following the coding conventions.
3. Write or update tests if necessary.
4. Commit your changes with a descriptive message (optionally prefixed, e.g., `backend:`).
5. Push your branch and create a pull request.

### Testing
**Trigger:** When you want to verify your code changes.
**Command:** `/run-tests`

1. Identify or create test files matching the `*.test.*` pattern.
2. Run your preferred Python test runner (e.g., `pytest`, `unittest`) on the test files.
   - Example:
     ```bash
     pytest
     ```
3. Review test results and fix any failing tests.

## Testing Patterns

- **Test Framework:** Unknown (use your preferred Python test runner).
- **Test File Pattern:** Files named with `*.test.*` (e.g., `dataProcessor.test.py`).
- **Test Example:**
  ```python
  # dataProcessor.test.py
  from .dataProcessor import DataProcessor

  def test_process_data():
      dp = DataProcessor()
      result = dp.process([1, 2, 3])
      assert result == [2, 4, 6]
  ```

## Commands
| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| /code-update   | Start a new code update workflow             |
| /run-tests     | Run all tests in the repository              |
```
