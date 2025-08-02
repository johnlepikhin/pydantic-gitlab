"""Test GitLabReference support."""

from pydantic_gitlab import GitLabCI, safe_dump_gitlab_yaml, safe_load_gitlab_yaml


def test_gitlab_reference_in_scripts():
    """Test GitLabReference in script, before_script, after_script."""
    yaml_content = """
.common:
  script:
    - echo "Common script"
  before_script:
    - echo "Common before"
  after_script:
    - echo "Common after"

test-job:
  script:
    - !reference [.common, script]
    - echo "Additional command"
  before_script:
    - !reference [.common, before_script]
  after_script:
    - !reference [.common, after_script]
"""
    # Parse without resolving
    data = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Should parse successfully
    gitlab_ci = GitLabCI(**data)

    # Check that references are preserved
    job = gitlab_ci.jobs["test-job"]
    assert len(job.script) == 2
    assert str(job.script[0]).startswith("GitLabReference")
    assert job.script[1] == 'echo "Additional command"'

    # Check serialization
    yaml_output = safe_dump_gitlab_yaml(data)
    assert "!reference" in yaml_output


def test_gitlab_reference_in_variables():
    """Test GitLabReference in variables."""
    yaml_content = """
.vars:
  variables:
    DATABASE_URL: "postgres://localhost/test"
    API_KEY: "secret"

test-job:
  variables:
    !reference [.vars, variables]
  script:
    - echo "Test"

deploy-job:
  variables:
    DB_URL: !reference [.vars, variables, DATABASE_URL]
    API_KEY: !reference [.vars, variables, API_KEY]
    CUSTOM_VAR: "custom"
  script:
    - echo "Deploy"
"""
    # Parse without resolving
    data = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Should parse successfully
    gitlab_ci = GitLabCI(**data)

    # Check whole variables reference
    test_job = gitlab_ci.jobs["test-job"]
    assert str(test_job.variables).startswith("GitLabReference")

    # Check individual variable references
    deploy_job = gitlab_ci.jobs["deploy-job"]
    # When dict contains GitLabReference, it's preserved as dict in our validator
    assert deploy_job.variables is not None
    # The variables should contain GitLabReference objects
    vars_dict = deploy_job.variables.variables if hasattr(deploy_job.variables, "variables") else deploy_job.variables
    assert "CUSTOM_VAR" in vars_dict


def test_gitlab_reference_in_rules():
    """Test GitLabReference in rules."""
    yaml_content = """
.standard-rules:
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: always
    - if: '$CI_MERGE_REQUEST_ID'

test-job:
  rules:
    - !reference [.standard-rules, rules]
  script:
    - echo "Test"

deploy-job:
  rules:
    - !reference [.standard-rules, rules]
    - if: '$CI_COMMIT_TAG'
      when: manual
  script:
    - echo "Deploy"
"""
    # Parse without resolving
    data = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Should parse successfully
    gitlab_ci = GitLabCI(**data)

    # Check rules reference
    test_job = gitlab_ci.jobs["test-job"]
    assert len(test_job.rules) == 1
    assert str(test_job.rules[0]).startswith("GitLabReference")

    # Check mixed rules
    deploy_job = gitlab_ci.jobs["deploy-job"]
    assert len(deploy_job.rules) == 2


def test_gitlab_reference_resolution():
    """Test that references can be resolved."""
    yaml_content = """
.common:
  before_script:
    - echo "Setup"
    - source env.sh

test-job:
  before_script:
    - !reference [.common, before_script]
  script:
    - pytest
"""
    # Parse with resolution (default)
    data = safe_load_gitlab_yaml(yaml_content)

    # Should parse and resolve successfully
    gitlab_ci = GitLabCI(**data)

    # Check that reference was resolved
    job = gitlab_ci.jobs["test-job"]
    assert job.before_script == ['echo "Setup"', "source env.sh"]


def test_gitlab_reference_roundtrip():
    """Test full roundtrip with references."""
    yaml_content = """
.template:
  script:
    - build.sh
  variables:
    ENV: "prod"

job:
  extends: .template
  script:
    - !reference [.template, script]
    - deploy.sh
  variables:
    !reference [.template, variables]
"""
    # Parse without resolving
    data1 = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Dump back to YAML
    yaml_output = safe_dump_gitlab_yaml(data1)

    # Parse again
    data2 = safe_load_gitlab_yaml(yaml_output, resolve_refs=False)

    # Should be equal
    assert data1 == data2

    # Should preserve !reference tags
    assert "!reference" in yaml_output


def test_gitlab_reference_in_artifacts():
    """Test GitLabReference in artifacts field."""
    # Use raw string to avoid escaping issues
    yaml_content = r""".store_job_artifacts:
  artifacts:
    paths:
      - build/
    expire_in: 1 week

generate-build-id:
  stage: Common prepare
  before_script: ./scripts/runner-provisioner.sh
  script: ./scripts/generate-build-id
  artifacts: !reference [.store_job_artifacts, artifacts]
"""
    # Parse without resolving
    data = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Should parse successfully
    gitlab_ci = GitLabCI(**data)

    # Check that reference is preserved
    job = gitlab_ci.jobs["generate-build-id"]
    assert str(job.artifacts).startswith("GitLabReference")

    # Check serialization
    yaml_output = safe_dump_gitlab_yaml(data)
    assert "!reference" in yaml_output


def test_gitlab_reference_in_needs():
    """Test GitLabReference in needs field."""
    yaml_content = r""".needs_upstream_artifacts:
  needs:
    - build-upstream
    - test-upstream

generate-build-id:
  extends: .common_job_template
  stage: Common prepare
  script:
    - !reference [.python_path_setup]
    - ./scripts/generate-build-id
  needs:
    - !reference [.needs_upstream_artifacts, needs]
"""
    # Parse without resolving
    data = safe_load_gitlab_yaml(yaml_content, resolve_refs=False)

    # Should parse successfully
    gitlab_ci = GitLabCI(**data)

    # Check that reference is preserved
    job = gitlab_ci.jobs["generate-build-id"]
    # needs is a list containing a GitLabReference
    assert len(job.needs) == 1
    assert str(job.needs[0]).startswith("GitLabReference")

    # Check serialization
    yaml_output = safe_dump_gitlab_yaml(data)
    assert "!reference" in yaml_output
