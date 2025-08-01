"""Default configuration for GitLab CI."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .artifacts import GitLabCIArtifacts
from .base import Duration, GitLabCIBaseModel
from .cache import GitLabCICache
from .job import GitLabCIJobHooks
from .retry import GitLabCIRetry, parse_retry
from .services import GitLabCIImage, GitLabCIService, parse_image, parse_services


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

    after_script: Optional[list[Union[str, Any]]] = Field(None, alias="after_script")
    artifacts: Optional[GitLabCIArtifacts] = None
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
