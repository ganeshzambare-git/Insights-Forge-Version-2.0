"""
Insight Forge V2 — Integration Tests for Docker Setup.

Verifies that Docker configurations, Compose YAML syntax, and root environment
variable examples are present and correctly structured.
"""

import os
import yaml


def test_docker_compose_file_exists_and_is_valid() -> None:
    """Assert that docker-compose.yml exists in the project root and is valid YAML."""
    # Find root from backend workspace tests folder (up two directories to project root)
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Let's check for compose file in both the parent of backend and the grandparent
    compose_path_grandparent = os.path.join(root_path, "..", "docker-compose.yml")
    compose_path_parent = os.path.join(root_path, "docker-compose.yml")

    compose_path = compose_path_grandparent if os.path.exists(compose_path_grandparent) else compose_path_parent

    assert os.path.exists(compose_path), f"docker-compose.yml not found at {compose_path_parent}"

    # Load and parse Compose structure
    with open(compose_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config, "Compose file is missing 'services' key."
    services = config["services"]

    # Verify that all 4 required containers are defined
    assert "postgres" in services, "Missing postgres service in docker-compose"
    assert "redis" in services, "Missing redis service in docker-compose"
    assert "backend" in services, "Missing backend service in docker-compose"
    assert "frontend" in services, "Missing frontend service in docker-compose"


def test_env_example_matches_compose_definitions() -> None:
    """Assert that environment configuration defaults correspond to internal Docker DNS."""
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_grandparent = os.path.join(root_path, "..", ".env.example")
    env_parent = os.path.join(root_path, ".env.example")

    env_path = env_grandparent if os.path.exists(env_grandparent) else env_parent
    assert os.path.exists(env_path), f".env.example not found at {env_parent}"

    # Verify default variables are defined
    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    assert "DATABASE_URL=postgresql+asyncpg://" in env_content
    assert "postgres:5432" in env_content  # internal docker DB endpoint DNS
    assert "redis:6379" in env_content     # internal docker redis endpoint DNS


def test_dockerfiles_exist() -> None:
    """Assert Dockerfile exists in both backend and frontend directories."""
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Backend Dockerfile check
    backend_dockerfile = os.path.join(root_path, "Dockerfile")
    assert os.path.exists(backend_dockerfile), "Backend Dockerfile not found"

    # Frontend Dockerfile check
    frontend_dockerfile_grandparent = os.path.join(root_path, "..", "insight-forge-frontend", "Dockerfile")
    frontend_dockerfile_parent = os.path.join(root_path, "insight-forge-frontend", "Dockerfile")
    frontend_dockerfile = frontend_dockerfile_grandparent if os.path.exists(frontend_dockerfile_grandparent) else frontend_dockerfile_parent

    # Try matching relative to the workspace parent if not found
    if not os.path.exists(frontend_dockerfile):
        frontend_dockerfile = os.path.abspath(os.path.join(root_path, "..", "insight-forge-frontend", "Dockerfile"))

    assert os.path.exists(frontend_dockerfile), f"Frontend Dockerfile not found at {frontend_dockerfile}"
