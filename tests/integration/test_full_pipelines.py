"""Integration tests for complete GitLab CI pipeline configurations."""

import yaml

from pydantic_gitlab import GitLabCI


class TestRealWorldPipelines:
    """Test real-world pipeline configurations."""

    def test_simple_nodejs_pipeline(self):
        """Test simple Node.js application pipeline."""
        config = """
stages:
  - build
  - test
  - deploy

variables:
  NODE_VERSION: "16"

cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - node_modules/

build:
  stage: build
  image: node:$NODE_VERSION
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 day

test:
  stage: test
  image: node:$NODE_VERSION
  script:
    - npm ci
    - npm test
  coverage: '/Coverage: (\\d+\\.\\d+)%/'

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploying to production"
  environment:
    name: production
    url: https://example.com
  only:
    - main
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        assert len(ci.stages) == 3
        assert ci.variables["NODE_VERSION"] == "16"
        assert len(ci.jobs) == 3
        assert ci.jobs["build"].stage == "build"
        assert ci.jobs["test"].coverage == r"/Coverage: (\d+\.\d+)%/"
        assert ci.jobs["deploy"].environment.name == "production"

    def test_python_microservice_pipeline(self):
        """Test Python microservice pipeline with Docker."""
        config = """
variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG

stages:
  - test
  - build
  - deploy

default:
  tags:
    - docker

# Hidden job templates
.python_test:
  image: python:3.9
  before_script:
    - pip install poetry
    - poetry install
  cache:
    key:
      files:
        - poetry.lock
    paths:
      - .venv/

lint:
  extends: .python_test
  stage: test
  script:
    - poetry run flake8
    - poetry run mypy src/
    - poetry run black --check .

test:
  extends: .python_test
  stage: test
  services:
    - name: postgres:13
      alias: db
      variables:
        POSTGRES_DB: test_db
        POSTGRES_USER: test_user
        POSTGRES_PASSWORD: test_pass
  variables:
    DATABASE_URL: postgresql://test_user:test_pass@db/test_db
  script:
    - poetry run pytest --cov=src --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  coverage: '/TOTAL.+?(\\d+\\%)/'

build:
  stage: build
  image: docker:20.10
  services:
    - docker:20.10-dind
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_MERGE_REQUEST_ID

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/app app=$IMAGE_TAG
  environment:
    name: production
    url: https://api.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        # Check global configuration
        assert ci.variables["DOCKER_DRIVER"] == "overlay2"
        assert ci.default.tags == ["docker"]

        # Check hidden job template
        assert ".python_test" in ci.references

        # Check extended jobs
        assert ci.jobs["lint"].extends == [".python_test"]
        assert ci.jobs["test"].extends == [".python_test"]

        # Check services
        test_job = ci.jobs["test"]
        assert len(test_job.services) == 1
        assert test_job.services[0].name == "postgres:13"
        assert test_job.services[0].alias == "db"

        # Check rules
        assert len(ci.jobs["deploy"].rules) == 1
        assert ci.jobs["deploy"].rules[0].when == "manual"

    def test_monorepo_pipeline(self):
        """Test monorepo pipeline with multiple services."""
        config = """
workflow:
  rules:
    - if: $CI_MERGE_REQUEST_ID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

stages:
  - build
  - test
  - deploy

# Frontend jobs
frontend:build:
  stage: build
  image: node:16
  script:
    - cd frontend
    - npm ci
    - npm run build
  artifacts:
    paths:
      - frontend/dist/
  rules:
    - changes:
        - frontend/**/*
        - package.json

frontend:test:
  stage: test
  image: node:16
  needs: ["frontend:build"]
  script:
    - cd frontend
    - npm ci
    - npm test
  rules:
    - changes:
        - frontend/**/*

# Backend jobs
backend:build:
  stage: build
  image: golang:1.19
  script:
    - cd backend
    - go mod download
    - go build -o app ./cmd/server
  artifacts:
    paths:
      - backend/app
  rules:
    - changes:
        - backend/**/*
        - go.mod

backend:test:
  stage: test
  image: golang:1.19
  needs: ["backend:build"]
  services:
    - redis:6-alpine
  script:
    - cd backend
    - go test -v ./...
  rules:
    - changes:
        - backend/**/*

# Deployment
deploy:all:
  stage: deploy
  image: alpine:latest
  needs:
    - job: frontend:build
      optional: true
    - job: backend:build
      optional: true
  script:
    - echo "Deploying services..."
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        # Check workflow
        assert len(ci.workflow.rules) == 2

        # Check change-based rules
        frontend_build = ci.jobs["frontend:build"]
        assert len(frontend_build.rules) == 1
        # Changes can be a list directly or a GitLabCIRulesChanges object
        changes = frontend_build.rules[0].changes
        if hasattr(changes, "changes"):
            assert changes.changes == ["frontend/**/*", "package.json"]
        else:
            assert changes == ["frontend/**/*", "package.json"]

        # Check needs with optional
        deploy_job = ci.jobs["deploy:all"]
        assert len(deploy_job.needs) == 2
        assert deploy_job.needs[0].job == "frontend:build"
        assert deploy_job.needs[0].optional is True

    def test_security_scanning_pipeline(self):
        """Test pipeline with security scanning."""
        config = r"""
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml

stages:
  - build
  - test
  - security
  - deploy

variables:
  SECURE_ANALYZERS_PREFIX: "$CI_TEMPLATE_REGISTRY_HOST/security-products"
  SAST_EXCLUDED_PATHS: "vendor/, tests/"

build:
  stage: build
  image: maven:3.8-openjdk-11
  script:
    - mvn clean package
  artifacts:
    paths:
      - target/*.jar
    reports:
      junit: target/surefire-reports/TEST-*.xml

dependency_scanning:
  stage: security
  variables:
    DS_JAVA_VERSION: 11

secret_detection:
  stage: security
  rules:
    - if: $CI_COMMIT_BRANCH
      exists:
        - "**/*"

sast:
  stage: security
  variables:
    SAST_JAVA_VERSION: 11

deploy:
  stage: deploy
  image: amazon/aws-cli:latest
  script:
    - aws s3 cp target/*.jar s3://my-bucket/
  environment:
    name: production
  dependencies:
    - build
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        # Check includes
        assert len(ci.include) == 3

        # Check security job variables
        assert ci.variables["SAST_EXCLUDED_PATHS"] == "vendor/, tests/"

        # Check artifact reports
        build_job = ci.jobs["build"]
        assert build_job.artifacts.reports.junit == ["target/surefire-reports/TEST-*.xml"]

        # Check tag-based deployment
        deploy_job = ci.jobs["deploy"]
        assert deploy_job.rules[0].if_ == r"$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/"

    def test_multi_environment_pipeline(self):
        """Test pipeline with multiple environments."""
        config = """
stages:
  - build
  - deploy

build:
  stage: build
  script:
    - docker build -t myapp:$CI_COMMIT_SHORT_SHA .
  artifacts:
    paths:
      - VERSION

.deploy_template:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploying to $CI_ENVIRONMENT_NAME"
    - ./deploy.sh

deploy:dev:
  extends: .deploy_template
  environment:
    name: development
    url: https://dev.example.com
    on_stop: stop:dev
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy:staging:
  extends: .deploy_template
  environment:
    name: staging
    url: https://staging.example.com
    on_stop: stop:staging
    auto_stop_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:prod:
  extends: .deploy_template
  environment:
    name: production
    url: https://example.com
    kubernetes:
      namespace: production
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
  allow_failure: false

stop:dev:
  extends: .deploy_template
  environment:
    name: development
    action: stop
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
      when: manual

stop:staging:
  extends: .deploy_template
  environment:
    name: staging
    action: stop
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        # Check template
        assert ".deploy_template" in ci.references

        # Check environment configurations
        dev_env = ci.jobs["deploy:dev"].environment
        assert dev_env.name == "development"
        assert dev_env.on_stop == "stop:dev"

        staging_env = ci.jobs["deploy:staging"].environment
        assert staging_env.auto_stop_in == "1 week"

        prod_env = ci.jobs["deploy:prod"].environment
        assert prod_env.kubernetes.namespace == "production"

        # Check stop jobs
        stop_dev = ci.jobs["stop:dev"]
        assert stop_dev.environment.action == "stop"
        assert stop_dev.when == "manual"

    def test_parallel_testing_pipeline(self):
        """Test pipeline with parallel testing."""
        config = """
stages:
  - build
  - test
  - report

build:
  stage: build
  script:
    - make build
  artifacts:
    paths:
      - build/

test:unit:
  stage: test
  needs: ["build"]
  parallel: 5
  script:
    - make test-unit TEST_SUITE=$CI_NODE_INDEX/$CI_NODE_TOTAL

test:integration:
  stage: test
  needs: ["build"]
  parallel:
    matrix:
      - DATABASE: ["mysql", "postgres"]
        VERSION: ["12", "13", "14"]
  services:
    - name: $DATABASE:$VERSION
      alias: db
  script:
    - make test-integration DB=$DATABASE DB_VERSION=$VERSION

test:browser:
  stage: test
  needs: ["build"]
  parallel:
    matrix:
      - BROWSER: ["chrome", "firefox", "safari"]
        OS: ["windows", "macos", "linux"]
  tags:
    - $OS
  script:
    - make test-e2e BROWSER=$BROWSER

report:coverage:
  stage: report
  needs:
    - test:unit
    - test:integration
  script:
    - make coverage-report
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  coverage: '/TOTAL.*?(\\d+%)/'
"""
        yaml_data = yaml.safe_load(config)
        ci = GitLabCI(**yaml_data)

        # Check simple parallel
        assert ci.jobs["test:unit"].parallel == 5

        # Check matrix parallel
        integration_parallel = ci.jobs["test:integration"].parallel
        assert len(integration_parallel.matrix) == 1
        assert integration_parallel.matrix[0]["DATABASE"] == ["mysql", "postgres"]
        assert integration_parallel.matrix[0]["VERSION"] == ["12", "13", "14"]

        # Check browser matrix
        browser_parallel = ci.jobs["test:browser"].parallel
        assert browser_parallel.matrix[0]["BROWSER"] == ["chrome", "firefox", "safari"]
        assert browser_parallel.matrix[0]["OS"] == ["windows", "macos", "linux"]

        # Check coverage aggregation
        report_job = ci.jobs["report:coverage"]
        assert len(report_job.needs) == 2
        assert report_job.coverage == r"/TOTAL.*?(\d+%)/"
