"""Tests for GitLab CI services and images."""

from pydantic_gitlab.services import (
    GitLabCIDockerConfig,
    GitLabCIImageObject,
    GitLabCIServiceObject,
)


class TestGitLabCIDockerConfig:
    """Test GitLabCIDockerConfig model."""

    def test_minimal_docker_config(self):
        """Test minimal Docker configuration."""
        config = GitLabCIDockerConfig()
        assert config.platform is None
        assert config.user is None

    def test_docker_config_with_platform(self):
        """Test Docker config with platform."""
        config = GitLabCIDockerConfig(platform="linux/amd64")
        assert config.platform == "linux/amd64"

    def test_docker_config_with_user(self):
        """Test Docker config with user."""
        config = GitLabCIDockerConfig(user="1000:1000")
        assert config.user == "1000:1000"

    def test_docker_config_complete(self):
        """Test complete Docker configuration."""
        config = GitLabCIDockerConfig(platform="linux/arm64", user="www-data")
        assert config.platform == "linux/arm64"
        assert config.user == "www-data"


class TestGitLabCIPullPolicy:
    """Test GitLabCIPullPolicy model."""

    def test_pull_policy_as_string(self):
        """Test pull policy as string."""
        policies = ["always", "never", "if-not-present"]

        for policy in policies:
            assert isinstance(policy, str)

    def test_pull_policy_as_list(self):
        """Test pull policy as list."""
        policy = ["always", "if-not-present"]
        assert isinstance(policy, list)
        assert len(policy) == 2


class TestGitLabCIImageObject:
    """Test GitLabCIImageObject model."""

    def test_image_object_with_name_only(self):
        """Test image object with name only."""
        image = GitLabCIImageObject(name="python:3.9")
        assert image.name == "python:3.9"
        assert image.entrypoint is None
        assert image.pull_policy is None

    def test_image_object_with_entrypoint(self):
        """Test image object with entrypoint."""
        image = GitLabCIImageObject(name="alpine:latest", entrypoint=["/bin/sh", "-c"])
        assert image.name == "alpine:latest"
        assert image.entrypoint == ["/bin/sh", "-c"]

    def test_image_object_with_pull_policy_string(self):
        """Test image object with pull policy as string."""
        image = GitLabCIImageObject(name="node:16", pull_policy="always")
        assert image.name == "node:16"
        assert image.pull_policy == "always"

    def test_image_object_with_pull_policy_list(self):
        """Test image object with pull policy as list."""
        image = GitLabCIImageObject(name="ruby:3.0", pull_policy=["always", "if-not-present"])
        assert image.name == "ruby:3.0"
        assert image.pull_policy == ["always", "if-not-present"]

    def test_image_object_with_docker_config(self):
        """Test image object with Docker configuration."""
        image = GitLabCIImageObject(name="custom:latest", docker={"platform": "linux/amd64", "user": "node"})
        assert image.name == "custom:latest"
        assert isinstance(image.docker, GitLabCIDockerConfig)
        assert image.docker.platform == "linux/amd64"
        assert image.docker.user == "node"

    def test_image_object_complete(self):
        """Test complete image object."""
        image = GitLabCIImageObject(
            name="registry.example.com/my-app:v1.0",
            entrypoint=["/usr/local/bin/app"],
            pull_policy="always",
            docker={"platform": "linux/arm64", "user": "app-user"},
        )

        dumped = image.model_dump()
        assert dumped["name"] == "registry.example.com/my-app:v1.0"
        assert dumped["entrypoint"] == ["/usr/local/bin/app"]
        assert dumped["pull_policy"] == "always"
        assert dumped["docker"]["platform"] == "linux/arm64"
        assert dumped["docker"]["user"] == "app-user"


class TestGitLabCIImage:
    """Test GitLabCIImage union type."""

    def test_image_as_string(self):
        """Test image as simple string."""
        image = "python:3.9-slim"
        assert isinstance(image, str)

    def test_image_as_object(self):
        """Test image as object."""
        image = GitLabCIImageObject(name="node:16-alpine", entrypoint=["/bin/sh"])
        assert isinstance(image, GitLabCIImageObject)
        assert image.name == "node:16-alpine"


class TestGitLabCIServiceObject:
    """Test GitLabCIServiceObject model."""

    def test_service_object_with_name_only(self):
        """Test service object with name only."""
        service = GitLabCIServiceObject(name="postgres:13")
        assert service.name == "postgres:13"
        assert service.alias is None
        assert service.entrypoint is None
        assert service.command is None
        assert service.variables is None

    def test_service_object_with_alias(self):
        """Test service object with alias."""
        service = GitLabCIServiceObject(name="postgres:13", alias="db")
        assert service.name == "postgres:13"
        assert service.alias == "db"

    def test_service_object_with_entrypoint(self):
        """Test service object with entrypoint."""
        service = GitLabCIServiceObject(name="redis:6", entrypoint=["redis-server"])
        assert service.name == "redis:6"
        assert service.entrypoint == ["redis-server"]

    def test_service_object_with_command(self):
        """Test service object with command."""
        service = GitLabCIServiceObject(
            name="mysql:8", command=["--default-authentication-plugin=mysql_native_password"]
        )
        assert service.name == "mysql:8"
        assert service.command == ["--default-authentication-plugin=mysql_native_password"]

    def test_service_object_with_variables(self):
        """Test service object with variables."""
        service = GitLabCIServiceObject(
            name="postgres:13",
            alias="postgres",
            variables={"POSTGRES_DB": "test_db", "POSTGRES_USER": "test_user", "POSTGRES_PASSWORD": "test_pass"},
        )
        assert service.name == "postgres:13"
        assert service.alias == "postgres"
        assert service.variables["POSTGRES_DB"] == "test_db"
        assert service.variables["POSTGRES_USER"] == "test_user"
        assert service.variables["POSTGRES_PASSWORD"] == "test_pass"

    def test_service_object_with_pull_policy(self):
        """Test service object with pull policy."""
        service = GitLabCIServiceObject(name="elasticsearch:7.10", pull_policy="if-not-present")
        assert service.name == "elasticsearch:7.10"
        assert service.pull_policy == "if-not-present"

    def test_service_object_complete(self):
        """Test complete service object."""
        service = GitLabCIServiceObject(
            name="mysql:8.0",
            alias="mysql",
            entrypoint=["docker-entrypoint.sh"],
            command=["mysqld"],
            variables={"MYSQL_ROOT_PASSWORD": "root", "MYSQL_DATABASE": "test"},
            pull_policy="always",
        )

        dumped = service.model_dump()
        assert dumped["name"] == "mysql:8.0"
        assert dumped["alias"] == "mysql"
        assert dumped["entrypoint"] == ["docker-entrypoint.sh"]
        assert dumped["command"] == ["mysqld"]
        assert dumped["variables"]["MYSQL_ROOT_PASSWORD"] == "root"
        assert dumped["pull_policy"] == "always"


class TestGitLabCIService:
    """Test GitLabCIService union type."""

    def test_service_as_string(self):
        """Test service as simple string."""
        service = "redis:latest"
        assert isinstance(service, str)

    def test_service_as_object(self):
        """Test service as object."""
        service = GitLabCIServiceObject(name="postgres:13", alias="database")
        assert isinstance(service, GitLabCIServiceObject)
        assert service.name == "postgres:13"
        assert service.alias == "database"


class TestIntegration:
    """Test integration scenarios."""

    def test_job_with_image_and_services(self):
        """Test job configuration with image and services."""
        config = {
            "image": {"name": "python:3.9", "entrypoint": [""]},
            "services": ["postgres:13", {"name": "redis:6", "alias": "cache"}],
        }

        # Parse image
        image = GitLabCIImageObject(**config["image"])
        assert image.name == "python:3.9"
        assert image.entrypoint == [""]

        # Parse services
        services = []
        for svc in config["services"]:
            if isinstance(svc, str):
                services.append(svc)
            else:
                services.append(GitLabCIServiceObject(**svc))

        assert len(services) == 2
        assert services[0] == "postgres:13"
        assert isinstance(services[1], GitLabCIServiceObject)
        assert services[1].name == "redis:6"
        assert services[1].alias == "cache"

    def test_private_registry_image(self):
        """Test private registry image configuration."""
        image = GitLabCIImageObject(name="$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG", pull_policy="always")
        assert image.name == "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG"
        assert image.pull_policy == "always"

    def test_service_with_health_check(self):
        """Test service that might need health check configuration."""
        service = GitLabCIServiceObject(
            name="elasticsearch:7.10",
            alias="elasticsearch",
            variables={"discovery.type": "single-node", "ES_JAVA_OPTS": "-Xms512m -Xmx512m"},
        )
        assert service.name == "elasticsearch:7.10"
        assert service.variables["discovery.type"] == "single-node"
