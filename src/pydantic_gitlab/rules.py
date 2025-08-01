"""Rules structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field

from .base import GitLabCIBaseModel, VariableName, VariableValue, WhenType


class GitLabCIRulesChanges(GitLabCIBaseModel):
    """Rules changes configuration."""

    paths: Optional[list[str]] = None
    compare_to: Optional[str] = Field(None, alias="compare_to")


class GitLabCIRulesIf(GitLabCIBaseModel):
    """Rules if condition."""

    # The condition is just a string expression
    condition: str


class GitLabCIRulesExists(GitLabCIBaseModel):
    """Rules exists configuration."""

    paths: list[str]
    project: Optional[str] = None
    ref: Optional[str] = None


class GitLabCIRule(GitLabCIBaseModel):
    """Single rule configuration."""

    # Conditions (at least one should be present)
    if_: Optional[str] = Field(None, alias="if")
    changes: Optional[Union[list[str], GitLabCIRulesChanges]] = None
    exists: Optional[Union[list[str], GitLabCIRulesExists]] = None

    # Actions
    when: Optional[WhenType] = None
    allow_failure: Optional[Union[bool, dict[str, list[int]]]] = Field(None, alias="allow_failure")
    variables: Optional[dict[VariableName, VariableValue]] = None

    # Job-specific rule options
    needs: Optional[Any] = None  # Will be defined properly in job.py
    interruptible: Optional[bool] = None
    start_in: Optional[str] = Field(None, alias="start_in")  # For delayed jobs

    def model_post_init(self, __context: Any) -> None:
        """Validate that at least one condition is present."""
        super().model_post_init(__context)
        if not any([self.if_, self.changes, self.exists]) and self.when is None:
            raise ValueError("Rule must have at least one condition (if, changes, exists) or 'when' field")
