"""Tests for validation errors and error messages."""

import pytest
from pydantic import ValidationError

from pydantic_gitlab import (
    GitLabCI,
    GitLabCIArtifacts,
    GitLabCICache,
    GitLabCICacheKey,
    GitLabCIJob,
    GitLabCIRule,
    GitLabCIWorkflow,
    GitLabCIWorkflowRule,
)
from pydantic_gitlab.include import parse_include


class TestJobValidationErrors:
    """Test job validation errors."""

    def test_job_without_script_run_or_trigger(self):
        """Test job can be created without script, run, or trigger."""
        # This is now allowed for template overrides
        job = GitLabCIJob()
        assert job.script is None
        assert job.run is None
        assert job.trigger is None

    def test_job_with_invalid_when(self):
        """Test job with invalid when value."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], when="invalid_when")

        error = str(exc_info.value)
        assert "when" in error.lower()

    def test_job_with_invalid_stage_type(self):
        """Test job with invalid stage type."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], stage=123)  # Stage should be string

        error = str(exc_info.value)
        assert "stage" in error.lower()

    def test_job_with_invalid_timeout(self):
        """Test job with invalid timeout format."""
        # Valid timeout formats are like "30 minutes", "2 hours", etc.
        # Invalid would be just a number or wrong format
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], timeout=30)  # Should be string

        error = str(exc_info.value)
        assert "timeout" in error.lower()

    def test_job_with_invalid_retry(self):
        """Test job with invalid retry configuration."""
        # Retry can be number 0-2 or object
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], retry="invalid")

        error = str(exc_info.value)
        assert "retry" in error.lower()

    def test_job_with_retry_max_out_of_range(self):
        """Test job with retry max out of range."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], retry={"max": 3})  # Max is 2

        error = str(exc_info.value)
        assert "max" in error.lower() or "retry" in error.lower()


class TestRuleValidationErrors:
    """Test rule validation errors."""

    def test_rule_without_conditions(self):
        """Test rule must have at least one condition."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIRule()

        error = str(exc_info.value)
        assert "at least one condition" in error.lower()

    def test_rule_with_only_action(self):
        """Test rule with only when is allowed."""
        # A rule with only 'when' is actually valid
        rule = GitLabCIRule(when="manual")
        assert rule.when == "manual"
        assert rule.if_ is None
        assert rule.changes is None
        assert rule.exists is None

    def test_workflow_rule_without_conditions(self):
        """Test workflow rule without conditions is allowed."""
        # Workflow rules can exist without conditions (e.g., just variables)
        rule = GitLabCIWorkflowRule()
        assert rule.if_ is None
        assert rule.changes is None
        assert rule.exists is None
        assert rule.when is None


class TestArtifactsValidationErrors:
    """Test artifacts validation errors."""

    def test_artifacts_without_paths_or_reports(self):
        """Test artifacts can exist without paths or reports."""
        # Artifacts can exist with just metadata like expire_in
        artifacts = GitLabCIArtifacts(expire_in="1 week")
        assert artifacts.paths is None
        assert artifacts.reports is None
        assert artifacts.expire_in == "1 week"

    def test_artifacts_with_invalid_when(self):
        """Test artifacts with invalid when value."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIArtifacts(paths=["dist/"], when="invalid")

        error = str(exc_info.value)
        assert "when" in error.lower()

    def test_artifacts_with_invalid_access(self):
        """Test artifacts with invalid access level."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIArtifacts(paths=["dist/"], access="invalid")

        error = str(exc_info.value)
        assert "access" in error.lower()


class TestCacheValidationErrors:
    """Test cache validation errors."""

    def test_cache_without_paths_or_untracked(self):
        """Test cache must have paths or untracked."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICache(key="cache-key")

        error = str(exc_info.value)
        assert "paths" in error.lower() or "untracked" in error.lower()

    def test_cache_key_without_key_or_files(self):
        """Test cache key must have key or files."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey()

        error = str(exc_info.value)
        assert "key" in error.lower() or "files" in error.lower()

    def test_cache_key_with_both_key_and_files(self):
        """Test cache key cannot have both key and files."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey(key="my-key", files=["package.json"])

        error = str(exc_info.value)
        assert "cannot specify both" in error.lower()

    def test_cache_key_prefix_without_files(self):
        """Test cache key prefix requires files."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey(key="my-key", prefix="prefix")

        error = str(exc_info.value)
        assert "prefix" in error.lower()

    def test_cache_with_invalid_policy(self):
        """Test cache with invalid policy."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICache(key="key", paths=["vendor/"], policy="invalid")

        error = str(exc_info.value)
        assert "policy" in error.lower()


class TestVariableValidationErrors:
    """Test variable validation errors."""

    def test_variable_with_invalid_type(self):
        """Test variable with completely invalid type."""
        # Variables now accept various types including nested dicts
        # This test is no longer valid as we support flexible variable types
        job = GitLabCIJob(script=["test"], variables={"VALID": "string", "ALSO_VALID": 123, "BOOL_VALID": True})
        assert job.variables["VALID"] == "string"
        assert job.variables["ALSO_VALID"] == 123
        assert job.variables["BOOL_VALID"] is True


class TestEnvironmentValidationErrors:
    """Test environment validation errors."""

    def test_environment_with_invalid_action(self):
        """Test environment with invalid action."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["deploy"], environment={"name": "production", "action": "invalid_action"})

        error = str(exc_info.value)
        assert "action" in error.lower()


class TestIncludeValidationErrors:
    """Test include validation errors."""

    def test_parse_include_with_unknown_type(self):
        """Test parsing include with unknown type."""
        with pytest.raises(ValueError) as exc_info:
            parse_include({"unknown_type": "value"})

        error = str(exc_info.value)
        assert "unknown include type" in error.lower()

    def test_parse_include_with_invalid_type(self):
        """Test parsing include with invalid type."""
        with pytest.raises(ValueError) as exc_info:
            parse_include(123)  # Not a string, dict, or list

        error = str(exc_info.value)
        assert "invalid include configuration" in error.lower()


class TestWorkflowValidationErrors:
    """Test workflow validation errors."""

    def test_workflow_auto_cancel_invalid_values(self):
        """Test workflow auto_cancel with invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIWorkflow(rules=[{"if": "$CI_COMMIT_BRANCH"}], auto_cancel={"on_new_commit": "invalid_value"})

        error = str(exc_info.value)
        assert "on_new_commit" in error.lower()


class TestComplexValidationScenarios:
    """Test complex validation scenarios."""

    def test_job_with_multiple_validation_errors(self):
        """Test job with multiple validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(
                script=["test"],  # Add script to avoid that validation issue
                when="invalid_when",
                timeout=123,  # Should be string
                retry="invalid",  # Should be number or object
                artifacts={
                    # Missing paths or reports
                    "when": "invalid_artifact_when"
                },
            )

        error = str(exc_info.value)
        # Should contain multiple validation errors
        assert "validation error" in error.lower()

    def test_nested_validation_errors(self):
        """Test nested validation errors are properly reported."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(
                script=["test"],
                cache={
                    "key": {
                        # Missing both key and files
                        "prefix": "test"  # But has prefix which requires files
                    },
                    # Missing paths or untracked
                },
            )

        error = str(exc_info.value)
        assert "validation error" in error.lower()

    def test_gitlab_ci_level_validation(self):
        """Test GitLab CI level validation."""
        # Test empty GitLabCI - should work
        ci = GitLabCI()
        assert ci.jobs == {}

        # Test with a job that has no script/run/trigger - should work
        ci = GitLabCI(test_job={"stage": "test"})
        assert "test_job" in ci.jobs
        assert ci.jobs["test_job"].stage == "test"


class TestErrorMessageClarity:
    """Test that error messages are clear and helpful."""

    def test_missing_required_field_message(self):
        """Test that jobs without script/run/trigger are allowed."""
        # Jobs without script/run/trigger are now allowed (template overrides)
        job = GitLabCIJob(stage="test")
        assert job.script is None
        assert job.run is None
        assert job.trigger is None

    def test_invalid_enum_value_message(self):
        """Test error message for invalid enum value."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=["test"], when="whenever")

        error = str(exc_info.value)
        # Should show valid options
        assert "when" in error.lower()
        # Ideally would show valid values like "on_success", "on_failure", etc.

    def test_type_mismatch_message(self):
        """Test error message for type mismatch."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIJob(script=123)  # Should be string or list

        error = str(exc_info.value)
        assert "script" in error.lower()
        # Should indicate expected type
