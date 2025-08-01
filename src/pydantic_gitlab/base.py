"""Base types and enums for GitLab CI configuration."""

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class GitLabCIBaseModel(BaseModel):
    """Base model for all GitLab CI structures."""

    model_config = {"extra": "allow", "populate_by_name": True}

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Dump model excluding None values by default."""
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    # Store unknown fields
    extra_fields: Optional[dict[str, Any]] = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        """Store extra fields after model initialization."""
        if self.__pydantic_extra__:
            extra = {}
            for key, value in self.__pydantic_extra__.items():
                extra[key] = value
            if extra:
                self.extra_fields = extra

    @classmethod
    def _handle_gitlab_reference(cls, v: Any) -> Any:
        """Handle GitLabReference objects in validators.

        This is a helper method for validators to handle GitLabReference objects.
        Import is done inside the method to avoid circular imports.

        Returns the value as-is if it contains GitLabReference, otherwise None.
        """
        from .yaml_parser import GitLabReference  # noqa: PLC0415

        if isinstance(v, GitLabReference):
            return v
        if isinstance(v, dict) and any(isinstance(val, GitLabReference) for val in v.values()):
            return v
        if isinstance(v, list) and any(isinstance(item, GitLabReference) for item in v):
            return v
        return None


class WhenType(str, Enum):
    """When to run job."""

    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    NEVER = "never"
    MANUAL = "manual"
    DELAYED = "delayed"


class PolicyType(str, Enum):
    """Cache policy type."""

    PULL = "pull"
    PUSH = "push"
    PULL_PUSH = "pull-push"


class GitStrategyType(str, Enum):
    """Git strategy type."""

    CLONE = "clone"
    FETCH = "fetch"
    NONE = "none"


class ArtifactAccessType(str, Enum):
    """Artifact access level."""

    ALL = "all"
    DEVELOPER = "developer"
    NONE = "none"


class EnvironmentActionType(str, Enum):
    """Environment action type."""

    START = "start"
    PREPARE = "prepare"
    STOP = "stop"
    VERIFY = "verify"
    ACCESS = "access"


class AutoCancelType(str, Enum):
    """Auto cancel type for workflows."""

    CONSERVATIVE = "conservative"
    INTERRUPTIBLE = "interruptible"
    NONE = "none"


class InputType(str, Enum):
    """Input parameter type."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"


class StageType(str, Enum):
    """Predefined stage types."""

    DOT_PRE = ".pre"
    DOT_POST = ".post"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"


# Type aliases for common fields
Duration = str  # e.g., "1 day", "2 hours 20 minutes", "never"
Percentage = str  # e.g., "50%"
CoverageRegex = str  # Regular expression for coverage
EnvironmentName = str  # Environment name
JobName = str  # Job name
StageName = str  # Stage name
Url = str  # URL string
FilePath = str  # File path
GitRef = str  # Git reference (branch, tag, SHA)
ImageName = str  # Docker image name
ServiceName = str  # Service name
VariableName = str  # Variable name
VariableValue = Union[str, int, bool, float]  # Variable value
CacheKey = str  # Cache key
ArtifactName = str  # Artifact name
