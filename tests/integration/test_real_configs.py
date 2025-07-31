"""Test parsing real GitLab CI configurations."""

from pathlib import Path

import pytest
import yaml

from pydantic_gitlab import GitLabCI


class TestRealConfigurations:
    """Test parsing real GitLab CI configuration files."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get fixtures directory path."""
        return Path(__file__).parent.parent / "fixtures" / "gitlab_ci_examples"

    def test_parse_nodejs_config(self, fixtures_dir):
        """Test parsing Node.js configuration."""
        config_path = fixtures_dir / "nodejs.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        # Verify structure
        assert ci.image == "node:16"
        assert len(ci.stages) == 4
        assert ci.variables["NODE_ENV"] == "test"

        # Check cache configuration
        assert ci.cache.key.files == ["package-lock.json"]
        assert ci.cache.paths == [".npm/", "node_modules/"]

        # Check jobs
        assert len(ci.jobs) == 6

        # Check install job
        install_job = ci.jobs["install"]
        assert install_job.stage == "install"
        assert install_job.artifacts.expire_in == "1 hour"

        # Check test job with coverage
        test_job = ci.jobs["test"]
        assert test_job.needs == ["install"]
        assert test_job.coverage == r"/Statements\s*:\s*(\d+\.\d+)%/"
        assert test_job.artifacts.reports.junit == ["junit.xml"]

        # Check deploy jobs
        deploy_staging = ci.jobs["deploy:staging"]
        assert deploy_staging.environment.name == "staging"
        assert deploy_staging.only == ["develop"]

        deploy_prod = ci.jobs["deploy:production"]
        assert deploy_prod.when == "manual"
        assert deploy_prod.only == ["main"]

    def test_parse_python_docker_config(self, fixtures_dir):
        """Test parsing Python Docker configuration."""
        config_path = fixtures_dir / "python_docker.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        # Check variables
        assert ci.variables["DOCKER_DRIVER"] == "overlay2"
        assert ci.variables["REGISTRY"] == "$CI_REGISTRY_IMAGE"

        # Check workflow
        assert len(ci.workflow.rules) == 3

        # Check test jobs
        lint_job = ci.jobs["test:lint"]
        assert lint_job.stage == "test"
        assert lint_job.image == "python:3.9"

        unit_job = ci.jobs["test:unit"]
        assert len(unit_job.services) == 2
        assert unit_job.services[0].name == "postgres:13"
        assert unit_job.services[0].alias == "postgres"
        assert unit_job.coverage == r"/TOTAL.+?(\d+\%)/"

        security_job = ci.jobs["test:security"]
        assert security_job.allow_failure is True

        # Check build job
        build_job = ci.jobs["build:image"]
        assert build_job.image == "docker:20.10"
        assert build_job.services[0] == "docker:20.10-dind"

        # Check deploy template
        assert ".deploy" in ci.references

        # Check deploy jobs
        staging_deploy = ci.jobs["deploy:staging"]
        assert staging_deploy.extends == [".deploy"]
        assert staging_deploy.environment.name == "staging"
        assert staging_deploy.environment.on_stop == "stop:staging"

        prod_deploy = ci.jobs["deploy:production"]
        assert prod_deploy.environment.kubernetes.namespace == "production"
        assert len(prod_deploy.rules) == 2
        assert prod_deploy.rules[0].if_ == r"$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/"
        assert prod_deploy.rules[0].when == "manual"

        # Check stop job
        stop_job = ci.jobs["stop:staging"]
        assert stop_job.environment.action == "stop"
        assert stop_job.when == "manual"

    def test_job_inheritance(self, fixtures_dir):
        """Test job inheritance with extends."""
        config_path = fixtures_dir / "python_docker.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        # Check that extended jobs inherit from template
        staging_deploy = ci.jobs["deploy:staging"]

        # The actual inheritance is not resolved by our parser
        # but we can check that extends is properly parsed
        assert staging_deploy.extends == [".deploy"]

        # Both should have their own properties
        assert staging_deploy.environment.name == "staging"
        assert staging_deploy.variables["DEPLOY_WEBHOOK_URL"] == "$STAGING_WEBHOOK_URL"

    def test_services_configuration(self, fixtures_dir):
        """Test complex services configuration."""
        config_path = fixtures_dir / "python_docker.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        unit_job = ci.jobs["test:unit"]

        # Check Postgres service
        postgres_service = unit_job.services[0]
        assert postgres_service.name == "postgres:13"
        assert postgres_service.alias == "postgres"
        assert postgres_service.variables["POSTGRES_DB"] == "test_db"
        assert postgres_service.variables["POSTGRES_USER"] == "test_user"

        # Check Redis service (simple string format)
        redis_service = unit_job.services[1]
        assert redis_service == "redis:6-alpine"

        # Check environment variables that use service aliases
        assert unit_job.variables["DATABASE_URL"] == "postgresql://test_user:test_pass@postgres/test_db"
        assert unit_job.variables["REDIS_URL"] == "redis://redis:6379"

    def test_conditional_logic_in_script(self, fixtures_dir):
        """Test parsing scripts with conditional logic."""
        config_path = fixtures_dir / "python_docker.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        build_job = ci.jobs["build:image"]

        # Check multi-line script with pipe
        assert len(build_job.script) == 3
        assert build_job.script[0] == "docker build -t $REGISTRY:$IMAGE_TAG ."
        assert build_job.script[1] == "docker push $REGISTRY:$IMAGE_TAG"
        # The third item is the multi-line conditional
        assert "if [" in build_job.script[2]
        assert "docker tag" in build_job.script[2]

    def test_artifacts_reports(self, fixtures_dir):
        """Test artifacts reports configuration."""
        config_path = fixtures_dir / "nodejs.yml"

        with config_path.open() as f:
            yaml_data = yaml.safe_load(f)

        ci = GitLabCI(**yaml_data)

        test_job = ci.jobs["test"]

        # Check JUnit report
        assert test_job.artifacts.reports.junit == ["junit.xml"]

        # Check coverage report
        coverage_report = test_job.artifacts.reports.coverage_report
        assert coverage_report["coverage_format"] == "cobertura"
        assert coverage_report["path"] == "coverage/cobertura-coverage.xml"
