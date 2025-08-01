"""Example of parsing GitLab CI YAML file with pydantic-gitlab."""

import yaml

from pydantic_gitlab import GitLabCI, safe_load_gitlab_yaml


def print_job_info(job_name, job):
    """Print information about a job."""
    print(f"  - {job_name}")
    print(f"    Stage: {job.stage or 'test'}")
    if job.script:
        print(f"    Script: {job.script[0]}{'...' if len(job.script) > 1 else ''}")
    if job.when:
        print(f"    When: {job.when.value}")
    if job.environment:
        print(f"    Environment: {job.environment.name}")
    if job.parallel:
        print(f"    Parallel: {job.parallel}")
    if job.needs:
        needs_str = ", ".join(n if isinstance(n, str) else n.job for n in job.needs)
        print(f"    Needs: {needs_str}")
    print()


def main():
    """Parse and validate a GitLab CI configuration."""
    # Example GitLab CI YAML content
    gitlab_ci_yaml = """
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_IMAGE: python:3.11
  CACHE_DIR: .cache

default:
  image: $DOCKER_IMAGE
  cache:
    key: "$CI_COMMIT_REF_SLUG"
    paths:
      - $CACHE_DIR/pip
  before_script:
    - python --version
    - pip install --cache-dir=$CACHE_DIR/pip -r requirements.txt

workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        DEPLOY_ENV: production
    - if: $CI_MERGE_REQUEST_ID
      variables:
        DEPLOY_ENV: review

build:
  stage: build
  script:
    - echo "Building application..."
    - python setup.py build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

test:unit:
  stage: test
  script:
    - pytest tests/unit
  coverage: '/TOTAL.*\\s+(\\d+%)/'
  parallel: 3

test:integration:
  stage: test
  script:
    - pytest tests/integration
  services:
    - name: postgres:15
      alias: db
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
  needs:
    - build

deploy:staging:
  stage: deploy
  script:
    - echo "Deploying to staging..."
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
      when: always
    - when: manual
  needs:
    - job: test:unit
      artifacts: false
    - test:integration

deploy:production:
  stage: deploy
  script:
    - echo "Deploying to production..."
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - main
  needs:
    - test:unit
    - test:integration

pages:
  stage: deploy
  script:
    - mkdocs build --site-dir public
  artifacts:
    paths:
      - public
  only:
    - main
"""

    # Parse YAML with GitLab CI specific tags support
    data = safe_load_gitlab_yaml(gitlab_ci_yaml)

    # Create and validate GitLabCI structure
    try:
        ci_config = GitLabCI(**data)
        print("✅ GitLab CI configuration is valid!")
        print()

        # Display parsed information
        print("📋 Stages:")
        for stage in ci_config.stages or []:
            print(f"  - {stage}")
        print()

        print("🔧 Global Variables:")
        if ci_config.variables:
            for name, value in ci_config.variables.variables.items():
                print(f"  {name}: {value}")
        print()

        print("👷 Jobs:")
        for job_name, job in ci_config.jobs.items():
            print_job_info(job_name, job)

        # Validate job dependencies
        errors = ci_config.validate_job_dependencies()
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ All job dependencies are valid!")

        # Example: Serialize back to YAML
        print("\n📄 Serialized back to YAML:")
        print("-" * 50)
        # Note: This is a simplified serialization
        # For production use, you might want to implement custom YAML serialization
        output_data = ci_config.model_dump(exclude_none=True, by_alias=True)
        print(yaml.dump(output_data, default_flow_style=False, sort_keys=False))

    except Exception as e:
        print(f"❌ Error parsing GitLab CI configuration: {e}")
        raise


if __name__ == "__main__":
    main()
