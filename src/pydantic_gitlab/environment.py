"""Environment structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field

from .base import Duration, EnvironmentActionType, EnvironmentName, GitLabCIBaseModel, JobName, Url


class GitLabCIKubernetes(GitLabCIBaseModel):
    """Kubernetes configuration for environment."""

    namespace: Optional[str] = None
    agent: Optional[Union[str, dict[str, Any]]] = None
    flux_resource_path: Optional[str] = Field(None, alias="flux_resource_path")


class GitLabCIEnvironment(GitLabCIBaseModel):
    """Environment configuration."""

    name: EnvironmentName
    url: Optional[Url] = None
    on_stop: Optional[JobName] = Field(None, alias="on_stop")
    action: Optional[EnvironmentActionType] = None
    auto_stop_in: Optional[Duration] = Field(None, alias="auto_stop_in")
    kubernetes: Optional[GitLabCIKubernetes] = None
    deployment_tier: Optional[str] = Field(None, alias="deployment_tier")

    @classmethod
    def from_string(cls, name: str) -> "GitLabCIEnvironment":
        """Create environment from string name."""
        return cls(name=name, on_stop=None, auto_stop_in=None, deployment_tier=None)

    def model_post_init(self, __context: Any) -> None:
        """Validate environment configuration."""
        super().model_post_init(__context)

        # auto_stop_in cannot be used with stop action
        if self.auto_stop_in is not None and self.action == EnvironmentActionType.STOP:
            raise ValueError("'auto_stop_in' cannot be used with action: stop")


def parse_environment(value: Union[str, dict[str, Any]]) -> GitLabCIEnvironment:
    """Parse environment configuration from various input formats."""
    if isinstance(value, str):
        return GitLabCIEnvironment.from_string(value)
    if isinstance(value, dict):
        return GitLabCIEnvironment(**value)
    raise ValueError(f"Invalid environment configuration: {value}")
