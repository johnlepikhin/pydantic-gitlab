"""Tests for GitLab CI include structures."""

import pytest

from pydantic_gitlab.include import (
    GitLabCIIncludeComponent,
    GitLabCIIncludeInputs,
    GitLabCIIncludeLocal,
    GitLabCIIncludeProject,
    GitLabCIIncludeRemote,
    GitLabCIIncludeTemplate,
    parse_include,
)


class TestGitLabCIIncludeInputs:
    """Test GitLabCIIncludeInputs model."""

    def test_include_inputs_simple(self):
        """Test simple include inputs."""
        inputs = GitLabCIIncludeInputs(environment="production", version="1.0.0")
        assert inputs.inputs["environment"] == "production"
        assert inputs.inputs["version"] == "1.0.0"

    def test_include_inputs_with_types(self):
        """Test include inputs with different types."""
        inputs = GitLabCIIncludeInputs(
            string_input="value", number_input=42, boolean_input=True, list_input=["item1", "item2"]
        )
        assert inputs.inputs["string_input"] == "value"
        assert inputs.inputs["number_input"] == 42
        assert inputs.inputs["boolean_input"] is True
        assert inputs.inputs["list_input"] == ["item1", "item2"]

    def test_include_inputs_access(self):
        """Test accessing inputs."""
        inputs = GitLabCIIncludeInputs(test_var="test_value")
        assert inputs.inputs["test_var"] == "test_value"


class TestGitLabCIIncludeLocal:
    """Test GitLabCIIncludeLocal model."""

    def test_include_local_simple(self):
        """Test simple local include."""
        include = GitLabCIIncludeLocal(local="/templates/test.yml")
        assert include.local == "/templates/test.yml"
        assert include.inputs is None
        assert include.rules is None

    def test_include_local_with_inputs(self):
        """Test local include with inputs."""
        include = GitLabCIIncludeLocal(local="/templates/deploy.yml", inputs={"environment": "staging", "replicas": 3})
        assert include.local == "/templates/deploy.yml"
        assert isinstance(include.inputs, GitLabCIIncludeInputs)
        assert include.inputs.inputs["environment"] == "staging"
        assert include.inputs.inputs["replicas"] == 3

    def test_include_local_with_rules(self):
        """Test local include with rules."""
        include = GitLabCIIncludeLocal(local="/templates/test.yml", rules=[{"if": "$CI_COMMIT_BRANCH == 'main'"}])
        assert include.local == "/templates/test.yml"
        assert len(include.rules) == 1
        assert include.rules[0].if_ == "$CI_COMMIT_BRANCH == 'main'"

    def test_include_local_wildcards(self):
        """Test local include with wildcards."""
        include = GitLabCIIncludeLocal(local="/templates/*.yml")
        assert include.local == "/templates/*.yml"


class TestGitLabCIIncludeProject:
    """Test GitLabCIIncludeProject model."""

    def test_include_project_simple(self):
        """Test simple project include."""
        include = GitLabCIIncludeProject(project="my-group/my-project", file="/templates/test.yml")
        assert include.project == "my-group/my-project"
        assert include.file == "/templates/test.yml"
        assert include.ref is None

    def test_include_project_with_ref(self):
        """Test project include with ref."""
        include = GitLabCIIncludeProject(project="my-group/my-project", file="/templates/test.yml", ref="v1.0.0")
        assert include.project == "my-group/my-project"
        assert include.file == "/templates/test.yml"
        assert include.ref == "v1.0.0"

    def test_include_project_multiple_files(self):
        """Test project include with multiple files."""
        include = GitLabCIIncludeProject(
            project="my-group/templates", file=["/templates/build.yml", "/templates/test.yml"]
        )
        assert include.project == "my-group/templates"
        assert include.file == ["/templates/build.yml", "/templates/test.yml"]

    def test_include_project_with_sha_ref(self):
        """Test project include with SHA ref."""
        include = GitLabCIIncludeProject(
            project="my-group/my-project", file="/templates/test.yml", ref="787123b47f14b552955ca2786bc9542ae66fee5b"
        )
        assert include.ref == "787123b47f14b552955ca2786bc9542ae66fee5b"

    def test_include_project_with_inputs(self):
        """Test project include with inputs."""
        include = GitLabCIIncludeProject(
            project="my-group/my-project", file="/templates/deploy.yml", inputs={"target": "production"}
        )
        assert isinstance(include.inputs, GitLabCIIncludeInputs)
        assert include.inputs.inputs["target"] == "production"


class TestGitLabCIIncludeRemote:
    """Test GitLabCIIncludeRemote model."""

    def test_include_remote_simple(self):
        """Test simple remote include."""
        include = GitLabCIIncludeRemote(remote="https://example.com/templates/test.yml")
        assert include.remote == "https://example.com/templates/test.yml"
        assert include.integrity is None

    def test_include_remote_with_integrity(self):
        """Test remote include with integrity check."""
        include = GitLabCIIncludeRemote(
            remote="https://example.com/templates/test.yml", integrity="sha256:abcdef1234567890"
        )
        assert include.remote == "https://example.com/templates/test.yml"
        assert include.integrity == "sha256:abcdef1234567890"

    def test_include_remote_with_rules(self):
        """Test remote include with rules."""
        include = GitLabCIIncludeRemote(
            remote="https://example.com/templates/deploy.yml", rules=[{"if": "$INCLUDE_REMOTE == 'true'"}]
        )
        assert include.remote == "https://example.com/templates/deploy.yml"
        assert len(include.rules) == 1


class TestGitLabCIIncludeTemplate:
    """Test GitLabCIIncludeTemplate model."""

    def test_include_template_simple(self):
        """Test simple template include."""
        include = GitLabCIIncludeTemplate(template="Auto-DevOps.gitlab-ci.yml")
        assert include.template == "Auto-DevOps.gitlab-ci.yml"

    def test_include_template_with_inputs(self):
        """Test template include with inputs."""
        include = GitLabCIIncludeTemplate(template="Jobs/Build.gitlab-ci.yml", inputs={"build_type": "maven"})
        assert include.template == "Jobs/Build.gitlab-ci.yml"
        assert isinstance(include.inputs, GitLabCIIncludeInputs)
        assert include.inputs.inputs["build_type"] == "maven"


class TestGitLabCIIncludeComponent:
    """Test GitLabCIIncludeComponent model."""

    def test_include_component_simple(self):
        """Test simple component include."""
        include = GitLabCIIncludeComponent(component="gitlab.com/my-org/my-component@1.0")
        assert include.component == "gitlab.com/my-org/my-component@1.0"

    def test_include_component_with_inputs(self):
        """Test component include with inputs."""
        include = GitLabCIIncludeComponent(
            component="gitlab.com/components/security-scan@2.0", inputs={"scan_type": "sast", "severity": "high"}
        )
        assert include.component == "gitlab.com/components/security-scan@2.0"
        assert include.inputs.inputs["scan_type"] == "sast"
        assert include.inputs.inputs["severity"] == "high"


class TestParseInclude:
    """Test parse_include function."""

    def test_parse_include_string(self):
        """Test parsing simple string include."""
        result = parse_include("/templates/test.yml")
        assert result == "/templates/test.yml"

    def test_parse_include_local_dict(self):
        """Test parsing local include dict."""
        result = parse_include({"local": "/templates/test.yml"})
        assert isinstance(result, GitLabCIIncludeLocal)
        assert result.local == "/templates/test.yml"

    def test_parse_include_project_dict(self):
        """Test parsing project include dict."""
        result = parse_include({"project": "my-group/my-project", "file": "/templates/test.yml", "ref": "main"})
        assert isinstance(result, GitLabCIIncludeProject)
        assert result.project == "my-group/my-project"
        assert result.file == "/templates/test.yml"
        assert result.ref == "main"

    def test_parse_include_remote_dict(self):
        """Test parsing remote include dict."""
        result = parse_include({"remote": "https://example.com/test.yml"})
        assert isinstance(result, GitLabCIIncludeRemote)
        assert result.remote == "https://example.com/test.yml"

    def test_parse_include_template_dict(self):
        """Test parsing template include dict."""
        result = parse_include({"template": "Auto-DevOps.gitlab-ci.yml"})
        assert isinstance(result, GitLabCIIncludeTemplate)
        assert result.template == "Auto-DevOps.gitlab-ci.yml"

    def test_parse_include_component_dict(self):
        """Test parsing component include dict."""
        result = parse_include({"component": "gitlab.com/components/test@1.0"})
        assert isinstance(result, GitLabCIIncludeComponent)
        assert result.component == "gitlab.com/components/test@1.0"

    def test_parse_include_list(self):
        """Test parsing list of includes."""
        result = parse_include(
            [
                "/templates/test1.yml",
                {"local": "/templates/test2.yml"},
                {"project": "my-group/my-project", "file": "test.yml"},
            ]
        )

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "/templates/test1.yml"
        assert isinstance(result[1], GitLabCIIncludeLocal)
        assert isinstance(result[2], GitLabCIIncludeProject)

    def test_parse_include_invalid_dict(self):
        """Test parsing invalid include dict."""
        with pytest.raises(ValueError) as exc_info:
            parse_include({"unknown": "value"})
        assert "Unknown include type" in str(exc_info.value)

    def test_parse_include_invalid_type(self):
        """Test parsing invalid include type."""
        with pytest.raises(ValueError) as exc_info:
            parse_include(123)
        assert "Invalid include configuration" in str(exc_info.value)


class TestIncludeComplexScenarios:
    """Test complex include scenarios."""

    def test_multiple_includes_with_rules(self):
        """Test multiple includes with different rules."""
        includes = [
            GitLabCIIncludeLocal(
                local="/templates/build.yml", rules=[{"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'"}]
            ),
            GitLabCIIncludeProject(
                project="shared/templates",
                file="/deploy.yml",
                ref="v2.0",
                rules=[{"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"}],
            ),
            GitLabCIIncludeTemplate(template="Security/SAST.gitlab-ci.yml", rules=[{"exists": ["**/*.py", "**/*.js"]}]),
        ]

        assert len(includes) == 3
        assert all(inc.rules is not None for inc in includes)

    def test_nested_include_configuration(self):
        """Test nested include configuration."""
        include = GitLabCIIncludeProject(
            project="infrastructure/ci-templates",
            file=["/base/setup.yml", "/jobs/build.yml", "/jobs/test.yml", "/jobs/deploy.yml"],
            ref="stable",
            inputs={"environment": "production", "region": "us-east-1", "replicas": 3, "enable_monitoring": True},
        )

        assert include.project == "infrastructure/ci-templates"
        assert len(include.file) == 4
        assert include.ref == "stable"
        assert include.inputs.inputs["environment"] == "production"
