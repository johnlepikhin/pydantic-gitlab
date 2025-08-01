"""Services and image structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import GitLabCIBaseModel, ImageName, ServiceName, VariableName, VariableValue


class GitLabCIDockerConfig(GitLabCIBaseModel):
    """Docker configuration for image."""

    platform: Optional[str] = None
    user: Optional[str] = None


class GitLabCIPullPolicy(GitLabCIBaseModel):
    """Pull policy configuration for image."""

    policy: Optional[Union[str, list[str]]] = None

    @field_validator("policy", mode="before")
    @classmethod
    def normalize_policy(cls, v: Any) -> Optional[list[str]]:
        """Normalize policy to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid policy value: {v}")


class GitLabCIImageObject(GitLabCIBaseModel):
    """Image configuration object."""

    name: ImageName
    entrypoint: Optional[list[str]] = None
    docker: Optional[GitLabCIDockerConfig] = None
    pull_policy: Optional[Union[str, list[str], GitLabCIPullPolicy]] = Field(None, alias="pull_policy")

    @field_validator("entrypoint", mode="before")
    @classmethod
    def normalize_entrypoint(cls, v: Any) -> Optional[list[str]]:
        """Normalize entrypoint to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid entrypoint value: {v}")

    @field_validator("pull_policy", mode="before")
    @classmethod
    def parse_pull_policy(cls, v: Any) -> Optional[Union[str, list[str], GitLabCIPullPolicy]]:
        """Parse pull policy."""
        if v is None:
            return None
        if isinstance(v, str):
            return v  # Keep as string
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            return GitLabCIPullPolicy(**v)
        raise ValueError(f"Invalid pull_policy value: {v}")


class GitLabCIServiceObject(GitLabCIBaseModel):
    """Service configuration object."""

    name: ServiceName
    alias: Optional[str] = None
    entrypoint: Optional[list[str]] = None
    command: Optional[list[str]] = None
    variables: Optional[dict[VariableName, VariableValue]] = None
    pull_policy: Optional[Union[str, list[str], GitLabCIPullPolicy]] = Field(None, alias="pull_policy")

    @field_validator("entrypoint", mode="before")
    @classmethod
    def normalize_entrypoint(cls, v: Any) -> Optional[list[str]]:
        """Normalize entrypoint to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("command", mode="before")
    @classmethod
    def normalize_command(cls, v: Any) -> Optional[list[str]]:
        """Normalize command to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("pull_policy", mode="before")
    @classmethod
    def parse_pull_policy(cls, v: Any) -> Optional[Union[str, list[str], GitLabCIPullPolicy]]:
        """Parse pull policy."""
        if v is None:
            return None
        if isinstance(v, str):
            return v  # Keep as string
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            return GitLabCIPullPolicy(**v)
        raise ValueError(f"Invalid pull_policy value: {v}")


# Union types for image and service
GitLabCIImage = Union[ImageName, GitLabCIImageObject]
GitLabCIService = Union[ServiceName, GitLabCIServiceObject]


def parse_image(value: Union[str, dict[str, Any]]) -> GitLabCIImage:
    """Parse image configuration from various input formats."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return GitLabCIImageObject(**value)
    raise ValueError(f"Invalid image configuration: {value}")


def parse_service(value: Union[str, dict[str, Any]]) -> GitLabCIService:
    """Parse service configuration from various input formats."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return GitLabCIServiceObject(**value)
    raise ValueError(f"Invalid service configuration: {value}")


def parse_services(value: Union[str, list[Any], dict[str, Any]]) -> list[GitLabCIService]:
    """Parse services configuration from various input formats."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [GitLabCIServiceObject(**value)]
    if isinstance(value, list):
        return [parse_service(item) for item in value]
    raise ValueError(f"Invalid services configuration: {value}")
