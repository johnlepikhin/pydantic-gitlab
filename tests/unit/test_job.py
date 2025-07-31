"""Tests for GitLab CI job structures."""

from pydantic_gitlab.job import (
    GitLabCIJob,
    GitLabCIJobDastConfiguration,
    GitLabCIJobHooks,
    GitLabCIJobIdentity,
    GitLabCIJobInherit,
    GitLabCIJobRelease,
    GitLabCIJobVariables,
)


class TestGitLabCIJobHooks:
    """Test GitLabCIJobHooks model."""

    def test_hooks_with_pre_get_sources(self):
        """Test hooks with pre_get_sources_script."""
        hooks = GitLabCIJobHooks(pre_get_sources_script=["echo 'Preparing environment'", "setup-tools"])
        assert hooks.pre_get_sources_script == ["echo 'Preparing environment'", "setup-tools"]

    def test_hooks_normalization(self):
        """Test script normalization from string to list."""
        hooks = GitLabCIJobHooks(pre_get_sources_script="echo 'Single command'")
        assert hooks.pre_get_sources_script == ["echo 'Single command'"]


class TestGitLabCIJobIdentity:
    """Test GitLabCIJobIdentity model."""

    def test_identity_basic(self):
        """Test basic identity configuration."""
        identity = GitLabCIJobIdentity(aud="https://example.com")
        assert identity.config["aud"] == "https://example.com"

    def test_identity_as_string(self):
        """Test identity as string."""
        identity = GitLabCIJobIdentity(aud="aws")
        assert identity.config["aud"] == "aws"

    def test_identity_as_list(self):
        """Test identity with audience as list."""
        identity = GitLabCIJobIdentity(aud=["https://example.com", "https://api.example.com"])
        assert identity.config["aud"] == ["https://example.com", "https://api.example.com"]


class TestGitLabCIJobInherit:
    """Test GitLabCIJobInherit model."""

    def test_inherit_default_true(self):
        """Test inherit with default=true."""
        inherit = GitLabCIJobInherit(default=True)
        assert inherit.default is True
        assert inherit.variables is None

    def test_inherit_default_false(self):
        """Test inherit with default=false."""
        inherit = GitLabCIJobInherit(default=False)
        assert inherit.default is False

    def test_inherit_default_list(self):
        """Test inherit with default as list."""
        inherit = GitLabCIJobInherit(default=["image", "services"])
        assert inherit.default == ["image", "services"]

    def test_inherit_variables_true(self):
        """Test inherit with variables=true."""
        inherit = GitLabCIJobInherit(variables=True)
        assert inherit.variables is True

    def test_inherit_variables_false(self):
        """Test inherit with variables=false."""
        inherit = GitLabCIJobInherit(variables=False)
        assert inherit.variables is False

    def test_inherit_variables_list(self):
        """Test inherit with variables as list."""
        inherit = GitLabCIJobInherit(variables=["VAR1", "VAR2"])
        assert inherit.variables == ["VAR1", "VAR2"]


class TestGitLabCIJobRelease:
    """Test GitLabCIJobRelease model."""

    def test_release_minimal(self):
        """Test minimal release configuration."""
        release = GitLabCIJobRelease(tag_name="v1.0.0", description="Release v1.0.0")
        assert release.tag_name == "v1.0.0"
        assert release.description == "Release v1.0.0"

    def test_release_with_name(self):
        """Test release with custom name."""
        release = GitLabCIJobRelease(tag_name="v2.0.0", name="Version 2.0.0", description="Major release")
        assert release.tag_name == "v2.0.0"
        assert release.name == "Version 2.0.0"

    def test_release_with_ref(self):
        """Test release with custom ref."""
        release = GitLabCIJobRelease(tag_name="v1.0.0", description="Release", ref="$CI_COMMIT_SHA")
        assert release.ref == "$CI_COMMIT_SHA"

    def test_release_with_milestones(self):
        """Test release with milestones."""
        release = GitLabCIJobRelease(tag_name="v1.0.0", description="Release", milestones=["v1.0", "Q1-2024"])
        assert release.milestones == ["v1.0", "Q1-2024"]

    def test_release_with_released_at(self):
        """Test release with released_at."""
        release = GitLabCIJobRelease(tag_name="v1.0.0", description="Release", released_at="2024-01-01T00:00:00Z")
        assert release.released_at == "2024-01-01T00:00:00Z"

    def test_release_with_assets(self):
        """Test release with assets."""
        release = GitLabCIJobRelease(
            tag_name="v1.0.0",
            description="Release",
            assets={"links": [{"name": "Binary", "url": "https://example.com/binary.zip"}]},
        )
        assert release.assets["links"][0]["name"] == "Binary"


class TestGitLabCIJobDastConfiguration:
    """Test GitLabCIJobDastConfiguration model."""

    def test_dast_configuration_basic(self):
        """Test basic DAST configuration."""
        dast = GitLabCIJobDastConfiguration(site_profile="Production Site", scanner_profile="Quick Scan")
        assert dast.site_profile == "Production Site"
        assert dast.scanner_profile == "Quick Scan"


class TestGitLabCIJob:
    """Test GitLabCIJob model."""

    def test_job_minimal_with_script(self):
        """Test minimal job with script."""
        job = GitLabCIJob(script=["echo 'Hello'", "echo 'World'"])
        assert job.script == ["echo 'Hello'", "echo 'World'"]
        assert job.stage is None
        assert job.image is None

    def test_job_minimal_with_run(self):
        """Test minimal job with run."""
        job = GitLabCIJob(run="echo 'Hello World'")
        assert job.run == ["echo 'Hello World'"]

    def test_job_minimal_with_trigger(self):
        """Test minimal job with trigger."""
        job = GitLabCIJob(trigger="my-project")
        assert job.trigger == "my-project"

    def test_job_can_be_empty(self):
        """Test job can be empty (e.g. template overrides)."""
        # Jobs without script/run/trigger are allowed
        # They might get these from templates or be placeholders
        job = GitLabCIJob()
        assert job.script is None
        assert job.run is None
        assert job.trigger is None

    def test_job_with_stage(self):
        """Test job with stage."""
        job = GitLabCIJob(script=["test"], stage="test")
        assert job.stage == "test"

    def test_job_with_image(self):
        """Test job with image."""
        job = GitLabCIJob(script=["python --version"], image="python:3.9")
        assert job.image == "python:3.9"

    def test_job_with_services(self):
        """Test job with services."""
        job = GitLabCIJob(script=["test"], services=["postgres:13", "redis:6"])
        assert job.services == ["postgres:13", "redis:6"]

    def test_job_with_variables(self):
        """Test job with variables."""
        job = GitLabCIJob(script=["deploy"], variables={"DEPLOY_ENV": "staging", "DEBUG": "true"})
        assert isinstance(job.variables, GitLabCIJobVariables)
        assert job.variables["DEPLOY_ENV"] == "staging"
        assert job.variables["DEBUG"] == "true"

    def test_job_with_before_after_script(self):
        """Test job with before_script and after_script."""
        job = GitLabCIJob(before_script=["setup"], script=["test"], after_script=["cleanup"])
        assert job.before_script == ["setup"]
        assert job.script == ["test"]
        assert job.after_script == ["cleanup"]

    def test_job_with_artifacts(self):
        """Test job with artifacts."""
        job = GitLabCIJob(script=["build"], artifacts={"paths": ["dist/"], "expire_in": "1 week"})
        assert job.artifacts.paths == ["dist/"]
        assert job.artifacts.expire_in == "1 week"

    def test_job_with_cache(self):
        """Test job with cache."""
        job = GitLabCIJob(script=["test"], cache={"key": "$CI_COMMIT_REF_SLUG", "paths": ["node_modules/"]})
        assert job.cache.key == "$CI_COMMIT_REF_SLUG"
        assert job.cache.paths == ["node_modules/"]

    def test_job_with_rules(self):
        """Test job with rules."""
        job = GitLabCIJob(
            script=["deploy"],
            rules=[
                {"if": "$CI_COMMIT_BRANCH == 'main'"},
                {"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'", "when": "never"},
            ],
        )
        assert len(job.rules) == 2
        assert job.rules[0].if_ == "$CI_COMMIT_BRANCH == 'main'"
        assert job.rules[1].when == "never"

    def test_job_with_needs(self):
        """Test job with needs."""
        job = GitLabCIJob(script=["test"], needs=["build", "compile"])
        assert job.needs == ["build", "compile"]

    def test_job_with_dependencies(self):
        """Test job with dependencies."""
        job = GitLabCIJob(script=["deploy"], dependencies=["build", "test"])
        assert job.dependencies == ["build", "test"]

    def test_job_with_environment(self):
        """Test job with environment."""
        job = GitLabCIJob(script=["deploy"], environment={"name": "production", "url": "https://prod.example.com"})
        assert job.environment.name == "production"
        assert job.environment.url == "https://prod.example.com"

    def test_job_with_extends(self):
        """Test job with extends."""
        job = GitLabCIJob(extends=".template", script=["test"])
        assert job.extends == [".template"]

    def test_job_with_multiple_extends(self):
        """Test job with multiple extends."""
        job = GitLabCIJob(extends=[".template1", ".template2"], script=["test"])
        assert job.extends == [".template1", ".template2"]

    def test_job_with_timeout(self):
        """Test job with timeout."""
        job = GitLabCIJob(script=["long-running-task"], timeout="2 hours")
        assert job.timeout == "2 hours"

    def test_job_with_retry(self):
        """Test job with retry."""
        job = GitLabCIJob(script=["flaky-test"], retry=2)
        assert job.retry == 2

    def test_job_with_retry_object(self):
        """Test job with retry as object."""
        job = GitLabCIJob(
            script=["test"], retry={"max": 2, "when": ["runner_system_failure", "stuck_or_timeout_failure"]}
        )
        assert job.retry.max == 2
        assert job.retry.when == ["runner_system_failure", "stuck_or_timeout_failure"]

    def test_job_with_parallel(self):
        """Test job with parallel."""
        job = GitLabCIJob(script=["test"], parallel=5)
        assert job.parallel == 5

    def test_job_with_parallel_matrix(self):
        """Test job with parallel matrix."""
        job = GitLabCIJob(script=["test"], parallel={"matrix": [{"VERSION": ["1.0", "2.0"], "OS": ["linux", "mac"]}]})
        assert job.parallel.matrix[0]["VERSION"] == ["1.0", "2.0"]
        assert job.parallel.matrix[0]["OS"] == ["linux", "mac"]

    def test_job_with_tags(self):
        """Test job with tags."""
        job = GitLabCIJob(script=["test"], tags=["docker", "linux"])
        assert job.tags == ["docker", "linux"]

    def test_job_with_allow_failure(self):
        """Test job with allow_failure."""
        job = GitLabCIJob(script=["test"], allow_failure=True)
        assert job.allow_failure is True

    def test_job_with_when(self):
        """Test job with when."""
        job = GitLabCIJob(script=["cleanup"], when="always")
        assert job.when == "always"

    def test_job_with_coverage(self):
        """Test job with coverage."""
        job = GitLabCIJob(script=["test"], coverage="/Coverage: (\\d+\\.\\d+)%/")
        assert job.coverage == "/Coverage: (\\d+\\.\\d+)%/"

    def test_job_with_release(self):
        """Test job with release."""
        job = GitLabCIJob(
            script=["build"], release={"tag_name": "v$CI_COMMIT_TAG", "description": "Release $CI_COMMIT_TAG"}
        )
        assert job.release.tag_name == "v$CI_COMMIT_TAG"
        assert job.release.description == "Release $CI_COMMIT_TAG"

    def test_job_with_resource_group(self):
        """Test job with resource_group."""
        job = GitLabCIJob(script=["deploy"], resource_group="production")
        assert job.resource_group == "production"

    def test_job_with_inherit(self):
        """Test job with inherit."""
        job = GitLabCIJob(script=["test"], inherit={"default": False, "variables": ["VAR1", "VAR2"]})
        assert job.inherit.default is False
        assert job.inherit.variables == ["VAR1", "VAR2"]

    def test_job_with_secrets(self):
        """Test job with secrets."""
        job = GitLabCIJob(
            script=["deploy"], secrets={"DATABASE_PASSWORD": {"vault": "production/database/password@secret"}}
        )
        assert "DATABASE_PASSWORD" in job.secrets

    def test_job_with_id_tokens(self):
        """Test job with id_tokens."""
        job = GitLabCIJob(script=["deploy"], id_tokens={"AWS_TOKEN": {"aud": "https://aws.amazon.com"}})
        assert "AWS_TOKEN" in job.id_tokens

    def test_complex_job(self):
        """Test complex job with many features."""
        job = GitLabCIJob(
            stage="deploy",
            image={"name": "alpine:latest", "entrypoint": [""]},
            services=["docker:dind"],
            variables={"DEPLOY_ENV": "production"},
            before_script=["apk add --no-cache curl"],
            script=["./deploy.sh"],
            after_script=["./cleanup.sh"],
            artifacts={"paths": ["logs/"], "expire_in": "1 week", "reports": {"junit": "report.xml"}},
            cache=[{"key": "gems", "paths": ["vendor/ruby"]}, {"key": "node", "paths": ["node_modules/"]}],
            rules=[{"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"}],
            needs=["build", "test"],
            environment={"name": "production", "url": "https://prod.example.com"},
            timeout="30 minutes",
            retry={"max": 2, "when": ["runner_system_failure"]},
            tags=["docker", "production"],
            allow_failure=False,
            when="on_success",
        )

        assert job.stage == "deploy"
        assert job.image.name == "alpine:latest"
        assert len(job.services) == 1
        assert job.variables["DEPLOY_ENV"] == "production"
        assert len(job.rules) == 1
        assert job.environment.name == "production"
