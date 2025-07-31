"""Tests for GitLab CI variables."""

from pydantic_gitlab.variables import (
    GitLabCIVariableObject,
    GitLabCIVariables,
)


class TestGitLabCIVariableObject:
    """Test GitLabCIVariableObject model."""

    def test_simple_variable(self):
        """Test simple variable object."""
        var = GitLabCIVariableObject(value="test-value")
        assert var.value == "test-value"
        assert var.description is None
        assert var.expand is None
        assert var.options is None

    def test_variable_with_description(self):
        """Test variable with description."""
        var = GitLabCIVariableObject(value="prod", description="Environment name")
        assert var.value == "prod"
        assert var.description == "Environment name"

    def test_variable_with_expand(self):
        """Test variable with expand option."""
        var = GitLabCIVariableObject(value="$CI_COMMIT_REF_NAME-$CI_JOB_ID", expand=False)
        assert var.value == "$CI_COMMIT_REF_NAME-$CI_JOB_ID"
        assert var.expand is False

    def test_variable_with_options(self):
        """Test variable with options."""
        var = GitLabCIVariableObject(value="development", options=["development", "staging", "production"])
        assert var.value == "development"
        assert var.options == ["development", "staging", "production"]

    def test_variable_value_types(self):
        """Test different value types."""
        # String value
        var1 = GitLabCIVariableObject(value="string-value")
        assert var1.value == "string-value"

        # Integer value
        var2 = GitLabCIVariableObject(value=42)
        assert var2.value == 42

        # Boolean value
        var3 = GitLabCIVariableObject(value=True)
        assert var3.value is True

        # Float value
        var4 = GitLabCIVariableObject(value=3.14)
        assert var4.value == 3.14

    def test_complex_variable(self):
        """Test complex variable with all fields."""
        var = GitLabCIVariableObject(
            value="staging",
            description="Deployment environment",
            expand=True,
            options=["development", "staging", "production"],
        )

        dumped = var.model_dump()
        assert dumped["value"] == "staging"
        assert dumped["description"] == "Deployment environment"
        assert dumped["expand"] is True
        assert dumped["options"] == ["development", "staging", "production"]


class TestGitLabCIVariable:
    """Test GitLabCIVariable union type."""

    def test_string_variable(self):
        """Test variable as string."""
        var = "simple-value"
        assert isinstance(var, str)

    def test_integer_variable(self):
        """Test variable as integer."""
        var = 123
        assert isinstance(var, int)

    def test_boolean_variable(self):
        """Test variable as boolean."""
        var = True
        assert isinstance(var, bool)

    def test_object_variable(self):
        """Test variable as object."""
        var = GitLabCIVariableObject(value="complex", description="Complex variable")
        assert isinstance(var, GitLabCIVariableObject)
        assert var.value == "complex"


class TestGitLabCIVariables:
    """Test GitLabCIVariables model."""

    def test_empty_variables(self):
        """Test empty variables object."""
        vars = GitLabCIVariables()
        assert vars.model_dump(exclude_none=True) == {}

    def test_simple_variables(self):
        """Test simple string variables."""
        vars = GitLabCIVariables(VAR1="value1", VAR2="value2", DEBUG="true")

        assert vars.VAR1 == "value1"
        assert vars.VAR2 == "value2"
        assert vars.DEBUG == "true"

    def test_mixed_type_variables(self):
        """Test variables with mixed types."""
        vars = GitLabCIVariables(STRING_VAR="text", INT_VAR=42, BOOL_VAR=True, FLOAT_VAR=3.14)

        assert vars.STRING_VAR == "text"
        assert vars.INT_VAR == 42
        assert vars.BOOL_VAR is True
        assert vars.FLOAT_VAR == 3.14

    def test_object_variables(self):
        """Test variables as objects."""
        vars = GitLabCIVariables(
            SIMPLE="simple-value",
            COMPLEX={"value": "complex-value", "description": "A complex variable", "expand": False},
        )

        assert vars.SIMPLE == "simple-value"
        assert isinstance(vars.COMPLEX, GitLabCIVariableObject)
        assert vars.COMPLEX.value == "complex-value"
        assert vars.COMPLEX.description == "A complex variable"
        assert vars.COMPLEX.expand is False

    def test_variable_with_options(self):
        """Test variable with options."""
        vars = GitLabCIVariables(
            ENVIRONMENT={
                "value": "staging",
                "description": "Target environment",
                "options": ["development", "staging", "production"],
            }
        )

        assert vars.ENVIRONMENT.value == "staging"
        assert vars.ENVIRONMENT.options == ["development", "staging", "production"]

    def test_dynamic_variable_access(self):
        """Test dynamic variable access."""
        vars = GitLabCIVariables(VAR1="value1", VAR2="value2")

        # Access via attribute
        assert vars.VAR1 == "value1"

        # Access via getattr
        assert vars.VAR2 == "value2"

        # Check if variable exists
        assert hasattr(vars, "VAR1")
        assert not hasattr(vars, "VAR3")

    def test_variables_with_special_names(self):
        """Test variables with special characters in names."""
        vars = GitLabCIVariables()

        # Variables with underscores
        vars.MY_VARIABLE = "value"
        assert vars.MY_VARIABLE == "value"

        # Variables with numbers
        vars.VAR_123 = "value123"
        assert vars.VAR_123 == "value123"

    def test_from_dict(self):
        """Test creating variables from dictionary."""
        vars_dict = {
            "DATABASE_URL": "postgres://localhost/mydb",
            "API_KEY": "secret-key",
            "DEBUG": True,
            "MAX_RETRIES": 3,
            "DEPLOY_ENV": {"value": "production", "description": "Deployment environment"},
        }

        vars = GitLabCIVariables(**vars_dict)
        assert vars.DATABASE_URL == "postgres://localhost/mydb"
        assert vars.API_KEY == "secret-key"
        assert vars.DEBUG is True
        assert vars.MAX_RETRIES == 3
        assert isinstance(vars.DEPLOY_ENV, GitLabCIVariableObject)
        assert vars.DEPLOY_ENV.value == "production"

    def test_model_dump(self):
        """Test model dump serialization."""
        vars = GitLabCIVariables(SIMPLE="value", COMPLEX={"value": "complex", "description": "Description"})

        dumped = vars.model_dump()
        assert dumped["SIMPLE"] == "value"
        assert isinstance(dumped["COMPLEX"], dict)
        assert dumped["COMPLEX"]["value"] == "complex"
        assert dumped["COMPLEX"]["description"] == "Description"

    def test_gitlab_predefined_variables(self):
        """Test common GitLab predefined variable patterns."""
        vars = GitLabCIVariables(
            DOCKER_IMAGE="$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG",
            DEPLOY_URL="https://$CI_ENVIRONMENT_SLUG.example.com",
            CACHE_KEY="$CI_JOB_NAME-$CI_COMMIT_REF_SLUG",
        )

        assert vars.DOCKER_IMAGE == "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG"
        assert vars.DEPLOY_URL == "https://$CI_ENVIRONMENT_SLUG.example.com"
        assert vars.CACHE_KEY == "$CI_JOB_NAME-$CI_COMMIT_REF_SLUG"

    def test_extra_fields(self):
        """Test that any variable name is allowed."""
        vars = GitLabCIVariables(STANDARD_VAR="value", custom_var="custom", _private_var="private", var123="numeric")

        assert vars.STANDARD_VAR == "value"
        assert vars.custom_var == "custom"
        assert vars._private_var == "private"
        assert vars.var123 == "numeric"

    def test_null_values(self):
        """Test handling of null values."""
        vars = GitLabCIVariables(VAR1="value", VAR2=None)

        # None values should be excluded in dump
        dumped = vars.model_dump()
        assert "VAR1" in dumped
        assert "VAR2" not in dumped
