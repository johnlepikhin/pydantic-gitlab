"""Include structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import FilePath, GitLabCIBaseModel, GitRef, Url
from .rules import GitLabCIRule


class GitLabCIIncludeInputs(GitLabCIBaseModel):
    """Include inputs configuration."""

    # Dynamic inputs stored as dict
    inputs: dict[str, Union[str, int, bool, list[Any]]] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        """Initialize with dynamic inputs."""
        super().__init__()
        self.inputs = data


class GitLabCIIncludeBase(GitLabCIBaseModel):
    """Base class for include configurations."""

    inputs: Optional[GitLabCIIncludeInputs] = None
    rules: Optional[list[GitLabCIRule]] = None

    @field_validator("rules", mode="before")
    @classmethod
    def normalize_rules(cls, v: Any) -> Optional[list[GitLabCIRule]]:
        """Normalize rules to list of GitLabCIRule."""
        if v is None:
            return None
        if isinstance(v, dict):
            return [GitLabCIRule(**v)]
        if isinstance(v, list):
            return [GitLabCIRule(**rule) if isinstance(rule, dict) else rule for rule in v]
        raise ValueError(f"Invalid rules value: {v}")


class GitLabCIIncludeLocal(GitLabCIIncludeBase):
    """Include local file configuration."""

    local: FilePath


class GitLabCIIncludeProject(GitLabCIIncludeBase):
    """Include project file configuration."""

    project: str
    file: Union[FilePath, list[FilePath]]
    ref: Optional[GitRef] = None

    @field_validator("file", mode="before")
    @classmethod
    def normalize_file(cls, v: Any) -> Union[str, list[str]]:
        """Keep file as is - can be string or list."""
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid file value: {v}")


class GitLabCIIncludeRemote(GitLabCIIncludeBase):
    """Include remote file configuration."""

    remote: Url
    integrity: Optional[str] = None  # SHA256 hash


class GitLabCIIncludeTemplate(GitLabCIIncludeBase):
    """Include template configuration."""

    template: str


class GitLabCIIncludeComponent(GitLabCIIncludeBase):
    """Include component configuration."""

    component: str


GitLabCIInclude = Union[
    str,  # Simple string include (local file)
    GitLabCIIncludeLocal,
    GitLabCIIncludeProject,
    GitLabCIIncludeRemote,
    GitLabCIIncludeTemplate,
    GitLabCIIncludeComponent,
]


def _parse_single_include(value: Union[str, dict[str, Any]]) -> GitLabCIInclude:
    """Parse single include item."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "local" in value:
            return GitLabCIIncludeLocal(**value)
        if "project" in value:
            return GitLabCIIncludeProject(**value)
        if "remote" in value:
            return GitLabCIIncludeRemote(**value)
        if "template" in value:
            return GitLabCIIncludeTemplate(**value)
        if "component" in value:
            return GitLabCIIncludeComponent(**value)
        raise ValueError(f"Unknown include type: {value}")
    raise ValueError(f"Invalid include item: {value}")


def parse_include(value: Union[str, dict[str, Any], list[Any]]) -> Union[GitLabCIInclude, list[GitLabCIInclude]]:
    """Parse include configuration from various input formats."""
    if isinstance(value, (str, dict)):
        return _parse_single_include(value)
    if isinstance(value, list):
        return [_parse_single_include(item) for item in value]
    raise ValueError(f"Invalid include configuration: {value}")
