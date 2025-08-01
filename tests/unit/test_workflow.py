"""Tests for GitLab CI workflow structures."""

from pydantic_gitlab.workflow import (
    GitLabCIWorkflow,
    GitLabCIWorkflowAutoCancel,
    GitLabCIWorkflowRule,
    GitLabCIWorkflowRuleAutoCancel,
)


class TestGitLabCIWorkflowAutoCancel:
    """Test GitLabCIWorkflowAutoCancel model."""

    def test_auto_cancel_with_on_new_commit(self):
        """Test auto cancel with on_new_commit."""
        auto_cancel = GitLabCIWorkflowAutoCancel(on_new_commit="conservative")
        assert auto_cancel.on_new_commit == "conservative"
        assert auto_cancel.on_job_failure is None

    def test_auto_cancel_with_on_job_failure(self):
        """Test auto cancel with on_job_failure."""
        auto_cancel = GitLabCIWorkflowAutoCancel(on_job_failure="all")
        assert auto_cancel.on_job_failure == "all"
        assert auto_cancel.on_new_commit is None

    def test_auto_cancel_with_both(self):
        """Test auto cancel with both options."""
        auto_cancel = GitLabCIWorkflowAutoCancel(on_new_commit="interruptible", on_job_failure="none")
        assert auto_cancel.on_new_commit == "interruptible"
        assert auto_cancel.on_job_failure == "none"

    def test_auto_cancel_on_new_commit_values(self):
        """Test valid on_new_commit values."""
        valid_values = ["conservative", "interruptible", "none"]

        for value in valid_values:
            auto_cancel = GitLabCIWorkflowAutoCancel(on_new_commit=value)
            assert auto_cancel.on_new_commit == value

    def test_auto_cancel_on_job_failure_values(self):
        """Test valid on_job_failure values."""
        valid_values = ["all", "none"]

        for value in valid_values:
            auto_cancel = GitLabCIWorkflowAutoCancel(on_job_failure=value)
            assert auto_cancel.on_job_failure == value


class TestGitLabCIWorkflowRuleAutoCancel:
    """Test GitLabCIWorkflowRuleAutoCancel model."""

    def test_rule_auto_cancel_simple(self):
        """Test simple rule auto cancel."""
        auto_cancel = GitLabCIWorkflowRuleAutoCancel(on_new_commit="conservative")
        assert auto_cancel.on_new_commit == "conservative"

    def test_rule_auto_cancel_complex(self):
        """Test complex rule auto cancel."""
        auto_cancel = GitLabCIWorkflowRuleAutoCancel(on_new_commit="interruptible", on_job_failure="all")
        assert auto_cancel.on_new_commit == "interruptible"
        assert auto_cancel.on_job_failure == "all"


class TestGitLabCIWorkflowRule:
    """Test GitLabCIWorkflowRule model."""

    def test_workflow_rule_with_if(self):
        """Test workflow rule with if condition."""
        rule = GitLabCIWorkflowRule(if_="$CI_PIPELINE_SOURCE == 'merge_request_event'")
        assert rule.if_ == "$CI_PIPELINE_SOURCE == 'merge_request_event'"
        assert rule.when is None
        assert rule.variables is None

    def test_workflow_rule_with_when(self):
        """Test workflow rule with when."""
        rule = GitLabCIWorkflowRule(if_="$CI_COMMIT_BRANCH == 'main'", when="always")
        assert rule.if_ == "$CI_COMMIT_BRANCH == 'main'"
        assert rule.when == "always"

    def test_workflow_rule_with_variables(self):
        """Test workflow rule with variables."""
        rule = GitLabCIWorkflowRule(
            if_="$CI_COMMIT_TAG", variables={"DEPLOY_ENVIRONMENT": "production", "ENABLE_MONITORING": "true"}
        )
        assert rule.if_ == "$CI_COMMIT_TAG"
        assert rule.variables["DEPLOY_ENVIRONMENT"] == "production"
        assert rule.variables["ENABLE_MONITORING"] == "true"

    def test_workflow_rule_with_auto_cancel(self):
        """Test workflow rule with auto_cancel."""
        rule = GitLabCIWorkflowRule(
            if_="$CI_PIPELINE_SOURCE == 'schedule'", auto_cancel={"on_new_commit": "none", "on_job_failure": "none"}
        )
        assert rule.if_ == "$CI_PIPELINE_SOURCE == 'schedule'"
        assert isinstance(rule.auto_cancel, GitLabCIWorkflowRuleAutoCancel)
        assert rule.auto_cancel.on_new_commit == "none"
        assert rule.auto_cancel.on_job_failure == "none"

    def test_workflow_rule_with_changes(self):
        """Test workflow rule with changes."""
        rule = GitLabCIWorkflowRule(changes=["src/**/*.py", "tests/**/*.py"])
        assert rule.changes == ["src/**/*.py", "tests/**/*.py"]

    def test_workflow_rule_with_exists(self):
        """Test workflow rule with exists."""
        rule = GitLabCIWorkflowRule(exists=["Dockerfile", "docker-compose.yml"])
        assert rule.exists == ["Dockerfile", "docker-compose.yml"]

    def test_workflow_rule_complex(self):
        """Test complex workflow rule."""
        rule = GitLabCIWorkflowRule(
            if_="$CI_MERGE_REQUEST_ID",
            when="always",
            variables={"PIPELINE_TYPE": "merge_request", "RUN_TESTS": "true"},
            auto_cancel={"on_new_commit": "interruptible"},
        )

        assert rule.if_ == "$CI_MERGE_REQUEST_ID"
        assert rule.when == "always"
        assert rule.variables["PIPELINE_TYPE"] == "merge_request"
        assert rule.auto_cancel.on_new_commit == "interruptible"

    def test_workflow_rule_validation(self):
        """Test workflow rule validation."""
        # Valid - has if condition
        rule1 = GitLabCIWorkflowRule(if_="$CI_COMMIT_BRANCH")
        assert rule1.if_ is not None

        # Valid - has changes condition
        rule2 = GitLabCIWorkflowRule(changes=["*.yml"])
        assert rule2.changes is not None

        # Valid - has exists condition
        rule3 = GitLabCIWorkflowRule(exists=["README.md"])
        assert rule3.exists is not None

        # Valid - workflow rules can have just variables without conditions
        rule4 = GitLabCIWorkflowRule(variables={"DEPLOY": "true"})
        assert rule4.variables == {"DEPLOY": "true"}

        # Valid - empty workflow rule (workflow rules don't require conditions)
        rule5 = GitLabCIWorkflowRule()
        assert rule5.if_ is None
        assert rule5.changes is None
        assert rule5.exists is None


class TestGitLabCIWorkflow:
    """Test GitLabCIWorkflow model."""

    def test_workflow_with_rules_only(self):
        """Test workflow with rules only."""
        workflow = GitLabCIWorkflow(
            rules=[
                {"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'"},
                {"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"},
            ]
        )
        assert len(workflow.rules) == 2
        assert workflow.rules[0].if_ == "$CI_PIPELINE_SOURCE == 'merge_request_event'"
        assert workflow.rules[1].if_ == "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"
        assert workflow.name is None
        assert workflow.auto_cancel is None

    def test_workflow_with_name(self):
        """Test workflow with name."""
        workflow = GitLabCIWorkflow(name="Pipeline for $CI_COMMIT_REF_NAME", rules=[{"if": "$CI_COMMIT_BRANCH"}])
        assert workflow.name == "Pipeline for $CI_COMMIT_REF_NAME"

    def test_workflow_with_auto_cancel(self):
        """Test workflow with auto_cancel."""
        workflow = GitLabCIWorkflow(
            auto_cancel={"on_new_commit": "conservative", "on_job_failure": "all"},
            rules=[{"if": "$CI_PIPELINE_SOURCE == 'web'"}],
        )
        assert isinstance(workflow.auto_cancel, GitLabCIWorkflowAutoCancel)
        assert workflow.auto_cancel.on_new_commit == "conservative"
        assert workflow.auto_cancel.on_job_failure == "all"

    def test_workflow_complex(self):
        """Test complex workflow configuration."""
        workflow = GitLabCIWorkflow(
            name="$CI_PIPELINE_SOURCE pipeline for $CI_COMMIT_REF_NAME",
            auto_cancel={"on_new_commit": "interruptible"},
            rules=[
                {
                    "if": "$CI_MERGE_REQUEST_ID",
                    "variables": {"PIPELINE_TYPE": "merge_request"},
                    "auto_cancel": {"on_new_commit": "interruptible"},
                },
                {
                    "if": "$CI_COMMIT_TAG",
                    "variables": {"PIPELINE_TYPE": "release"},
                    "auto_cancel": {"on_new_commit": "none"},
                },
                {"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH", "variables": {"PIPELINE_TYPE": "main"}},
                {"when": "never"},
            ],
        )

        assert workflow.name == "$CI_PIPELINE_SOURCE pipeline for $CI_COMMIT_REF_NAME"
        assert workflow.auto_cancel.on_new_commit == "interruptible"
        assert len(workflow.rules) == 4

        # Check first rule
        assert workflow.rules[0].if_ == "$CI_MERGE_REQUEST_ID"
        assert workflow.rules[0].variables["PIPELINE_TYPE"] == "merge_request"
        assert workflow.rules[0].auto_cancel.on_new_commit == "interruptible"

        # Check second rule
        assert workflow.rules[1].if_ == "$CI_COMMIT_TAG"
        assert workflow.rules[1].variables["PIPELINE_TYPE"] == "release"
        assert workflow.rules[1].auto_cancel.on_new_commit == "none"

        # Check third rule
        assert workflow.rules[2].if_ == "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"
        assert workflow.rules[2].variables["PIPELINE_TYPE"] == "main"

        # Check fourth rule
        assert workflow.rules[3].when == "never"

    def test_workflow_rules_normalization(self):
        """Test workflow rules normalization."""
        # Single rule as dict
        workflow1 = GitLabCIWorkflow(rules={"if": "$CI_COMMIT_BRANCH"})
        assert isinstance(workflow1.rules, list)
        assert len(workflow1.rules) == 1
        assert workflow1.rules[0].if_ == "$CI_COMMIT_BRANCH"

        # Multiple rules as list
        workflow2 = GitLabCIWorkflow(rules=[{"if": "$CI_COMMIT_TAG"}, {"if": "$CI_COMMIT_BRANCH"}])
        assert len(workflow2.rules) == 2

    def test_workflow_prevent_duplicate_pipelines(self):
        """Test workflow configuration to prevent duplicate pipelines."""
        workflow = GitLabCIWorkflow(
            rules=[
                {"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'"},
                {"if": "$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS", "when": "never"},
                {"if": "$CI_COMMIT_BRANCH"},
            ]
        )

        assert len(workflow.rules) == 3
        assert workflow.rules[1].when == "never"

    def test_workflow_from_dict(self):
        """Test creating workflow from dictionary."""
        workflow_dict = {
            "name": "Custom Pipeline",
            "auto_cancel": {"on_new_commit": "conservative"},
            "rules": [{"if": "$CI_PIPELINE_SOURCE == 'schedule'", "variables": {"SCHEDULED": "true"}}],
        }

        workflow = GitLabCIWorkflow(**workflow_dict)
        assert workflow.name == "Custom Pipeline"
        assert workflow.auto_cancel.on_new_commit == "conservative"
        assert workflow.rules[0].variables["SCHEDULED"] == "true"
