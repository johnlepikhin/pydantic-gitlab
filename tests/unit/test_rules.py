"""Tests for GitLab CI rules."""

import pytest
from pydantic import ValidationError

from pydantic_gitlab.rules import (
    GitLabCIRule,
    GitLabCIRulesChanges,
    GitLabCIRulesExists,
    GitLabCIRulesIf,
)


class TestGitLabCIRulesIf:
    """Test GitLabCIRulesIf model."""

    def test_simple_if_expression(self):
        """Test simple if expression."""
        rule = GitLabCIRulesIf(condition="$CI_COMMIT_BRANCH == 'main'")
        assert rule.condition == "$CI_COMMIT_BRANCH == 'main'"

    def test_complex_if_expressions(self):
        """Test complex if expressions."""
        expressions = [
            "$CI_PIPELINE_SOURCE == 'merge_request_event'",
            "$CI_COMMIT_TAG =~ /^v\\d+\\.\\d+\\.\\d+$/",
            "$CI_COMMIT_MESSAGE =~ /skip-tests/ && $CI_COMMIT_BRANCH == 'main'",
            "$CUSTOM_VARIABLE == 'true' || $OTHER_VARIABLE != 'false'",
        ]

        for expr in expressions:
            rule = GitLabCIRulesIf(condition=expr)
            assert rule.condition == expr


class TestGitLabCIRulesChanges:
    """Test GitLabCIRulesChanges model."""

    def test_single_path_as_string(self):
        """Test single path as string."""
        rule = GitLabCIRulesChanges(paths=["src/**/*.py"])
        assert rule.paths == ["src/**/*.py"]

    def test_multiple_paths_as_list(self):
        """Test multiple paths as list."""
        paths = ["src/**/*.py", "tests/**/*.py", "*.md"]
        rule = GitLabCIRulesChanges(paths=paths)
        assert rule.paths == paths

    def test_compare_to(self):
        """Test compare_to field."""
        rule = GitLabCIRulesChanges(paths=["README.md"], compare_to="main")
        assert rule.paths == ["README.md"]
        assert rule.compare_to == "main"

    def test_compare_to_ref(self):
        """Test changes with compare_to."""
        rule = GitLabCIRulesChanges(paths=["src/**/*"], compare_to="refs/heads/main")
        assert rule.paths == ["src/**/*"]
        assert rule.compare_to == "refs/heads/main"


class TestGitLabCIRulesExists:
    """Test GitLabCIRulesExists model."""

    def test_single_path_as_list(self):
        """Test single path as list."""
        rule = GitLabCIRulesExists(paths=["Dockerfile"])
        assert rule.paths == ["Dockerfile"]

    def test_multiple_paths_as_list(self):
        """Test multiple paths as list."""
        paths = ["Dockerfile", "docker-compose.yml", "*.dockerfile"]
        rule = GitLabCIRulesExists(paths=paths)
        assert rule.paths == paths

    def test_exists_with_project(self):
        """Test exists with project reference."""
        rule = GitLabCIRulesExists(paths=["package.json"], project="my-group/my-project")
        assert rule.paths == ["package.json"]
        assert rule.project == "my-group/my-project"

    def test_glob_patterns(self):
        """Test glob patterns in exists."""
        patterns = [
            "**/*.yml",
            "src/**/test_*.py",
            "docs/**/*.md",
        ]
        rule = GitLabCIRulesExists(paths=patterns)
        assert rule.paths == patterns


class TestGitLabCIRule:
    """Test GitLabCIRule model."""

    def test_rule_with_if(self):
        """Test rule with if condition."""
        rule = GitLabCIRule(if_="$CI_COMMIT_BRANCH == 'main'")
        assert rule.if_ == "$CI_COMMIT_BRANCH == 'main'"
        assert rule.when is None
        assert rule.allow_failure is None

    def test_rule_with_changes(self):
        """Test rule with changes condition."""
        rule = GitLabCIRule(changes=["src/**/*.py", "tests/**/*.py"])
        assert isinstance(rule.changes, list)
        assert rule.changes == ["src/**/*.py", "tests/**/*.py"]

    def test_rule_with_exists(self):
        """Test rule with exists condition."""
        rule = GitLabCIRule(exists=["Dockerfile"])
        assert isinstance(rule.exists, list)
        assert rule.exists == ["Dockerfile"]

    def test_rule_with_when(self):
        """Test rule with when action."""
        rule = GitLabCIRule(if_="$CI_PIPELINE_SOURCE == 'schedule'", when="always")
        assert rule.if_ == "$CI_PIPELINE_SOURCE == 'schedule'"
        assert rule.when == "always"

    def test_rule_with_variables(self):
        """Test rule with variables."""
        variables = {"DEPLOY_ENV": "production", "DEBUG": "false"}
        rule = GitLabCIRule(if_="$CI_COMMIT_BRANCH == 'main'", variables=variables)
        assert rule.variables == variables

    def test_rule_with_allow_failure(self):
        """Test rule with allow_failure."""
        rule = GitLabCIRule(if_="$CI_COMMIT_TAG", allow_failure=True)
        assert rule.allow_failure is True

    def test_rule_with_needs(self):
        """Test rule with needs."""
        needs = ["build-job", "test-job"]
        rule = GitLabCIRule(if_="$CI_COMMIT_BRANCH", needs=needs)
        assert rule.needs == needs

    def test_complex_rule(self):
        """Test complex rule with multiple conditions."""
        rule = GitLabCIRule(
            if_="$CI_MERGE_REQUEST_ID",
            changes={"paths": ["src/**/*"], "compare_to": "refs/heads/main"},
            when="manual",
            allow_failure=False,
            variables={"RUN_TESTS": "true"},
        )

        assert rule.if_ == "$CI_MERGE_REQUEST_ID"
        assert isinstance(rule.changes, GitLabCIRulesChanges)
        assert rule.when == "manual"
        assert rule.allow_failure is False
        assert rule.variables == {"RUN_TESTS": "true"}

    def test_rule_from_dict(self):
        """Test creating rule from dictionary."""
        rule_dict = {"if": "$CI_COMMIT_BRANCH == 'main'", "when": "always", "variables": {"DEPLOY": "true"}}

        rule = GitLabCIRule(**rule_dict)
        assert rule.if_ == "$CI_COMMIT_BRANCH == 'main'"
        assert rule.when == "always"
        assert rule.variables == {"DEPLOY": "true"}

    def test_multiple_conditions(self):
        """Test rule with multiple conditions."""
        rule = GitLabCIRule(
            if_="$CI_PIPELINE_SOURCE == 'merge_request_event'", changes=["src/**/*.py"], exists=["tests/**/*.py"]
        )

        assert rule.if_ is not None
        assert rule.changes is not None
        assert rule.exists is not None

    def test_rule_validation(self):
        """Test rule must have at least one condition."""
        # Valid - has if condition
        rule1 = GitLabCIRule(if_="$CI_COMMIT_BRANCH")
        assert rule1.if_ is not None

        # Valid - has changes condition
        rule2 = GitLabCIRule(changes=["*.py"])
        assert rule2.changes is not None

        # Valid - has exists condition
        rule3 = GitLabCIRule(exists=["Dockerfile"])
        assert rule3.exists is not None

        # Invalid - no conditions
        with pytest.raises(ValidationError) as exc_info:
            GitLabCIRule()

        assert "at least one condition" in str(exc_info.value).lower()

    def test_changes_with_advanced_options(self):
        """Test changes with advanced options."""
        rule = GitLabCIRule(changes={"paths": ["src/**/*", "lib/**/*"], "compare_to": "refs/heads/develop"})

        assert isinstance(rule.changes, GitLabCIRulesChanges)
        assert rule.changes.paths == ["src/**/*", "lib/**/*"]
        assert rule.changes.compare_to == "refs/heads/develop"

    def test_interruptible(self):
        """Test rule with interruptible."""
        rule = GitLabCIRule(if_="$CI_COMMIT_BRANCH", interruptible=True)
        assert rule.interruptible is True

    def test_model_dump(self):
        """Test model serialization."""
        rule = GitLabCIRule(
            if_="$CI_COMMIT_TAG", when="on_success", variables={"TAG_DEPLOY": "true"}, allow_failure=False
        )

        dumped = rule.model_dump(exclude_none=True, by_alias=True)
        assert dumped["if"] == "$CI_COMMIT_TAG"
        assert dumped["when"] == "on_success"
        assert dumped["variables"] == {"TAG_DEPLOY": "true"}
        assert dumped["allow_failure"] is False
