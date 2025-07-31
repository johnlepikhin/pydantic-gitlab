"""Test YAML serialization and deserialization roundtrip."""

from typing import Any

import yaml

from pydantic_gitlab import (
    GitLabCI,
    GitLabCIIncludeComponent,
    GitLabCIIncludeLocal,
    GitLabCIIncludeProject,
    GitLabCIIncludeRemote,
    GitLabCIIncludeTemplate,
)


class TestYAMLRoundtrip:
    """Test YAML serialization roundtrip."""

    def normalize_yaml_data(self, data: Any) -> Any:
        """Normalize YAML data for comparison."""
        if isinstance(data, dict):
            # Remove None values and normalize nested structures
            return {k: self.normalize_yaml_data(v) for k, v in data.items() if v is not None}
        if isinstance(data, list):
            return [self.normalize_yaml_data(item) for item in data]
        return data

    def test_simple_pipeline_roundtrip(self):
        """Test simple pipeline YAML roundtrip."""
        original_yaml = """
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - echo "Building..."
    - make build

test:
  stage: test
  script:
    - echo "Testing..."
    - make test
  needs: ["build"]

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  when: manual
"""
        # Parse YAML
        original_data = yaml.safe_load(original_yaml)

        # Create GitLabCI object
        ci = GitLabCI(**original_data)

        # Serialize back to dict
        serialized_data = ci.model_dump()

        # Normalize both for comparison
        normalized_original = self.normalize_yaml_data(original_data)
        normalized_serialized = self.normalize_yaml_data(serialized_data)

        # Check that key elements are preserved
        assert normalized_serialized["stages"] == normalized_original["stages"]
        assert "build" in normalized_serialized
        assert "test" in normalized_serialized
        assert "deploy" in normalized_serialized

        # Check job details
        assert normalized_serialized["build"]["script"] == normalized_original["build"]["script"]
        assert normalized_serialized["test"]["needs"] == normalized_original["test"]["needs"]
        assert normalized_serialized["deploy"]["when"] == normalized_original["deploy"]["when"]

    def test_complex_job_roundtrip(self):
        """Test complex job configuration roundtrip."""
        job_yaml = """
test_job:
  stage: test
  image:
    name: python:3.9
    entrypoint: [""]
  services:
    - name: postgres:13
      alias: db
      variables:
        POSTGRES_DB: test
  variables:
    TEST_VAR: "value"
    NUMBER_VAR: 42
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest
  after_script:
    - echo "Done"
  artifacts:
    paths:
      - reports/
    reports:
      junit: report.xml
    expire_in: 1 week
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - .cache/
  rules:
    - if: $CI_MERGE_REQUEST_ID
      changes:
        - "**/*.py"
  retry:
    max: 2
    when:
      - runner_system_failure
  timeout: 30 minutes
  parallel: 3
  allow_failure: true
"""
        data = yaml.safe_load(job_yaml)
        ci = GitLabCI(**data)

        job = ci.jobs["test_job"]

        # Check all fields are preserved
        assert job.stage == "test"
        assert job.image.name == "python:3.9"
        assert job.image.entrypoint == [""]
        assert len(job.services) == 1
        assert job.services[0].alias == "db"
        assert job.variables["TEST_VAR"] == "value"
        assert job.variables["NUMBER_VAR"] == 42
        assert job.before_script == ["pip install -r requirements.txt"]
        assert job.script == ["pytest"]
        assert job.artifacts.paths == ["reports/"]
        assert job.cache.key == "$CI_COMMIT_REF_SLUG"
        assert len(job.rules) == 1
        assert job.retry.max == 2
        assert job.timeout == "30 minutes"
        assert job.parallel == 3
        assert job.allow_failure is True

    def test_workflow_roundtrip(self):
        """Test workflow configuration roundtrip."""
        workflow_yaml = """
workflow:
  name: "Pipeline for $CI_COMMIT_REF_NAME"
  rules:
    - if: $CI_MERGE_REQUEST_ID
      variables:
        PIPELINE_TYPE: merge_request
    - if: $CI_COMMIT_TAG
      variables:
        PIPELINE_TYPE: tag
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      variables:
        PIPELINE_TYPE: main
    - when: never
  auto_cancel:
    on_new_commit: conservative
    on_job_failure: all
"""
        data = yaml.safe_load(workflow_yaml)
        ci = GitLabCI(**data)

        workflow = ci.workflow
        assert workflow.name == "Pipeline for $CI_COMMIT_REF_NAME"
        assert len(workflow.rules) == 4
        assert workflow.rules[0].variables["PIPELINE_TYPE"] == "merge_request"
        assert workflow.rules[3].when == "never"
        assert workflow.auto_cancel.on_new_commit == "conservative"
        assert workflow.auto_cancel.on_job_failure == "all"

    def test_include_roundtrip(self):
        """Test include configuration roundtrip."""
        include_yaml = """
include:
  - local: /templates/common.yml
  - project: my-group/my-project
    file: /templates/jobs.yml
    ref: v1.0.0
  - remote: https://example.com/template.yml
  - template: Auto-DevOps.gitlab-ci.yml
  - component: gitlab.com/components/test@1.0
    inputs:
      stage: test
"""
        data = yaml.safe_load(include_yaml)
        ci = GitLabCI(**data)

        includes = ci.include
        assert len(includes) == 5

        # Check each include type
        # Local include is converted to GitLabCIIncludeLocal object
        assert isinstance(includes[0], GitLabCIIncludeLocal)
        assert includes[0].local == "/templates/common.yml"

        assert isinstance(includes[1], GitLabCIIncludeProject)
        assert includes[1].project == "my-group/my-project"
        assert includes[1].file == "/templates/jobs.yml"
        assert includes[1].ref == "v1.0.0"

        assert isinstance(includes[2], GitLabCIIncludeRemote)
        assert includes[2].remote == "https://example.com/template.yml"

        assert isinstance(includes[3], GitLabCIIncludeTemplate)
        assert includes[3].template == "Auto-DevOps.gitlab-ci.yml"

        assert isinstance(includes[4], GitLabCIIncludeComponent)
        assert includes[4].component == "gitlab.com/components/test@1.0"
        assert includes[4].inputs.inputs["stage"] == "test"

    def test_special_job_types_roundtrip(self):
        """Test special job types roundtrip."""
        special_yaml = """
pages:
  stage: deploy
  script:
    - mkdir public
    - cp -r dist/* public/
  artifacts:
    paths:
      - public
  only:
    - main

release_job:
  stage: release
  image: registry.gitlab.com/gitlab-org/release-cli:latest
  script:
    - echo "Creating release"
  release:
    tag_name: v$CI_COMMIT_TAG
    name: "Release $CI_COMMIT_TAG"
    description: "Release notes for $CI_COMMIT_TAG"
    milestones:
      - m1
      - m2
    assets:
      links:
        - name: "Binary"
          url: "https://example.com/bin.zip"
  only:
    - tags

trigger_job:
  stage: deploy
  trigger:
    project: my-group/my-deployment
    branch: main
    strategy: depend
"""
        data = yaml.safe_load(special_yaml)
        ci = GitLabCI(**data)

        # Check pages job
        pages = ci.jobs["pages"]
        assert pages.script == ["mkdir public", "cp -r dist/* public/"]
        assert pages.artifacts.paths == ["public"]

        # Check release job
        release_job = ci.jobs["release_job"]
        assert release_job.release.tag_name == "v$CI_COMMIT_TAG"
        assert release_job.release.milestones == ["m1", "m2"]
        assert release_job.release.assets["links"][0]["name"] == "Binary"

        # Check trigger job
        trigger_job = ci.jobs["trigger_job"]
        assert trigger_job.trigger.project == "my-group/my-deployment"
        assert trigger_job.trigger.branch == "main"
        assert trigger_job.trigger.strategy == "depend"

    def test_yaml_to_string_roundtrip(self):
        """Test converting to YAML string and back."""
        config = {
            "stages": ["build", "test"],
            "variables": {"KEY": "value"},
            "build": {"stage": "build", "script": ["echo 'Building'"]},
            "test": {"stage": "test", "script": ["echo 'Testing'"], "needs": ["build"]},
        }

        # Create CI object
        ci = GitLabCI(**config)

        # Convert to YAML string
        yaml_str = ci.model_dump_yaml()

        # Parse back
        parsed_data = yaml.safe_load(yaml_str)
        ci2 = GitLabCI(**parsed_data)

        # Compare
        assert ci.stages == ci2.stages
        assert ci.variables["KEY"] == ci2.variables["KEY"]
        assert ci.jobs["build"].script == ci2.jobs["build"].script
        assert ci.jobs["test"].needs == ci2.jobs["test"].needs

    def test_extra_fields_preserved(self):
        """Test that extra fields are preserved in roundtrip."""
        yaml_with_extras = """
stages:
  - test

unknown_global_field: "preserved"
future_feature:
  option1: value1
  option2: value2

test:
  stage: test
  script: ["echo 'test'"]
  unknown_job_field: "also preserved"
  future_job_feature:
    setting: true
"""
        data = yaml.safe_load(yaml_with_extras)
        ci = GitLabCI(**data)

        # Extra fields should be preserved
        assert ci.extra_fields["unknown_global_field"] == "preserved"
        assert ci.extra_fields["future_feature"]["option1"] == "value1"

        # Job extra fields
        job = ci.jobs["test"]
        assert job.unknown_job_field == "also preserved"
        assert job.future_job_feature["setting"] is True

        # Serialize and check
        serialized = ci.model_dump()
        assert serialized["unknown_global_field"] == "preserved"
        assert serialized["test"]["unknown_job_field"] == "also preserved"
