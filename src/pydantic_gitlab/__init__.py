"""Pydantic GitLab - A modern Python library for parsing GitLab CI YAML files."""

from .artifacts import GitLabCIArtifacts, GitLabCIArtifactsReports
from .base import (
    ArtifactAccessType,
    AutoCancelType,
    EnvironmentActionType,
    GitLabCIBaseModel,
    GitStrategyType,
    InputType,
    PolicyType,
    StageType,
    WhenType,
)
from .cache import GitLabCICache, GitLabCICacheKey
from .default import GitLabCIDefault, GitLabCIIdToken
from .environment import GitLabCIEnvironment, GitLabCIKubernetes
from .gitlab_ci import GitLabCI
from .include import (
    GitLabCIInclude,
    GitLabCIIncludeComponent,
    GitLabCIIncludeLocal,
    GitLabCIIncludeProject,
    GitLabCIIncludeRemote,
    GitLabCIIncludeTemplate,
)
from .job import (
    GitLabCIJob,
    GitLabCIJobDastConfiguration,
    GitLabCIJobHooks,
    GitLabCIJobIdentity,
    GitLabCIJobInherit,
    GitLabCIJobRelease,
    GitLabCIJobVariables,
)
from .needs import GitLabCINeeds, GitLabCINeedsObject
from .pages import GitLabCIPages, GitLabCIPagesConfig
from .parallel import GitLabCIParallel, GitLabCIParallelMatrix, GitLabCIParallelObject
from .retry import GitLabCIRetry, GitLabCIRetryObject
from .rules import (
    GitLabCIRule,
    GitLabCIRulesChanges,
    GitLabCIRulesExists,
    GitLabCIRulesIf,
)
from .services import (
    GitLabCIDockerConfig,
    GitLabCIImage,
    GitLabCIImageObject,
    GitLabCIPullPolicy,
    GitLabCIService,
    GitLabCIServiceObject,
)
from .spec import GitLabCISpec, GitLabCISpecInput, GitLabCISpecInputs
from .trigger import GitLabCITrigger, GitLabCITriggerInclude, GitLabCITriggerSimple
from .variables import GitLabCIVariable, GitLabCIVariableObject, GitLabCIVariables
from .workflow import (
    GitLabCIWorkflow,
    GitLabCIWorkflowAutoCancel,
    GitLabCIWorkflowRule,
    GitLabCIWorkflowRuleAutoCancel,
)
from .yaml_parser import (
    GitLabReference,
    dump_gitlab_yaml,
    parse_gitlab_yaml,
    safe_dump_gitlab_yaml,
    safe_load_gitlab_yaml,
)

__version__ = "0.2.1"

__all__ = [
    "ArtifactAccessType",
    "AutoCancelType",
    "EnvironmentActionType",
    "GitLabCI",
    "GitLabCIArtifacts",
    "GitLabCIArtifactsReports",
    "GitLabCIBaseModel",
    "GitLabCICache",
    "GitLabCICacheKey",
    "GitLabCIDefault",
    "GitLabCIDockerConfig",
    "GitLabCIEnvironment",
    "GitLabCIIdToken",
    "GitLabCIImage",
    "GitLabCIImageObject",
    "GitLabCIInclude",
    "GitLabCIIncludeComponent",
    "GitLabCIIncludeLocal",
    "GitLabCIIncludeProject",
    "GitLabCIIncludeRemote",
    "GitLabCIIncludeTemplate",
    "GitLabCIJob",
    "GitLabCIJobDastConfiguration",
    "GitLabCIJobHooks",
    "GitLabCIJobIdentity",
    "GitLabCIJobInherit",
    "GitLabCIJobRelease",
    "GitLabCIJobVariables",
    "GitLabCIKubernetes",
    "GitLabCINeeds",
    "GitLabCINeedsObject",
    "GitLabCIPages",
    "GitLabCIPagesConfig",
    "GitLabCIParallel",
    "GitLabCIParallelMatrix",
    "GitLabCIParallelObject",
    "GitLabCIPullPolicy",
    "GitLabCIRetry",
    "GitLabCIRetryObject",
    "GitLabCIRule",
    "GitLabCIRulesChanges",
    "GitLabCIRulesExists",
    "GitLabCIRulesIf",
    "GitLabCIService",
    "GitLabCIServiceObject",
    "GitLabCISpec",
    "GitLabCISpecInput",
    "GitLabCISpecInputs",
    "GitLabCITrigger",
    "GitLabCITriggerInclude",
    "GitLabCITriggerSimple",
    "GitLabCIVariable",
    "GitLabCIVariableObject",
    "GitLabCIVariables",
    "GitLabCIWorkflow",
    "GitLabCIWorkflowAutoCancel",
    "GitLabCIWorkflowRule",
    "GitLabCIWorkflowRuleAutoCancel",
    "GitLabReference",
    "GitStrategyType",
    "InputType",
    "PolicyType",
    "StageType",
    "WhenType",
    "__version__",
    "dump_gitlab_yaml",
    "parse_gitlab_yaml",
    "safe_dump_gitlab_yaml",
    "safe_load_gitlab_yaml",
]
