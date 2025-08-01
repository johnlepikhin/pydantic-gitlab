"""Parallel job structures for GitLab CI configuration."""

from typing import Any, Union

from pydantic import field_validator

from .base import GitLabCIBaseModel


class GitLabCIParallelMatrix(GitLabCIBaseModel):
    """Parallel matrix configuration."""

    # Matrix is a list of dictionaries with variable combinations
    matrix: list[dict[str, Union[str, list[str]]]]

    @field_validator("matrix")
    @classmethod
    def validate_matrix(cls, v: list[dict[str, Any]]) -> list[dict[str, Union[str, list[str]]]]:
        """Validate matrix configuration."""
        if not v:
            raise ValueError("Matrix cannot be empty")

        # Validate each matrix entry
        for idx, entry in enumerate(v):
            if not isinstance(entry, dict):
                raise ValueError(f"Matrix entry {idx} must be a dictionary")
            if not entry:
                raise ValueError(f"Matrix entry {idx} cannot be empty")

        return v


class GitLabCIParallelObject(GitLabCIBaseModel):
    """Parallel object configuration."""

    matrix: list[dict[str, Union[str, list[str]]]]

    @field_validator("matrix")
    @classmethod
    def validate_matrix(cls, v: list[dict[str, Any]]) -> list[dict[str, Union[str, list[str]]]]:
        """Validate matrix configuration."""
        if not v:
            raise ValueError("Matrix cannot be empty")
        return v


# Type for parallel - can be number or object with matrix
GitLabCIParallel = Union[int, GitLabCIParallelObject]


def parse_parallel(value: Union[int, dict[str, Any]]) -> GitLabCIParallel:
    """Parse parallel configuration from various input formats."""
    if isinstance(value, int):
        if value < 2 or value > 200:
            raise ValueError("Parallel value must be between 2 and 200")
        return value
    if isinstance(value, dict):
        return GitLabCIParallelObject(**value)
    raise ValueError(f"Invalid parallel configuration: {value}")
