"""Pages job structure for GitLab CI configuration."""

from typing import Any, Optional

from pydantic import Field

from .base import Duration, GitLabCIBaseModel
from .job import GitLabCIJob


class GitLabCIPagesConfig(GitLabCIBaseModel):
    """Pages-specific configuration."""

    path_prefix: Optional[str] = Field(None, alias="path_prefix")
    expire_in: Optional[Duration] = Field(None, alias="expire_in")
    publish: Optional[str] = None  # Directory to publish (default: public)


class GitLabCIPages(GitLabCIJob):
    """Special pages job configuration."""

    def model_post_init(self, __context: Any) -> None:
        """Validate pages job configuration."""
        super().model_post_init(__context)

        # Pages job should have artifacts with public path
        if self.artifacts and self.artifacts.paths:
            # In GitLab 17.10+, public is automatically added if not present
            # But we don't enforce this as it depends on GitLab version
            pass
