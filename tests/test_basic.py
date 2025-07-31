"""Basic tests for pydantic-gitlab."""

import yaml

from pydantic_gitlab import GitLabCI, WhenType


def test_simple_gitlab_ci():
    """Test parsing a simple GitLab CI configuration."""
    yaml_content = """
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  VERSION: "1.0.0"

build-job:
  stage: build
  script:
    - echo "Building application..."
    - make build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

test-job:
  stage: test
  script:
    - echo "Running tests..."
    - make test
  dependencies:
    - build-job
  coverage: '/Code coverage: \\d+\\.\\d+%/'

deploy-job:
  stage: deploy
  script:
    - echo "Deploying to production..."
    - make deploy
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - main
"""

    # Parse YAML
    data = yaml.safe_load(yaml_content)

    # Create GitLabCI object
    ci = GitLabCI(**data)

    # Check stages
    assert ci.stages == ["build", "test", "deploy"]

    # Check variables
    assert ci.variables is not None
    assert ci.variables.get("DOCKER_DRIVER") == "overlay2"
    assert ci.variables.get("VERSION") == "1.0.0"

    # Check jobs
    assert len(ci.jobs) == 3

    # Check build job
    build_job = ci.get_job("build-job")
    assert build_job is not None
    assert build_job.stage == "build"
    assert build_job.script == ['echo "Building application..."', "make build"]
    assert build_job.artifacts is not None
    assert build_job.artifacts.paths == ["dist/"]
    assert build_job.artifacts.expire_in == "1 week"

    # Check test job
    test_job = ci.get_job("test-job")
    assert test_job is not None
    assert test_job.stage == "test"
    assert test_job.dependencies == ["build-job"]
    assert test_job.coverage == "/Code coverage: \\d+\\.\\d+%/"

    # Check deploy job
    deploy_job = ci.get_job("deploy-job")
    assert deploy_job is not None
    assert deploy_job.stage == "deploy"
    assert deploy_job.when == WhenType.MANUAL
    assert deploy_job.environment is not None
    assert deploy_job.environment.name == "production"
    assert deploy_job.environment.url == "https://example.com"


def test_job_with_rules():
    """Test job with rules configuration."""
    yaml_content = """
test-job:
  script:
    - pytest
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - "**/*.py"
      when: always
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: always
    - when: never
"""

    data = yaml.safe_load(yaml_content)
    ci = GitLabCI(**data)

    job = ci.get_job("test-job")
    assert job is not None
    assert len(job.rules) == 3

    # First rule
    assert job.rules[0].if_ == '$CI_PIPELINE_SOURCE == "merge_request_event"'
    assert job.rules[0].changes == ["**/*.py"]
    assert job.rules[0].when == WhenType.ALWAYS

    # Second rule
    assert job.rules[1].if_ == "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"
    assert job.rules[1].when == WhenType.ALWAYS

    # Third rule
    assert job.rules[2].when == WhenType.NEVER


def test_workflow_configuration():
    """Test workflow configuration."""
    yaml_content = """
workflow:
  name: 'Pipeline for $CI_COMMIT_BRANCH'
  rules:
    - if: $CI_COMMIT_TITLE =~ /-draft$/
      when: never
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

build:
  script: echo "Building..."
"""

    data = yaml.safe_load(yaml_content)
    ci = GitLabCI(**data)

    assert ci.workflow is not None
    assert ci.workflow.name == "Pipeline for $CI_COMMIT_BRANCH"
    assert len(ci.workflow.rules) == 3

    # Check workflow rules
    assert ci.workflow.rules[0].if_ == "$CI_COMMIT_TITLE =~ /-draft$/"
    assert ci.workflow.rules[0].when == "never"

    assert ci.workflow.rules[1].if_ == '$CI_PIPELINE_SOURCE == "merge_request_event"'
    assert ci.workflow.rules[2].if_ == "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"


def test_parallel_matrix():
    """Test parallel matrix configuration."""
    yaml_content = """
test:
  script: npm test
  parallel:
    matrix:
      - NODE_VERSION: ["14", "16", "18"]
        OS: ["ubuntu", "macos"]
"""

    data = yaml.safe_load(yaml_content)
    ci = GitLabCI(**data)

    job = ci.get_job("test")
    assert job is not None
    assert job.parallel is not None
    assert hasattr(job.parallel, "matrix")
    assert len(job.parallel.matrix) == 1
    assert job.parallel.matrix[0]["NODE_VERSION"] == ["14", "16", "18"]
    assert job.parallel.matrix[0]["OS"] == ["ubuntu", "macos"]


def test_include_configuration():
    """Test include configuration."""
    yaml_content = """
include:
  - local: '/templates/.gitlab-ci-template.yml'
  - project: 'my-group/my-project'
    file: '/templates/.builds.yml'
    ref: main
  - remote: 'https://gitlab.com/example-project/-/raw/main/.gitlab-ci.yml'
  - template: Auto-DevOps.gitlab-ci.yml

build:
  script: make build
"""

    data = yaml.safe_load(yaml_content)
    ci = GitLabCI(**data)

    assert ci.include is not None
    assert isinstance(ci.include, list)
    assert len(ci.include) == 4

    # Check local include
    assert ci.include[0].local == "/templates/.gitlab-ci-template.yml"

    # Check project include
    assert ci.include[1].project == "my-group/my-project"
    assert ci.include[1].file == "/templates/.builds.yml"
    assert ci.include[1].ref == "main"

    # Check remote include
    assert ci.include[2].remote == "https://gitlab.com/example-project/-/raw/main/.gitlab-ci.yml"

    # Check template include
    assert ci.include[3].template == "Auto-DevOps.gitlab-ci.yml"


def test_default_configuration():
    """Test default configuration."""
    yaml_content = """
default:
  image: ruby:3.0
  before_script:
    - bundle install
  retry: 2
  artifacts:
    expire_in: 1 day

test1:
  script: bundle exec rspec

test2:
  image: ruby:2.7
  script: bundle exec rspec
  retry: 1
"""

    data = yaml.safe_load(yaml_content)
    ci = GitLabCI(**data)

    assert ci.default is not None
    assert ci.default.image == "ruby:3.0"
    assert ci.default.before_script == ["bundle install"]
    assert ci.default.retry == 2
    assert ci.default.artifacts is not None
    assert ci.default.artifacts.expire_in == "1 day"
