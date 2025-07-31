"""Tests for GitLab CI environments."""

from pydantic_gitlab.environment import GitLabCIEnvironment, GitLabCIKubernetes


class TestGitLabCIKubernetes:
    """Test GitLabCIKubernetes model."""

    def test_minimal_kubernetes(self):
        """Test minimal Kubernetes configuration."""
        k8s = GitLabCIKubernetes(namespace="production")
        assert k8s.namespace == "production"

    def test_kubernetes_with_all_fields(self):
        """Test Kubernetes with all fields."""
        k8s = GitLabCIKubernetes(
            namespace="staging-$CI_COMMIT_REF_SLUG",
            service_account_overwrite="custom-sa",
            proxy_url="https://proxy.example.com",
        )
        assert k8s.namespace == "staging-$CI_COMMIT_REF_SLUG"
        assert k8s.service_account_overwrite == "custom-sa"
        assert k8s.proxy_url == "https://proxy.example.com"

    def test_namespace_with_variables(self):
        """Test namespace with CI/CD variables."""
        k8s = GitLabCIKubernetes(namespace="app-$CI_ENVIRONMENT_SLUG")
        assert k8s.namespace == "app-$CI_ENVIRONMENT_SLUG"


class TestGitLabCIEnvironment:
    """Test GitLabCIEnvironment model."""

    def test_simple_environment_string(self):
        """Test simple environment as string."""
        env = "production"
        # String environments are handled at job level
        assert isinstance(env, str)

    def test_environment_with_name_only(self):
        """Test environment with name only."""
        env = GitLabCIEnvironment(name="staging")
        assert env.name == "staging"
        assert env.url is None
        assert env.action is None

    def test_environment_with_url(self):
        """Test environment with URL."""
        env = GitLabCIEnvironment(name="production", url="https://prod.example.com")
        assert env.name == "production"
        assert env.url == "https://prod.example.com"

    def test_environment_with_dynamic_url(self):
        """Test environment with dynamic URL using variables."""
        env = GitLabCIEnvironment(name="review/$CI_COMMIT_REF_SLUG", url="https://$CI_COMMIT_REF_SLUG.example.com")
        assert env.name == "review/$CI_COMMIT_REF_SLUG"
        assert env.url == "https://$CI_COMMIT_REF_SLUG.example.com"

    def test_environment_actions(self):
        """Test environment action types."""
        actions = ["start", "prepare", "stop", "verify", "access"]

        for action in actions:
            env = GitLabCIEnvironment(name="production", action=action)
            assert env.action == action

    def test_environment_on_stop(self):
        """Test environment on_stop configuration."""
        env = GitLabCIEnvironment(name="review/$CI_COMMIT_REF_SLUG", on_stop="stop_review")
        assert env.on_stop == "stop_review"

    def test_environment_auto_stop_in(self):
        """Test environment auto_stop_in configuration."""
        auto_stop_values = [
            "1 hour",
            "2 hours",
            "1 day",
            "1 week",
            "1 month",
            "30 minutes",
        ]

        for value in auto_stop_values:
            env = GitLabCIEnvironment(name="review/$CI_COMMIT_REF_SLUG", auto_stop_in=value)
            assert env.auto_stop_in == value

    def test_environment_kubernetes(self):
        """Test environment with Kubernetes configuration."""
        env = GitLabCIEnvironment(name="production", kubernetes={"namespace": "prod"})

        assert isinstance(env.kubernetes, GitLabCIKubernetes)
        assert env.kubernetes.namespace == "prod"

    def test_environment_deployment_tier(self):
        """Test environment deployment tier."""
        tiers = ["production", "staging", "testing", "development", "other"]

        for tier in tiers:
            env = GitLabCIEnvironment(name="env-name", deployment_tier=tier)
            assert env.deployment_tier == tier

    def test_complex_environment(self):
        """Test complex environment configuration."""
        env = GitLabCIEnvironment(
            name="review/$CI_COMMIT_REF_SLUG",
            url="https://$CI_COMMIT_REF_SLUG.review.example.com",
            action="start",
            on_stop="stop_review_app",
            auto_stop_in="2 weeks",
            kubernetes={"namespace": "review-$CI_COMMIT_REF_SLUG", "service_account_overwrite": "review-sa"},
            deployment_tier="development",
        )

        dumped = env.model_dump()
        assert dumped["name"] == "review/$CI_COMMIT_REF_SLUG"
        assert dumped["url"] == "https://$CI_COMMIT_REF_SLUG.review.example.com"
        assert dumped["action"] == "start"
        assert dumped["on_stop"] == "stop_review_app"
        assert dumped["auto_stop_in"] == "2 weeks"
        assert "kubernetes" in dumped
        assert dumped["kubernetes"]["namespace"] == "review-$CI_COMMIT_REF_SLUG"
        assert dumped["deployment_tier"] == "development"

    def test_stop_environment(self):
        """Test stop environment configuration."""
        env = GitLabCIEnvironment(name="review/$CI_COMMIT_REF_SLUG", action="stop")
        assert env.action == "stop"

    def test_from_dict(self):
        """Test creating environment from dictionary."""
        env_dict = {"name": "production", "url": "https://prod.example.com", "kubernetes": {"namespace": "production"}}

        env = GitLabCIEnvironment(**env_dict)
        assert env.name == "production"
        assert env.url == "https://prod.example.com"
        assert env.kubernetes.namespace == "production"

    def test_extra_fields(self):
        """Test that extra fields are preserved."""
        env = GitLabCIEnvironment(name="production", custom_field="custom_value", future_option=True)

        assert env.name == "production"
        assert env.custom_field == "custom_value"
        assert env.future_option is True

    def test_model_dump_excludes_none(self):
        """Test that None values are excluded from dump."""
        env = GitLabCIEnvironment(name="staging")

        dumped = env.model_dump()
        assert "name" in dumped
        assert "url" not in dumped
        assert "action" not in dumped
        assert "on_stop" not in dumped

    def test_environment_with_rules(self):
        """Test environment that might be used with rules."""
        # Environment itself doesn't have rules, but can be conditional
        env = GitLabCIEnvironment(name="production", url="https://prod.example.com")

        # Rules would be applied at job level
        assert env.name == "production"
        assert env.url == "https://prod.example.com"
