"""Needs structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from .base import GitLabCIBaseModel, GitRef, JobName


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


# Type for needs - can be string (job name) or object
GitLabCINeeds = Union[JobName, GitLabCINeedsObject]


def parse_needs(value: Union[str, dict[str, Any], list[Any]]) -> list[GitLabCINeeds]:
    """Parse needs configuration from various input formats."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [GitLabCINeedsObject(**value)]
    if isinstance(value, list):
        result: list[GitLabCINeeds] = []
        for item in value:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(GitLabCINeedsObject(**item))
            else:
                raise ValueError(f"Invalid needs item: {item}")
        return result
    raise ValueError(f"Invalid needs configuration: {value}")
