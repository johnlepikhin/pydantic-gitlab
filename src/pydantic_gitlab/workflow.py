"""Workflow structures for GitLab CI configuration."""

from typing import Any, Optional

from pydantic import Field, field_validator

from .base import AutoCancelType, GitLabCIBaseModel
from .rules import GitLabCIRule


class GitLabCIWorkflowAutoCancel(GitLabCIBaseModel):
    """Workflow auto-cancel configuration."""

    on_new_commit: Optional[AutoCancelType] = Field(None, alias="on_new_commit")
    on_job_failure: Optional[str] = Field(None, alias="on_job_failure")  # "all" or "none"

    @field_validator("on_job_failure")
    @classmethod
    def validate_on_job_failure(cls, v: Optional[str]) -> Optional[str]:
        """Validate on_job_failure value."""
        if v is not None and v not in ["all", "none"]:
            raise ValueError("on_job_failure must be 'all' or 'none'")
        return v


class GitLabCIWorkflowRuleAutoCancel(GitLabCIBaseModel):
    """Auto-cancel configuration for workflow rules."""

    on_new_commit: Optional[AutoCancelType] = Field(None, alias="on_new_commit")
    on_job_failure: Optional[str] = Field(None, alias="on_job_failure")

    @field_validator("on_job_failure")
    @classmethod
    def validate_on_job_failure(cls, v: Optional[str]) -> Optional[str]:
        """Validate on_job_failure value."""
        if v is not None and v not in ["all", "none"]:
            raise ValueError("on_job_failure must be 'all' or 'none'")
        return v


class GitLabCIWorkflowRule(GitLabCIRule):
    """Workflow-specific rule configuration."""

    # Workflow rules can only use specific when values
    # Override parent's when field type
    auto_cancel: Optional[GitLabCIWorkflowRuleAutoCancel] = Field(None, alias="auto_cancel")

    @field_validator("when")
    @classmethod
    def validate_when(cls, v: Optional[str]) -> Optional[str]:
        """Validate when value for workflow rules."""
        if v is not None and v not in ["always", "never"]:
            raise ValueError("Workflow rules can only use 'when: always' or 'when: never'")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Skip parent validation for workflow rules."""
        # Don't call parent's model_post_init which requires conditions
        # Workflow rules can have just variables without conditions
        GitLabCIBaseModel.model_post_init(self, __context)


class GitLabCIWorkflow(GitLabCIBaseModel):
    """Workflow configuration."""

    name: Optional[str] = None
    rules: Optional[list[GitLabCIWorkflowRule]] = None
    auto_cancel: Optional[GitLabCIWorkflowAutoCancel] = Field(None, alias="auto_cancel")

    @field_validator("rules", mode="before")
    @classmethod
    def normalize_rules(cls, v: Any) -> Optional[list[GitLabCIWorkflowRule]]:
        """Normalize rules to list of GitLabCIWorkflowRule."""
        if v is None:
            return None
        if isinstance(v, dict):
            return [GitLabCIWorkflowRule(**v)]
        if isinstance(v, list):
            return [GitLabCIWorkflowRule(**rule) if isinstance(rule, dict) else rule for rule in v]
        raise ValueError(f"Invalid rules value: {v}")
