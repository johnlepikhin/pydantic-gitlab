"""Tests for base types and enums."""

import pytest
from pydantic import Field, ValidationError

from pydantic_gitlab.base import (
    ArtifactAccessType,
    AutoCancelType,
    EnvironmentActionType,
    GitLabCIBaseModel,
    GitRef,
    GitStrategyType,
    InputType,
    JobName,
    PolicyType,
    StageName,
    StageType,
    Url,
    WhenType,
)


class TestEnums:
    """Test enum types."""

    def test_when_type_values(self):
        """Test WhenType enum values."""
        assert WhenType.ON_SUCCESS == "on_success"
        assert WhenType.ON_FAILURE == "on_failure"
        assert WhenType.ALWAYS == "always"
        assert WhenType.MANUAL == "manual"
        assert WhenType.DELAYED == "delayed"
        assert WhenType.NEVER == "never"

    def test_stage_type_values(self):
        """Test StageType enum values."""
        assert StageType.DOT_PRE == ".pre"
        assert StageType.DOT_POST == ".post"
        assert StageType.BUILD == "build"
        assert StageType.TEST == "test"
        assert StageType.DEPLOY == "deploy"

    def test_git_strategy_type_values(self):
        """Test GitStrategyType enum values."""
        assert GitStrategyType.CLONE == "clone"
        assert GitStrategyType.FETCH == "fetch"
        assert GitStrategyType.NONE == "none"

    def test_policy_type_values(self):
        """Test PolicyType enum values."""
        assert PolicyType.PULL == "pull"
        assert PolicyType.PUSH == "push"
        assert PolicyType.PULL_PUSH == "pull-push"

    def test_artifact_access_type_values(self):
        """Test ArtifactAccessType enum values."""
        assert ArtifactAccessType.DEVELOPER == "developer"
        assert ArtifactAccessType.NONE == "none"
        assert ArtifactAccessType.ALL == "all"

    def test_environment_action_type_values(self):
        """Test EnvironmentActionType enum values."""
        assert EnvironmentActionType.START == "start"
        assert EnvironmentActionType.PREPARE == "prepare"
        assert EnvironmentActionType.STOP == "stop"
        assert EnvironmentActionType.VERIFY == "verify"
        assert EnvironmentActionType.ACCESS == "access"

    def test_auto_cancel_type_values(self):
        """Test AutoCancelType enum values."""
        assert AutoCancelType.CONSERVATIVE == "conservative"
        assert AutoCancelType.INTERRUPTIBLE == "interruptible"
        assert AutoCancelType.NONE == "none"

    def test_input_type_values(self):
        """Test InputType enum values."""
        assert InputType.STRING == "string"
        assert InputType.NUMBER == "number"
        assert InputType.BOOLEAN == "boolean"


class TestTypeAliases:
    """Test type aliases."""

    def test_job_name_validation(self):
        """Test JobName type validation."""
        # Valid job names
        valid_names = [
            "build",
            "test-job",
            "deploy_production",
            "job123",
            "my-job_123",
            ".hidden-job",
        ]

        for name in valid_names:
            assert isinstance(name, JobName)

    def test_stage_name_validation(self):
        """Test StageName type validation."""
        # Valid stage names
        valid_names = [
            "build",
            "test",
            "deploy",
            ".pre",
            ".post",
            "custom-stage",
        ]

        for name in valid_names:
            assert isinstance(name, StageName)

    def test_git_ref_validation(self):
        """Test GitRef type validation."""
        # Valid git refs
        valid_refs = [
            "main",
            "develop",
            "feature/new-feature",
            "v1.0.0",
            "787123b47f14b552955ca2786bc9542ae66fee5b",
        ]

        for ref in valid_refs:
            assert isinstance(ref, GitRef)

    def test_url_validation(self):
        """Test Url type validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://gitlab.com/group/project",
            "https://example.com/path/to/file.yml",
        ]

        for url in valid_urls:
            assert isinstance(url, Url)


class TestGitLabCIBaseModel:
    """Test GitLabCIBaseModel functionality."""

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed and stored."""

        class TestModel(GitLabCIBaseModel):
            known_field: str

        # Create model with extra fields
        data = {
            "known_field": "value",
            "extra_field1": "extra_value1",
            "extra_field2": 123,
            "extra_field3": {"nested": "value"},
        }

        model = TestModel(**data)

        # Check known field
        assert model.known_field == "value"

        # Check extra fields are accessible
        assert model.extra_field1 == "extra_value1"
        assert model.extra_field2 == 123
        assert model.extra_field3 == {"nested": "value"}

    def test_model_dump_excludes_none(self):
        """Test that None values are excluded from model_dump."""

        class TestModel(GitLabCIBaseModel):
            required_field: str
            optional_field: str = None
            another_optional: int = None

        model = TestModel(required_field="value")
        dumped = model.model_dump()

        assert "required_field" in dumped
        assert "optional_field" not in dumped
        assert "another_optional" not in dumped

    def test_model_dump_with_extra_fields(self):
        """Test model_dump includes extra fields."""

        class TestModel(GitLabCIBaseModel):
            known_field: str

        model = TestModel(known_field="value", extra_field="extra_value", nested_extra={"key": "value"})

        dumped = model.model_dump()

        assert dumped["known_field"] == "value"
        assert dumped["extra_field"] == "extra_value"
        assert dumped["nested_extra"] == {"key": "value"}

    def test_populate_by_name(self):
        """Test that fields can be populated by name or alias."""

        class TestModel(GitLabCIBaseModel):
            field_with_alias: str = Field(None, alias="fieldAlias")

        # Test with field name
        model1 = TestModel(field_with_alias="value1")
        assert model1.field_with_alias == "value1"

        # Test with alias
        model2 = TestModel(fieldAlias="value2")
        assert model2.field_with_alias == "value2"

    def test_model_copy(self):
        """Test model copy functionality."""

        class TestModel(GitLabCIBaseModel):
            field1: str
            field2: int = 42

        original = TestModel(field1="value", extra_field="extra")
        copy = original.model_copy()

        assert copy.field1 == original.field1
        assert copy.field2 == original.field2
        assert copy.extra_field == original.extra_field

        # Modify copy and ensure original is not affected
        copy.field1 = "modified"
        assert original.field1 == "value"

    def test_model_validate(self):
        """Test model validation."""

        class TestModel(GitLabCIBaseModel):
            required_field: str
            optional_field: int = None

        # Valid data
        valid_data = {"required_field": "value", "extra": "allowed"}
        model = TestModel.model_validate(valid_data)
        assert model.required_field == "value"
        assert model.extra == "allowed"

        # Invalid data - missing required field
        invalid_data = {"optional_field": 123}
        with pytest.raises(ValidationError) as exc_info:
            TestModel.model_validate(invalid_data)

        assert "required_field" in str(exc_info.value)

    def test_json_schema(self):
        """Test JSON schema generation."""

        class TestModel(GitLabCIBaseModel):
            string_field: str
            int_field: int
            optional_field: str = None

        schema = TestModel.model_json_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "string_field" in schema["properties"]
        assert "int_field" in schema["properties"]
        assert "optional_field" in schema["properties"]
        assert schema["required"] == ["string_field", "int_field"]
        assert schema["additionalProperties"] is True  # Extra fields allowed
