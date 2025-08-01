"""Artifacts structures for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import ArtifactAccessType, ArtifactName, Duration, GitLabCIBaseModel, WhenType


class GitLabCIArtifactsReports(GitLabCIBaseModel):
    """Artifacts reports configuration."""

    junit: Optional[Union[str, list[str]]] = None
    coverage_report: Optional[Union[str, dict[str, Union[str, list[str]]]]] = Field(None, alias="coverage_report")
    codequality: Optional[Union[str, list[str]]] = None
    sast: Optional[Union[str, list[str]]] = None
    dependency_scanning: Optional[Union[str, list[str]]] = Field(None, alias="dependency_scanning")
    container_scanning: Optional[Union[str, list[str]]] = Field(None, alias="container_scanning")
    dast: Optional[Union[str, list[str]]] = None
    license_management: Optional[Union[str, list[str]]] = Field(None, alias="license_management")
    license_scanning: Optional[Union[str, list[str]]] = Field(None, alias="license_scanning")
    performance: Optional[Union[str, list[str]]] = None
    requirements: Optional[Union[str, list[str]]] = None
    secret_detection: Optional[Union[str, list[str]]] = Field(None, alias="secret_detection")
    terraform: Optional[Union[str, list[str]]] = None
    accessibility: Optional[Union[str, list[str]]] = None
    cluster_image_scanning: Optional[Union[str, list[str]]] = Field(None, alias="cluster_image_scanning")
    requirements_v2: Optional[Union[str, list[str]]] = Field(None, alias="requirements_v2")
    api_fuzzing: Optional[Union[str, list[str]]] = Field(None, alias="api_fuzzing")
    browser_performance: Optional[Union[str, list[str]]] = Field(None, alias="browser_performance")
    coverage_fuzzing: Optional[Union[str, list[str]]] = Field(None, alias="coverage_fuzzing")
    load_performance: Optional[Union[str, list[str]]] = Field(None, alias="load_performance")
    metrics: Optional[Union[str, list[str]]] = None
    repository_xray: Optional[Union[str, list[str]]] = Field(None, alias="repository_xray")
    cyclonedx: Optional[Union[str, list[str]]] = None

    @field_validator(
        "junit",
        "codequality",
        "sast",
        "dependency_scanning",
        "container_scanning",
        "dast",
        "license_management",
        "license_scanning",
        "performance",
        "requirements",
        "secret_detection",
        "terraform",
        "accessibility",
        "cluster_image_scanning",
        "requirements_v2",
        "api_fuzzing",
        "browser_performance",
        "coverage_fuzzing",
        "load_performance",
        "metrics",
        "repository_xray",
        "cyclonedx",
        mode="before",
    )
    @classmethod
    def normalize_report_paths(cls, v: Any) -> Optional[Union[str, list[str]]]:
        """Normalize report paths to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")


class GitLabCIArtifacts(GitLabCIBaseModel):
    """Artifacts configuration."""

    paths: Optional[list[str]] = None
    exclude: Optional[list[str]] = None
    expire_in: Optional[Duration] = Field(None, alias="expire_in")
    expose_as: Optional[str] = Field(None, alias="expose_as")
    name: Optional[ArtifactName] = None
    public: Optional[bool] = None
    access: Optional[ArtifactAccessType] = None
    reports: Optional[GitLabCIArtifactsReports] = None
    untracked: Optional[bool] = None
    when: Optional[WhenType] = None

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

    @field_validator("exclude", mode="before")
    @classmethod
    def normalize_exclude(cls, v: Any) -> Optional[list[str]]:
        """Normalize exclude to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    def model_post_init(self, __context: Any) -> None:
        """Validate artifacts configuration."""
        super().model_post_init(__context)

        # Can't use both public and access
        if self.public is not None and self.access is not None:
            raise ValueError("Cannot use both 'public' and 'access' in artifacts configuration")

        # expose_as requires paths
        if self.expose_as is not None and not self.paths:
            raise ValueError("'expose_as' requires 'paths' to be defined")
