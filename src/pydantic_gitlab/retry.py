"""Retry structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import field_validator

from .base import GitLabCIBaseModel


class GitLabCIRetryObject(GitLabCIBaseModel):
    """Retry configuration object."""

    max: Optional[int] = None  # 0, 1, or 2
    when: Optional[Union[str, list[str]]] = None  # Retry conditions

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: Optional[int]) -> Optional[int]:
        """Validate max retry attempts."""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("Retry max must be 0, 1, or 2")
        return v

    @field_validator("when", mode="before")
    @classmethod
    def normalize_when(cls, v: Any) -> Optional[list[str]]:
        """Normalize when to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid when value: {v}")


# Type for retry - can be number or object
GitLabCIRetry = Union[int, GitLabCIRetryObject]


def parse_retry(value: Union[int, dict[str, Any]]) -> GitLabCIRetry:
    """Parse retry configuration from various input formats."""
    if isinstance(value, int):
        if value not in [0, 1, 2]:
            raise ValueError("Retry value must be 0, 1, or 2")
        return value
    if isinstance(value, dict):
        return GitLabCIRetryObject(**value)
    raise ValueError(f"Invalid retry configuration: {value}")
