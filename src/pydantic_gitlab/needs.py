"""Needs structures for GitLab CI configuration."""

import re
from typing import TYPE_CHECKING, Any, Optional, Union

from .base import GitLabCIBaseModel, GitRef, JobName

if TYPE_CHECKING:
    from .yaml_parser import GitLabReference


class GitLabCINeedsObject(GitLabCIBaseModel):
    """Needs object configuration for cross-project/pipeline dependencies."""

    job: Optional[JobName] = None
    project: Optional[str] = None
    ref: Optional[GitRef] = None
    artifacts: Optional[bool] = None
    optional: Optional[bool] = None
    pipeline: Optional[str] = None  # For parent-child pipeline relationships

    def model_post_init(self, __context: Any) -> None:
        """Validate needs configuration."""
        super().model_post_init(__context)

        # Either job or pipeline should be specified
        if not self.job and not self.pipeline:
            raise ValueError("Needs must specify either 'job' or 'pipeline'")

        # Can't specify both job and pipeline
        if self.job and self.pipeline:
            raise ValueError("Cannot specify both 'job' and 'pipeline' in needs")


# Type for needs - can be string (job name), object, or GitLabReference
GitLabCINeeds = Union[JobName, GitLabCINeedsObject, "GitLabReference"]


def _parse_needs_item(item: Any) -> GitLabCINeeds:
    """Parse a single needs item."""
    # Import here to avoid circular import
    from .yaml_parser import GitLabReference  # noqa: PLC0415

    if isinstance(item, GitLabReference):
        return item
    if isinstance(item, str):
        # Check if it's an escaped !reference string
        if item.startswith("\\!reference "):
            # Handle escaped !reference strings from YAML parsing
            match = re.match(r"\\!reference \[(.*?)\]", item)
            if match:
                path_str = match.group(1)
                # Parse the path - it should be comma-separated strings
                path_parts = [part.strip().strip("'\"") for part in path_str.split(",")]
                return GitLabReference(path_parts)
            raise ValueError(f"Invalid reference format: {item}")
        return item
    if isinstance(item, dict):
        return GitLabCINeedsObject(**item)
    raise ValueError(f"Invalid needs item: {item}")


def parse_needs(value: Union[str, dict[str, Any], list[Any]]) -> list[GitLabCINeeds]:
    """Parse needs configuration from various input formats."""
    # Import here to avoid circular import
    from .yaml_parser import GitLabReference  # noqa: PLC0415

    # If it's a GitLabReference, keep it as is for now
    # The actual resolution should happen during YAML parsing
    if isinstance(value, GitLabReference):
        # Return as a list with the reference - it will be resolved later
        return [value]

    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [GitLabCINeedsObject(**value)]
    if isinstance(value, list):
        return [_parse_needs_item(item) for item in value]
    raise ValueError(f"Invalid needs configuration: {value}")


# Rebuild to resolve forward references
from .yaml_parser import GitLabReference  # noqa: E402
