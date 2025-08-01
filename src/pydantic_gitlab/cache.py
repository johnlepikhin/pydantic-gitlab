"""Cache structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import CacheKey, GitLabCIBaseModel, PolicyType, WhenType


class GitLabCICacheKey(GitLabCIBaseModel):
    """Cache key configuration."""

    key: Optional[str] = None  # Direct key string
    files: Optional[list[str]] = None
    prefix: Optional[str] = None

    @field_validator("files", mode="before")
    @classmethod
    def validate_files(cls, v: Any) -> Optional[list[str]]:
        """Validate and normalize files list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            if len(v) > 2:
                raise ValueError("cache:key:files can have a maximum of 2 files")
            return v
        raise ValueError(f"Invalid files value: {v}")

    def model_post_init(self, __context: Any) -> None:
        """Validate cache key configuration."""
        super().model_post_init(__context)

        # Must have either key or files
        if self.key is None and self.files is None:
            raise ValueError("Cache key must have either 'key' or 'files'")

        # Cannot have both key and files
        if self.key is not None and self.files is not None:
            raise ValueError("Cache key cannot specify both 'key' and 'files'")

        # Prefix requires files
        if self.prefix is not None and self.files is None:
            raise ValueError("'prefix' can only be used with 'files'")


class GitLabCICache(GitLabCIBaseModel):
    """Cache configuration."""

    paths: Optional[list[str]] = None
    key: Optional[Union[CacheKey, GitLabCICacheKey]] = None
    untracked: Optional[bool] = None
    unprotect: Optional[bool] = None
    when: Optional[WhenType] = None
    policy: Optional[PolicyType] = None
    fallback_keys: Optional[list[CacheKey]] = Field(None, alias="fallback_keys")

    @field_validator("paths", mode="before")
    @classmethod
    def normalize_paths(cls, v: Any) -> Optional[list[str]]:
        """Normalize paths to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("key", mode="before")
    @classmethod
    def parse_key(cls, v: Any) -> Optional[Union[CacheKey, GitLabCICacheKey]]:
        """Parse cache key."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return GitLabCICacheKey(**v)
        raise ValueError(f"Invalid key value: {v}")

    @field_validator("fallback_keys", mode="before")
    @classmethod
    def normalize_fallback_keys(cls, v: Any) -> Optional[list[CacheKey]]:
        """Normalize fallback_keys to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    def model_post_init(self, __context: Any) -> None:
        """Validate cache configuration."""
        super().model_post_init(__context)

        # Validate cache key format
        if isinstance(self.key, str) and ("/" in self.key or self.key in {".", ".."}):
            raise ValueError(f"Invalid cache key: {self.key}. Key cannot contain '/' or be '.' or '..'")

        # At least paths should be defined for cache to work
        if not self.paths and not self.untracked:
            raise ValueError("Cache must define either 'paths' or 'untracked: true'")
