"""Tests for edge cases and complex scenarios."""

from pydantic_gitlab import GitLabCI, GitLabCIJob
from pydantic_gitlab.job import GitLabCIJobVariables


class TestFieldNormalization:
    """Test field normalization edge cases."""

    def test_script_normalization_edge_cases(self):
        """Test script normalization with various input types."""
        # Single command as string
        job1 = GitLabCIJob(script="echo 'hello'")
        assert job1.script == ["echo 'hello'"]

        # Empty string should become list with empty string
        job2 = GitLabCIJob(script="")
        assert job2.script == [""]

        # List with mixed content
        job3 = GitLabCIJob(script=["echo 'line1'", "", "echo 'line3'"])
        assert job3.script == ["echo 'line1'", "", "echo 'line3'"]

        # Multiline string (should not be split)
        multiline = """echo 'line1'
echo 'line2'
echo 'line3'"""
        job4 = GitLabCIJob(script=multiline)
        assert job4.script == [multiline]

    def test_extends_normalization_edge_cases(self):
        """Test extends normalization edge cases."""
        # Single extend as string
        job1 = GitLabCIJob(script=["test"], extends=".template")
        assert job1.extends == [".template"]

        # Multiple extends
        job2 = GitLabCIJob(script=["test"], extends=[".base", ".specific"])
        assert job2.extends == [".base", ".specific"]

        # Empty list should remain empty
        job3 = GitLabCIJob(script=["test"], extends=[])
        assert job3.extends == []

    def test_tags_normalization_edge_cases(self):
        """Test tags normalization edge cases."""
        # Single tag as string
        job1 = GitLabCIJob(script=["test"], tags="docker")
        assert job1.tags == ["docker"]

        # Empty string tag
        job2 = GitLabCIJob(script=["test"], tags=["docker", "", "linux"])
        assert job2.tags == ["docker", "", "linux"]


class TestVariableExpansion:
    """Test CI/CD variable expansion edge cases."""

    def test_variable_references_in_strings(self):
        """Test various variable reference formats."""
        job = GitLabCIJob(
            script=[
                "echo $VAR",
                "echo ${VAR}",
                "echo $CI_COMMIT_REF_NAME",
                "echo ${CI_COMMIT_REF_NAME}",
                "echo $$VAR",  # Escaped dollar sign
                "echo '$VAR'",  # Single quotes prevent expansion
                'echo "$VAR"',  # Double quotes allow expansion
            ],
            variables={
                "IMAGE": "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG",
                "URL": "https://${CI_ENVIRONMENT_SLUG}.example.com",
                "ESCAPED": "$$DOLLAR",
            },
        )

        assert "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG" in job.variables["IMAGE"]
        assert "https://${CI_ENVIRONMENT_SLUG}.example.com" in job.variables["URL"]
        assert "$$DOLLAR" in job.variables["ESCAPED"]

    def test_nested_variable_references(self):
        """Test nested variable references."""
        ci = GitLabCI(
            variables={
                "BASE_IMAGE": "python:3.9",
                "FULL_IMAGE": "$BASE_IMAGE-alpine",
                "REGISTRY_IMAGE": "$CI_REGISTRY/$FULL_IMAGE",
            },
            test_job={"script": ["echo $REGISTRY_IMAGE"], "variables": {"LOCAL_IMAGE": "$REGISTRY_IMAGE-$CI_JOB_ID"}},
        )

        assert ci.variables["FULL_IMAGE"] == "$BASE_IMAGE-alpine"
        assert ci.jobs["test_job"].variables["LOCAL_IMAGE"] == "$REGISTRY_IMAGE-$CI_JOB_ID"


class TestJobDependencies:
    """Test job dependency edge cases."""

    def test_circular_dependencies(self):
        """Test circular dependency detection."""
        ci = GitLabCI(
            job_a={"script": ["echo A"], "needs": ["job_b"]},
            job_b={"script": ["echo B"], "needs": ["job_c"]},
            job_c={"script": ["echo C"], "needs": ["job_a"]},
        )

        # The library doesn't prevent circular dependencies at parse time
        # This would be caught by GitLab CI when running
        assert ci.jobs["job_a"].needs == ["job_b"]
        assert ci.jobs["job_b"].needs == ["job_c"]
        assert ci.jobs["job_c"].needs == ["job_a"]

    def test_needs_with_artifacts(self):
        """Test needs with artifact options."""
        job = GitLabCIJob(
            script=["deploy"], needs=["build", {"job": "test", "artifacts": True}, {"job": "scan", "artifacts": False}]
        )

        assert len(job.needs) == 3
        assert job.needs[0] == "build"
        assert job.needs[1].job == "test"
        assert job.needs[1].artifacts is True
        assert job.needs[2].artifacts is False

    def test_needs_with_optional(self):
        """Test needs with optional jobs."""
        job = GitLabCIJob(
            script=["deploy"], needs=[{"job": "build", "optional": True}, {"job": "test", "optional": False}]
        )

        assert job.needs[0].optional is True
        assert job.needs[1].optional is False


class TestRulesEdgeCases:
    """Test rules edge cases."""

    def test_complex_rule_conditions(self):
        """Test complex rule conditions."""
        job = GitLabCIJob(
            script=["test"],
            rules=[
                # Multiple conditions in one rule
                {
                    "if": "$CI_MERGE_REQUEST_ID",
                    "changes": ["src/**/*.py"],
                    "exists": ["tests/**/*.py"],
                    "when": "manual",
                },
                # Rule with only when
                {"when": "never"},
                # Rule with complex changes
                {"changes": {"paths": ["src/**/*", "lib/**/*"], "compare_to": "refs/heads/main"}},
            ],
        )

        assert len(job.rules) == 3
        assert job.rules[0].if_ == "$CI_MERGE_REQUEST_ID"
        assert job.rules[0].changes == ["src/**/*.py"]
        assert job.rules[0].exists == ["tests/**/*.py"]

    def test_rules_with_all_keywords(self):
        """Test rules with all possible keywords."""
        job = GitLabCIJob(
            script=["deploy"],
            rules=[
                {
                    "if": "$CI_COMMIT_TAG",
                    "changes": ["version.txt"],
                    "exists": ["Dockerfile"],
                    "when": "manual",
                    "allow_failure": True,
                    "variables": {"DEPLOY": "true"},
                    "needs": ["build", "test"],
                    "interruptible": False,
                }
            ],
        )

        rule = job.rules[0]
        assert rule.if_ == "$CI_COMMIT_TAG"
        assert rule.when == "manual"
        assert rule.allow_failure is True
        assert rule.variables["DEPLOY"] == "true"
        assert rule.needs == ["build", "test"]
        assert rule.interruptible is False


class TestParallelJobsEdgeCases:
    """Test parallel job edge cases."""

    def test_parallel_matrix_complex(self):
        """Test complex parallel matrix configurations."""
        job = GitLabCIJob(
            script=["test"],
            parallel={
                "matrix": [
                    {"PROVIDER": ["aws", "gcp", "azure"], "STACK": ["monitoring", "app", "data"]},
                    {"PROVIDER": ["aws"], "STACK": ["legacy"], "REGION": ["us-east-1", "eu-west-1"]},
                ]
            },
        )

        assert len(job.parallel.matrix) == 2
        assert job.parallel.matrix[0]["PROVIDER"] == ["aws", "gcp", "azure"]
        assert job.parallel.matrix[1]["REGION"] == ["us-east-1", "eu-west-1"]

    def test_parallel_with_large_number(self):
        """Test parallel with large number."""
        job = GitLabCIJob(
            script=["test"],
            parallel=50,  # Maximum allowed by GitLab
        )
        assert job.parallel == 50


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_yaml_special_characters_in_values(self):
        """Test YAML special characters in values."""
        job = GitLabCIJob(
            script=[
                "echo 'Single quotes'",
                'echo "Double quotes"',
                "echo `backticks`",
                "echo | pipe",
                "echo > redirect",
                "echo & ampersand",
                "echo : colon",
                "echo { brace",
                "echo [ bracket",
                "echo @ at",
                "echo # hash",
            ],
            variables={
                "SPECIAL_CHARS": "!@#$%^&*()",
                "YAML_SPECIAL": "|>-:{}[]",
                "QUOTES": "'\"",
                "NEWLINE": "line1\\nline2",
                "TAB": "col1\\tcol2",
            },
        )

        assert len(job.script) == 11
        assert job.variables["SPECIAL_CHARS"] == "!@#$%^&*()"
        assert job.variables["YAML_SPECIAL"] == "|>-:{}[]"

    def test_unicode_characters(self):
        """Test Unicode characters in values."""
        job = GitLabCIJob(
            script=["echo 'Hello 世界'"],
            variables={"EMOJI": "🚀 Deploy", "UNICODE": "Привет мир", "MIXED": "Test-テスト-测试"},
        )

        assert job.script[0] == "echo 'Hello 世界'"
        assert job.variables["EMOJI"] == "🚀 Deploy"
        assert job.variables["UNICODE"] == "Привет мир"


class TestExtraFieldsHandling:
    """Test handling of extra/unknown fields."""

    def test_extra_fields_preserved(self):
        """Test that extra fields are preserved."""
        job_data = {
            "script": ["test"],
            "unknown_field": "value",
            "future_feature": {"option1": "value1", "option2": 123},
        }

        job = GitLabCIJob(**job_data)
        assert job.script == ["test"]
        assert job.unknown_field == "value"
        assert job.future_feature == {"option1": "value1", "option2": 123}

    def test_gitlab_ci_extra_fields(self):
        """Test extra fields at GitLabCI level."""
        ci_data = {
            "stages": ["build", "test"],
            "test_job": {"script": ["test"]},
            "unknown_keyword": "value",
            "future_section": {"setting": "value"},
        }

        ci = GitLabCI(**ci_data)
        assert ci.stages == ["build", "test"]
        assert "test_job" in ci.jobs
        assert ci.extra_fields["unknown_keyword"] == "value"
        assert ci.extra_fields["future_section"] == {"setting": "value"}


class TestEmptyConfigurations:
    """Test empty and minimal configurations."""

    def test_minimal_valid_ci(self):
        """Test minimal valid CI configuration."""
        # Minimal config has at least one job
        ci = GitLabCI(test={"script": ["echo 'test'"]})

        assert len(ci.jobs) == 1
        assert ci.jobs["test"].script == ["echo 'test'"]

    def test_empty_arrays_and_objects(self):
        """Test empty arrays and objects."""
        job = GitLabCIJob(
            script=["test"],
            variables={},  # Empty variables
            tags=[],  # Empty tags
            rules=[],  # Empty rules
            services=[],  # Empty services
            needs=[],  # Empty needs
        )

        assert job.script == ["test"]
        assert isinstance(job.variables, GitLabCIJobVariables)
        assert job.variables.variables == {}
        assert job.tags == []
        assert job.rules == []
        assert job.services == []
        assert job.needs == []


class TestLongStrings:
    """Test handling of very long strings."""

    def test_long_script_commands(self):
        """Test very long script commands."""
        long_command = "echo " + "x" * 1000  # Very long command
        job = GitLabCIJob(script=[long_command])
        assert job.script[0] == long_command

    def test_long_variable_values(self):
        """Test very long variable values."""
        long_value = "A" * 5000  # 5KB string
        job = GitLabCIJob(script=["test"], variables={"LONG_VAR": long_value})
        assert job.variables["LONG_VAR"] == long_value


class TestDeprecatedSyntax:
    """Test handling of deprecated GitLab CI syntax."""

    def test_only_except_keywords(self):
        """Test deprecated only/except keywords."""
        # These are stored as extra fields since they're not in our models
        job = GitLabCIJob(script=["test"], only=["main", "develop"], except_=["tags"])

        assert job.script == ["test"]
        assert job.only == ["main", "develop"]
        assert job.except_ == ["tags"]

    def test_type_keyword(self):
        """Test deprecated type keyword."""
        job = GitLabCIJob(
            script=["test"],
            type="test",  # Old way to specify stage
        )

        assert job.script == ["test"]
        assert job.type == "test"
