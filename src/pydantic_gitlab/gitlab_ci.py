"""Main GitLab CI configuration structure."""

from typing import Any, Optional, Union

import yaml
from pydantic import Field, field_validator, model_validator

from .base import GitLabCIBaseModel, JobName, StageName
from .cache import GitLabCICache
from .default import GitLabCIDefault
from .include import GitLabCIInclude, parse_include
from .job import GitLabCIJob
from .pages import GitLabCIPages
from .spec import GitLabCISpec
from .variables import GitLabCIVariables
from .workflow import GitLabCIWorkflow


class GitLabCI(GitLabCIBaseModel):
    """Root GitLab CI configuration structure."""

    # Header section (must be separated by --- in YAML)
    spec: Optional[GitLabCISpec] = None

    # Global keywords
    cache: Optional[Union[GitLabCICache, list[GitLabCICache]]] = None
    default: Optional[GitLabCIDefault] = None
    include: Optional[Union[GitLabCIInclude, list[GitLabCIInclude]]] = None
    stages: Optional[list[StageName]] = None
    variables: Optional[GitLabCIVariables] = None
    workflow: Optional[GitLabCIWorkflow] = None

    # Jobs - stored separately from other fields
    jobs: dict[JobName, Union[GitLabCIJob, GitLabCIPages]] = Field(default_factory=dict, exclude=True)

    # Special handling for !reference tags
    references: dict[str, Any] = Field(default_factory=dict, exclude=True)

    @field_validator("include", mode="before")
    @classmethod
    def parse_include_field(cls, v: Any) -> Optional[Union[GitLabCIInclude, list[GitLabCIInclude]]]:
        """Parse include field."""
        if v is None:
            return None
        return parse_include(v)

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(cls, v: Any) -> Optional[list[StageName]]:
        """Normalize stages to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Flatten nested lists if any
            result = []
            for item in v:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result
        raise ValueError(f"Invalid stages value: {v}")

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables_field(cls, v: Any) -> Optional[GitLabCIVariables]:
        """Parse variables field."""
        if v is None:
            return None
        if isinstance(v, dict):
            return GitLabCIVariables(**v)
        if isinstance(v, GitLabCIVariables):
            return v
        raise ValueError(f"Invalid variables value: {v}")

    @model_validator(mode="before")
    @classmethod
    def extract_jobs(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Extract job definitions from the configuration."""
        # Known global keywords that are not jobs
        global_keywords = {
            "cache",
            "default",
            "include",
            "stages",
            "variables",
            "workflow",
            "spec",
            # Also exclude any keys starting with dot (like .pre, .post)
        }

        # Extract references (keys starting with .)
        references: dict[str, Any] = {}
        jobs: dict[str, Union[GitLabCIJob, GitLabCIPages]] = {}

        # Process all keys
        for key, value in list(values.items()):
            if key.startswith(".") and key not in [".pre", ".post"]:
                # This is a reference/template job
                references[key] = value
                # Remove from main values
                values.pop(key, None)
            elif key not in global_keywords and isinstance(value, dict):
                # Check if this looks like a job definition
                job_keywords = {"script", "run", "trigger", "extends", "stage", "when", "rules", "only", "except"}
                if any(k in value for k in job_keywords):
                    # Special handling for pages job
                    if key == "pages":
                        jobs[key] = GitLabCIPages(**value)
                    else:
                        jobs[key] = GitLabCIJob(**value)
                    # Remove from main values
                    values.pop(key, None)

        # Add extracted data to values
        values["jobs"] = jobs
        values["references"] = references

        return values

    def get_job(self, name: str) -> Optional[GitLabCIJob]:
        """Get job by name."""
        return self.jobs.get(name)

    def add_job(self, name: str, job: GitLabCIJob) -> None:
        """Add or update a job."""
        self.jobs[name] = job

    def remove_job(self, name: str) -> Optional[GitLabCIJob]:
        """Remove a job and return it."""
        return self.jobs.pop(name, None)

    def get_all_stages(self) -> list[str]:
        """Get all stages including defaults and job-defined stages."""
        # Start with defined stages or defaults
        stages = list(self.stages) if self.stages else [".pre", "build", "test", "deploy", ".post"]

        # Add any stages defined in jobs
        for job in self.jobs.values():
            if job.stage and job.stage not in stages:
                stages.append(job.stage)

        return stages

    def validate_job_dependencies(self) -> list[str]:
        """Validate that job dependencies are valid."""
        errors = []
        job_names = set(self.jobs.keys())

        for job_name, job in self.jobs.items():
            # Check needs
            if job.needs:
                for need in job.needs:
                    if isinstance(need, str) and need not in job_names:
                        errors.append(f"Job '{job_name}' needs non-existent job '{need}'")

            # Check dependencies
            if job.dependencies:
                for dep in job.dependencies:
                    if dep not in job_names:
                        errors.append(f"Job '{job_name}' depends on non-existent job '{dep}'")

            # Check environment on_stop
            if job.environment and isinstance(job.environment, dict):
                on_stop = job.environment.get("on_stop")
                if on_stop and on_stop not in job_names:
                    errors.append(f"Job '{job_name}' environment on_stop references non-existent job '{on_stop}'")

        return errors

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Custom serialization to include jobs in output."""
        # Get base model data
        data = super().model_dump(**kwargs)

        # Handle variables - flatten if it's GitLabCIVariables
        if "variables" in data and self.variables is not None:
            data["variables"] = self.variables.model_dump(**kwargs)

        # Add jobs to the output
        for job_name, job in self.jobs.items():
            data[job_name] = job.model_dump(**kwargs)

        # Add references
        for ref_name, ref_value in self.references.items():
            data[ref_name] = ref_value

        return data

    def model_dump_yaml(self, **kwargs: Any) -> str:
        """Serialize to YAML format."""
        data = self.model_dump(**kwargs)

        # Handle spec section separately if present
        spec_data = data.pop("spec", None)

        yaml_parts = []

        # Add spec section with separator if present
        if spec_data:
            yaml_parts.append(yaml.dump({"spec": spec_data}, default_flow_style=False, sort_keys=False))
            yaml_parts.append("---")

        # Add main configuration
        if data:
            yaml_parts.append(yaml.dump(data, default_flow_style=False, sort_keys=False))

        return "\n".join(yaml_parts)
