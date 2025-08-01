"""Job structure for GitLab CI configuration."""

from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .artifacts import GitLabCIArtifacts
from .base import (
    CoverageRegex,
    Duration,
    GitLabCIBaseModel,
    GitStrategyType,
    JobName,
    StageName,
    VariableName,
    VariableValue,
    WhenType,
)
from .cache import GitLabCICache
from .environment import GitLabCIEnvironment, parse_environment
from .needs import GitLabCINeeds, parse_needs
from .parallel import GitLabCIParallel, parse_parallel
from .retry import GitLabCIRetry, parse_retry
from .rules import GitLabCIRule
from .services import GitLabCIImage, GitLabCIService, parse_image, parse_services
from .trigger import GitLabCITrigger, parse_trigger


class GitLabCIJobVariables(GitLabCIBaseModel):
    """Job-level variables configuration."""

    # Simple key-value pairs
    variables: dict[VariableName, VariableValue] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        """Initialize with dynamic variables."""
        super().__init__()
        self.variables = data

    def __getitem__(self, key: str) -> VariableValue:
        """Get variable value."""
        return self.variables[key]

    def __setitem__(self, key: str, value: VariableValue) -> None:
        """Set variable value."""
        self.variables[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if variable exists."""
        return key in self.variables

    def get(self, key: str, default: Any = None) -> Any:
        """Get variable value with default."""
        return self.variables.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Get variable value by attribute name."""
        if name in self.variables:
            return self.variables[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class GitLabCIJobHooks(GitLabCIBaseModel):
    """Job hooks configuration."""

    pre_get_sources_script: Optional[list[str]] = Field(None, alias="pre_get_sources_script")

    @field_validator("pre_get_sources_script", mode="before")
    @classmethod
    def normalize_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")


class GitLabCIJobInherit(GitLabCIBaseModel):
    """Job inherit configuration."""

    default: Optional[Union[bool, list[str]]] = None
    variables: Optional[Union[bool, list[VariableName]]] = None

    @field_validator("default", mode="before")
    @classmethod
    def normalize_default(cls, v: Any) -> Optional[Union[bool, list[str]]]:
        """Normalize default inheritance."""
        if v is None or isinstance(v, bool):
            return v
        if isinstance(v, list):
            return v
        return None

    @field_validator("variables", mode="before")
    @classmethod
    def normalize_variables(cls, v: Any) -> Optional[Union[bool, list[str]]]:
        """Normalize variables inheritance."""
        if v is None or isinstance(v, bool):
            return v
        if isinstance(v, list):
            return v
        return None


class GitLabCIJobRelease(GitLabCIBaseModel):
    """Job release configuration."""

    tag_name: str = Field(alias="tag_name")
    description: str  # Required according to GitLab docs
    tag_message: Optional[str] = Field(None, alias="tag_message")
    name: Optional[str] = None
    ref: Optional[str] = None
    milestones: Optional[list[str]] = None
    released_at: Optional[str] = Field(None, alias="released_at")
    assets: Optional[dict[str, Any]] = None


class GitLabCIJobDastConfiguration(GitLabCIBaseModel):
    """DAST configuration for job."""

    site_profile: str = Field(alias="site_profile")
    scanner_profile: str = Field(alias="scanner_profile")


class GitLabCIJobIdentity(GitLabCIBaseModel):
    """Job identity configuration for authentication."""

    # Identity configuration is provider-specific
    # Keeping it flexible as Dict for now
    config: dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data: Any) -> None:
        """Initialize with provider-specific config."""
        super().__init__()
        self.config = data


class GitLabCIJob(GitLabCIBaseModel):
    """GitLab CI job configuration."""

    # Core job definition
    script: Optional[list[Union[str, Any]]] = None
    run: Optional[list[str]] = None  # Alternative to script
    extends: Optional[Union[str, list[str]]] = None
    stage: Optional[StageName] = None
    only: Optional[Any] = None  # Deprecated but still used
    except_: Optional[Any] = Field(None, alias="except")  # Deprecated but still used

    # Job control
    rules: Optional[Union[list[GitLabCIRule], Any]] = None
    when: Optional[WhenType] = None
    allow_failure: Optional[Union[bool, dict[str, list[int]]]] = Field(None, alias="allow_failure")
    manual_confirmation: Optional[str] = Field(None, alias="manual_confirmation")
    start_in: Optional[Duration] = Field(None, alias="start_in")  # For delayed jobs
    timeout: Optional[Duration] = None
    resource_group: Optional[str] = Field(None, alias="resource_group")
    interruptible: Optional[bool] = None

    # Scripts and hooks
    before_script: Optional[list[Union[str, Any]]] = Field(None, alias="before_script")
    after_script: Optional[list[Union[str, Any]]] = Field(None, alias="after_script")
    hooks: Optional[GitLabCIJobHooks] = None

    # Dependencies and artifacts
    needs: Optional[list[GitLabCINeeds]] = None
    dependencies: Optional[list[JobName]] = None
    artifacts: Optional[GitLabCIArtifacts] = None

    # Environment and deployment
    environment: Optional[Union[str, GitLabCIEnvironment]] = None
    release: Optional[GitLabCIJobRelease] = None

    # Docker configuration
    image: Optional[GitLabCIImage] = None
    services: Optional[list[GitLabCIService]] = None

    # Caching
    cache: Optional[Union[GitLabCICache, list[GitLabCICache]]] = None

    # Variables
    variables: Optional[Union[dict[VariableName, VariableValue], GitLabCIJobVariables, Any]] = None

    # Runner configuration
    tags: Optional[list[str]] = None

    # Git configuration
    git_strategy: Optional[GitStrategyType] = Field(None, alias="git_strategy")
    git_submodule_strategy: Optional[str] = Field(None, alias="git_submodule_strategy")
    git_submodule_paths: Optional[list[str]] = Field(None, alias="git_submodule_paths")
    git_depth: Optional[int] = Field(None, alias="git_depth")
    git_clean_flags: Optional[str] = Field(None, alias="git_clean_flags")

    # Advanced features
    parallel: Optional[GitLabCIParallel] = None
    trigger: Optional[GitLabCITrigger] = None
    inherit: Optional[GitLabCIJobInherit] = None
    retry: Optional[GitLabCIRetry] = None
    coverage: Optional[CoverageRegex] = None
    dast_configuration: Optional[GitLabCIJobDastConfiguration] = Field(None, alias="dast_configuration")
    identity: Optional[GitLabCIJobIdentity] = None

    # Pages-specific
    pages: Optional[dict[str, Any]] = None  # For pages jobs

    @field_validator("script", mode="before")
    @classmethod
    def normalize_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            # Import here to avoid circular import
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if any(isinstance(item, GitLabReference) for item in v):
                # Keep GitLabReference objects as is - they should be resolved during YAML parsing
                return v
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("run", mode="before")
    @classmethod
    def normalize_run(cls, v: Any) -> Optional[list[str]]:
        """Normalize run to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("extends", mode="before")
    @classmethod
    def normalize_extends(cls, v: Any) -> Optional[list[str]]:
        """Normalize extends to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("before_script", mode="before")
    @classmethod
    def normalize_before_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize before_script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            # Import here to avoid circular import
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if any(isinstance(item, GitLabReference) for item in v):
                # Keep GitLabReference objects as is - they should be resolved during YAML parsing
                return v
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("after_script", mode="before")
    @classmethod
    def normalize_after_script(cls, v: Any) -> Optional[list[str]]:
        """Normalize after_script to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            # Import here to avoid circular import
            from .yaml_parser import GitLabReference  # noqa: PLC0415

            if any(isinstance(item, GitLabReference) for item in v):
                # Keep GitLabReference objects as is - they should be resolved during YAML parsing
                return v
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: Any) -> Optional[list[str]]:
        """Normalize tags to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("dependencies", mode="before")
    @classmethod
    def normalize_dependencies(cls, v: Any) -> Optional[list[str]]:
        """Normalize dependencies to list."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid value: {v}")

    @field_validator("rules", mode="before")
    @classmethod
    def normalize_rules(cls, v: Any) -> Any:
        """Normalize rules to list of GitLabCIRule."""
        if v is None:
            return None
        # Check if it's a GitLabReference
        from .yaml_parser import GitLabReference  # noqa: PLC0415

        if isinstance(v, GitLabReference):
            # Keep GitLabReference objects as is
            return v
        if isinstance(v, dict):
            return [GitLabCIRule(**v)]
        if isinstance(v, list):
            # Check if list contains GitLabReference objects
            if any(isinstance(item, GitLabReference) for item in v):
                # Keep list with GitLabReference objects as is
                return v
            return [GitLabCIRule(**rule) if isinstance(rule, dict) else rule for rule in v]
        raise ValueError(f"Invalid rules value: {v}")

    @field_validator("needs", mode="before")
    @classmethod
    def parse_needs_field(cls, v: Any) -> Optional[list[GitLabCINeeds]]:
        """Parse needs field."""
        if v is None:
            return None
        return parse_needs(v)

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment_field(cls, v: Any) -> Optional[GitLabCIEnvironment]:
        """Parse environment field."""
        if v is None:
            return None
        return parse_environment(v)

    @field_validator("image", mode="before")
    @classmethod
    def parse_image_field(cls, v: Any) -> Optional[GitLabCIImage]:
        """Parse image field."""
        if v is None:
            return None
        return parse_image(v)

    @field_validator("services", mode="before")
    @classmethod
    def parse_services_field(cls, v: Any) -> Optional[list[GitLabCIService]]:
        """Parse services field."""
        if v is None:
            return None
        return parse_services(v)

    @field_validator("cache", mode="before")
    @classmethod
    def parse_cache_field(cls, v: Any) -> Optional[Union[GitLabCICache, list[GitLabCICache]]]:
        """Parse cache field."""
        if v is None:
            return None
        if isinstance(v, list):
            return [GitLabCICache(**c) if isinstance(c, dict) else c for c in v]
        if isinstance(v, dict):
            return GitLabCICache(**v)
        raise ValueError(f"Invalid cache value: {v}")

    @field_validator("parallel", mode="before")
    @classmethod
    def parse_parallel_field(cls, v: Any) -> Optional[GitLabCIParallel]:
        """Parse parallel field."""
        if v is None:
            return None
        return parse_parallel(v)

    @field_validator("trigger", mode="before")
    @classmethod
    def parse_trigger_field(cls, v: Any) -> Optional[GitLabCITrigger]:
        """Parse trigger field."""
        if v is None:
            return None
        return parse_trigger(v)

    @field_validator("retry", mode="before")
    @classmethod
    def parse_retry_field(cls, v: Any) -> Optional[GitLabCIRetry]:
        """Parse retry field."""
        if v is None:
            return None
        return parse_retry(v)

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables_field(cls, v: Any) -> Any:
        """Parse variables field."""
        if v is None:
            return None
        # Check if it's a GitLabReference
        from .yaml_parser import GitLabReference  # noqa: PLC0415

        if isinstance(v, GitLabReference):
            # Keep GitLabReference objects as is
            return v
        if isinstance(v, GitLabCIJobVariables):
            return v
        if isinstance(v, dict):
            # Check if dict contains GitLabReference values
            if any(isinstance(val, GitLabReference) for val in v.values()):
                # Keep dict with GitLabReference values as is
                return v
            return GitLabCIJobVariables(**v)
        raise ValueError(f"Invalid variables value: {v}")

    def model_post_init(self, __context: Any) -> None:
        """Validate job configuration."""
        super().model_post_init(__context)

        # Can't have both script and run
        if self.script and self.run:
            raise ValueError("Job cannot have both 'script' and 'run'")

        # Can't use needs with dependencies
        if self.needs and self.dependencies:
            raise ValueError("Job cannot use both 'needs' and 'dependencies'")

        # Manual confirmation only for manual jobs
        if self.manual_confirmation and self.when != WhenType.MANUAL:
            raise ValueError("'manual_confirmation' can only be used with 'when: manual'")

        # start_in only for delayed jobs
        if self.start_in and self.when != WhenType.DELAYED:
            raise ValueError("'start_in' can only be used with 'when: delayed'")
