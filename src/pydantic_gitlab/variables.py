"""Variables structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import GitLabCIBaseModel, VariableName, VariableValue


class GitLabCIVariableObject(GitLabCIBaseModel):
    """Variable object with additional properties."""

    value: VariableValue
    description: Optional[str] = None
    expand: Optional[bool] = None
    options: Optional[list[str]] = None

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate options list."""
        if v is not None and len(v) > 50:
            raise ValueError("Variable can have maximum 50 options")
        return v


# Top-level variables can be either simple string or object
GitLabCIVariable = Union[VariableValue, GitLabCIVariableObject]


class GitLabCIVariables(GitLabCIBaseModel):
    """Top-level variables configuration."""

    # Store variables as dict
    variables: dict[VariableName, GitLabCIVariable] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        """Initialize with variables."""
        # Parse each variable
        parsed_vars: dict[str, GitLabCIVariable] = {}
        for key, value in data.items():
            if value is None:
                # Skip None values
                continue
            if isinstance(value, dict) and any(k in value for k in ["value", "description", "expand", "options"]):
                parsed_vars[key] = GitLabCIVariableObject(**value)
            else:
                parsed_vars[key] = value

        super().__init__()
        self.variables = parsed_vars

    def __getitem__(self, key: str) -> GitLabCIVariable:
        """Get variable by key."""
        return self.variables[key]

    def __setitem__(self, key: str, value: GitLabCIVariable) -> None:
        """Set variable by key."""
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get variable value with default."""
        if key in self.variables:
            var = self.variables[key]
            if isinstance(var, GitLabCIVariableObject):
                return var.value
            return var
        return default

    def __getattr__(self, name: str) -> Any:
        """Get variable value by attribute name."""
        if name in self.variables:
            return self.variables[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set variable value by attribute name."""
        if name in [
            "variables",
            "extra_fields",
            "model_config",
            "model_fields",
            "model_computed_fields",
        ] or name.startswith("_"):
            # Let pydantic handle its own attributes
            super().__setattr__(name, value)
        else:
            # Store as a variable
            if not hasattr(self, "variables"):
                super().__setattr__("variables", {})
            if isinstance(value, (str, int, bool, float, GitLabCIVariableObject)):
                self.variables[name] = value
            else:
                raise ValueError(f"Invalid variable value type: {type(value)}")

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Custom serialization to flatten variables."""
        # Return the variables dict directly, not wrapped
        result: dict[str, Any] = {}
        for key, value in self.variables.items():
            if isinstance(value, GitLabCIVariableObject):
                # Convert object to dict
                obj_dict = value.model_dump(**kwargs)
                result[key] = obj_dict
            else:
                result[key] = value
        return result
