"""Spec structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import GitLabCIBaseModel, InputType


class GitLabCISpecInput(GitLabCIBaseModel):
    """Single input specification."""

    default: Optional[Union[str, int, bool, list[Any]]] = None
    description: Optional[str] = None
    options: Optional[list[Union[str, int]]] = None
    regex: Optional[str] = None
    type: Optional[InputType] = None

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[list[Any]]) -> Optional[list[Union[str, int]]]:
        """Validate options list."""
        if v is not None and len(v) > 50:
            raise ValueError("Input can have maximum 50 options")
            # Options can only be used with string or number types
            # This will be validated in model_post_init
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate input specification."""
        super().model_post_init(__context)

        # Validate type compatibility
        if self.options is not None:
            if self.type == InputType.BOOLEAN:
                raise ValueError("Options cannot be used with boolean type")
            if self.type == InputType.ARRAY:
                raise ValueError("Options cannot be used with array type")

        # Regex only works with string type
        if self.regex is not None and self.type not in [None, InputType.STRING]:
            raise ValueError("Regex can only be used with string type")

        # Validate default value against options
        if self.default is not None and self.options is not None and self.default not in self.options:
            raise ValueError(f"Default value '{self.default}' is not in options")

        # Validate default value type
        if self.default is not None and self.type is not None:
            if self.type == InputType.STRING and not isinstance(self.default, str):
                raise ValueError("Default value must be a string for string type")
            if self.type == InputType.NUMBER and not isinstance(self.default, (int, float)):
                raise ValueError("Default value must be a number for number type")
            if self.type == InputType.BOOLEAN and not isinstance(self.default, bool):
                raise ValueError("Default value must be a boolean for boolean type")
            if self.type == InputType.ARRAY and not isinstance(self.default, list):
                raise ValueError("Default value must be an array for array type")


class GitLabCISpecInputs(GitLabCIBaseModel):
    """Inputs specification for included configurations."""

    # Dynamic inputs stored as dict
    inputs: dict[str, GitLabCISpecInput] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        """Initialize with input specifications."""
        # Parse inputs
        parsed_inputs = {}
        for key, value in data.items():
            if key != "inputs":  # Skip the wrapper key if present
                if value is None:
                    # Simple input without configuration
                    parsed_inputs[key] = GitLabCISpecInput()
                elif isinstance(value, dict):
                    parsed_inputs[key] = GitLabCISpecInput(**value)
                else:
                    raise ValueError(f"Invalid input specification for '{key}'")

        # Handle case where data contains 'inputs' key
        if "inputs" in data and isinstance(data["inputs"], dict):
            for key, value in data["inputs"].items():
                if value is None:
                    parsed_inputs[key] = GitLabCISpecInput()
                elif isinstance(value, dict):
                    parsed_inputs[key] = GitLabCISpecInput(**value)
                else:
                    raise ValueError(f"Invalid input specification for '{key}'")

        super().__init__()
        self.inputs = parsed_inputs


class GitLabCISpec(GitLabCIBaseModel):
    """Spec section for GitLab CI configuration files."""

    inputs: Optional[GitLabCISpecInputs] = None

    @field_validator("inputs", mode="before")
    @classmethod
    def parse_inputs(cls, v: Any) -> Optional[GitLabCISpecInputs]:
        """Parse inputs specification."""
        if v is None:
            return None
        if isinstance(v, dict):
            return GitLabCISpecInputs(**v)
        if isinstance(v, GitLabCISpecInputs):
            return v
        raise ValueError(f"Invalid inputs value: {v}")
