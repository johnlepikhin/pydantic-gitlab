"""Shared pytest fixtures and configuration."""

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def sample_configs_dir() -> Path:
    """Return path to sample GitLab CI configurations."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Load a fixture file."""

    def _load(filename: str) -> dict[str, Any]:
        fixture_path = Path(__file__).parent / "fixtures" / filename
        with fixture_path.open() as f:
            return yaml.safe_load(f)

    return _load


@pytest.fixture
def minimal_job_config() -> dict[str, Any]:
    """Minimal valid job configuration."""
    return {"script": ["echo 'Hello World'"]}


@pytest.fixture
def complex_job_config() -> dict[str, Any]:
    """Complex job configuration with many fields."""
    return {
        "stage": "test",
        "script": ["pytest", "coverage run -m pytest"],
        "image": "python:3.9",
        "services": ["postgres:latest"],
        "variables": {"TEST_VAR": "value"},
        "cache": {"key": "$CI_COMMIT_REF_SLUG", "paths": [".cache/"]},
        "artifacts": {"paths": ["coverage/"], "reports": {"junit": "report.xml"}, "expire_in": "1 week"},
        "rules": [{"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'"}],
        "retry": 2,
        "timeout": "30 minutes",
        "tags": ["docker"],
        "allow_failure": False,
        "when": "on_success",
    }


@pytest.fixture
def minimal_ci_config() -> dict[str, Any]:
    """Minimal valid CI configuration."""
    return {"test-job": {"script": ["echo 'test'"]}}


@pytest.fixture
def complex_ci_config() -> dict[str, Any]:
    """Complex CI configuration with multiple features."""
    return {
        "stages": ["build", "test", "deploy"],
        "variables": {"DOCKER_DRIVER": "overlay2", "DOCKER_TLS_CERTDIR": "/certs"},
        "default": {"image": "ruby:3.0", "cache": {"paths": ["vendor/"]}},
        "workflow": {"rules": [{"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"}]},
        "build-job": {"stage": "build", "script": ["make build"], "artifacts": {"paths": ["dist/"]}},
        "test-job": {"stage": "test", "script": ["make test"], "needs": ["build-job"]},
        "deploy-job": {
            "stage": "deploy",
            "script": ["make deploy"],
            "environment": {"name": "production", "url": "https://example.com"},
            "only": ["main"],
        },
    }


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up test environment."""
    # Change to temp directory for test isolation
    monkeypatch.chdir(tmp_path)

    # Create fixtures directory if it doesn't exist
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    yield
