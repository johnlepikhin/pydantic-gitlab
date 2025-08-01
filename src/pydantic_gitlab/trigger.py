"""Trigger structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import field_validator

from .base import GitLabCIBaseModel, GitRef
from .include import GitLabCIInclude, parse_include


class GitLabCITriggerSimple(GitLabCIBaseModel):
    """Simple trigger configuration with just project path."""

    project: str
    branch: Optional[GitRef] = None
    strategy: Optional[str] = None  # "depend"
    forward: Optional[dict[str, bool]] = None  # pipeline_variables, yaml_variables

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: Optional[str]) -> Optional[str]:
        """Validate trigger strategy."""
        if v is not None and v != "depend":
            raise ValueError("Trigger strategy must be 'depend'")
        return v


class GitLabCITriggerInclude(GitLabCIBaseModel):
    """Trigger configuration with include."""

    include: Union[GitLabCIInclude, list[GitLabCIInclude]]
    strategy: Optional[str] = None  # "depend"
    forward: Optional[dict[str, bool]] = None  # pipeline_variables, yaml_variables

    @field_validator("include", mode="before")
    @classmethod
    def parse_include_field(cls, v: Any) -> Union[GitLabCIInclude, list[GitLabCIInclude]]:
        """Parse include field."""
        return parse_include(v)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: Optional[str]) -> Optional[str]:
        """Validate trigger strategy."""
        if v is not None and v != "depend":
            raise ValueError("Trigger strategy must be 'depend'")
        return v


# Type for trigger - can be string (project path) or object
GitLabCITrigger = Union[str, GitLabCITriggerSimple, GitLabCITriggerInclude]


def parse_trigger(value: Union[str, dict[str, Any]]) -> GitLabCITrigger:
    """Parse trigger configuration from various input formats."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "include" in value:
            return GitLabCITriggerInclude(**value)
        if "project" in value:
            return GitLabCITriggerSimple(**value)
        raise ValueError(f"Invalid trigger configuration: {value}")
    raise ValueError(f"Invalid trigger configuration: {value}")
