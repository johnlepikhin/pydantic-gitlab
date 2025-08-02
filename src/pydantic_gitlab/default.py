"""Default configuration for GitLab CI."""

from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import Field, field_validator, model_validator

from .artifacts import GitLabCIArtifacts
from .base import Duration, GitLabCIBaseModel
from .cache import GitLabCICache
from .job import GitLabCIJobHooks
from .retry import GitLabCIRetry, parse_retry
from .services import GitLabCIImage, GitLabCIService, parse_image, parse_services

if TYPE_CHECKING:
    from .yaml_parser import GitLabReference


class GitLabCIIdToken(GitLabCIBaseModel):
    """ID token configuration."""

    aud: Optional[Union[str, list[str]]] = None

    @field_validator("aud", mode="before")
    @classmethod
    def normalize_aud(cls, v: Any) -> Optional[list[str]]:
        """Normalize audience to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")


class GitLabCIDefault(GitLabCIBaseModel):
    """Default configuration for all jobs."""

    model_config = {"arbitrary_types_allowed": True}  # noqa: RUF012

    after_script: Optional[list[Union[str, Any]]] = Field(None, alias="after_script")
    artifacts: Optional[Union[GitLabCIArtifacts, "GitLabReference"]] = None
    before_script: Optional[list[Union[str, Any]]] = Field(None, alias="before_script")
    cache: Optional[Union[GitLabCICache, list[GitLabCICache]]] = None
    hooks: Optional[GitLabCIJobHooks] = None
    id_tokens: Optional[dict[str, GitLabCIIdToken]] = Field(None, alias="id_tokens")
    image: Optional[GitLabCIImage] = None
    interruptible: Optional[bool] = None
    retry: Optional[GitLabCIRetry] = None
    services: Optional[list[GitLabCIService]] = None
    tags: Optional[list[str]] = None
    timeout: Optional[Duration] = None

    @field_validator("after_script", mode="before")
    @classmethod
    def normalize_after_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize after_script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            # Import here to avoid circular import
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if any(isinstance(item, GitLabReference) for item in v):
                # Keep GitLabReference objects as is - they should be resolved during YAML parsing
                return v
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("before_script", mode="before")
    @classmethod
    def normalize_before_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize before_script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            # Import here to avoid circular import
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if any(isinstance(item, GitLabReference) for item in v):
                # Keep GitLabReference objects as is - they should be resolved during YAML parsing
                return v
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("artifacts", mode="before")
    @classmethod
    def parse_artifacts_field(cls, v: Any) -> Any:
        """Parse artifacts field."""
        if v is None:
            return None
        # Check if it's a GitLabReference
        from .yaml_parser import GitLabReference  # noqa: PLC0415

        if isinstance(v, GitLabReference):
            # Keep GitLabReference objects as is
            return v
        # If it's already a GitLabCIArtifacts instance, return it
        if isinstance(v, GitLabCIArtifacts):
            return v
        # If it's a dict, create GitLabCIArtifacts from it
        if isinstance(v, dict):
            return GitLabCIArtifacts(**v)
        raise ValueError(f"Invalid artifacts value: {v}")

    @field_validator("cache", mode="before")
    @classmethod
    def parse_cache_field(cls, v: Any) -> Optional[Union[GitLabCICache, list[GitLabCICache]]]:
        """Parse cache field."""
        if v is None:
            return None
        if isinstance(v, list):
            return [GitLabCICache(**c) if isinstance(c, dict) else c for c in v]
        if isinstance(v, dict):
            return GitLabCICache(**v)
        raise ValueError(f"Invalid cache value: {v}")

    @field_validator("image", mode="before")
    @classmethod
    def parse_image_field(cls, v: Any) -> Optional[GitLabCIImage]:
        """Parse image field."""
        if v is None:
            return None
        return parse_image(v)

    @field_validator("retry", mode="before")
    @classmethod
    def parse_retry_field(cls, v: Any) -> Optional[GitLabCIRetry]:
        """Parse retry field."""
        if v is None:
            return None
        return parse_retry(v)

    @field_validator("services", mode="before")
    @classmethod
    def parse_services_field(cls, v: Any) -> Optional[list[GitLabCIService]]:
        """Parse services field."""
        if v is None:
            return None
        return parse_services(v)

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: Any) -> Optional[list[str]]:
        """Normalize tags to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("id_tokens", mode="before")
    @classmethod
    def parse_id_tokens(cls, v: Any) -> Optional[dict[str, GitLabCIIdToken]]:
        """Parse id_tokens configuration."""
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("id_tokens must be a dictionary")

        result = {}
        for key, value in v.items():
            if isinstance(value, dict):
                result[key] = GitLabCIIdToken(**value)
            else:
                raise ValueError(f"Invalid id_token configuration for '{key}'")
        return result

    @model_validator(mode="before")
    @classmethod
    def validate_artifacts_field(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate and transform artifacts field."""
        if "artifacts" in values and values["artifacts"] is not None:
            v = values["artifacts"]
            # Check if it's a GitLabReference
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if isinstance(v, GitLabReference):
                # Keep GitLabReference objects as is
                pass
            elif isinstance(v, GitLabCIArtifacts):
                # Already the right type
                pass
            elif isinstance(v, dict):
                # Convert dict to GitLabCIArtifacts
                values["artifacts"] = GitLabCIArtifacts(**v)
            else:
                raise ValueError(f"Invalid artifacts value: {v}")
        return values


# Rebuild model to resolve forward references
from .yaml_parser import GitLabReference  # noqa: E402

GitLabCIDefault.model_rebuild()
