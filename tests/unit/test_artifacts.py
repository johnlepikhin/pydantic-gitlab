"""Tests for GitLab CI artifacts."""

from pydantic_gitlab.artifacts import GitLabCIArtifacts, GitLabCIArtifactsReports


class TestGitLabCIArtifactsReports:
    """Test GitLabCIArtifactsReports model."""

    def test_empty_reports(self):
        """Test empty reports object."""
        reports = GitLabCIArtifactsReports()
        dumped = reports.model_dump(exclude_none=True)
        assert dumped == {}

    def test_junit_reports(self):
        """Test JUnit reports configuration."""
        # Single file
        reports = GitLabCIArtifactsReports(junit="test-results.xml")
        assert reports.junit == ["test-results.xml"]

        # Multiple files
        reports = GitLabCIArtifactsReports(junit=["test1.xml", "test2.xml"])
        assert reports.junit == ["test1.xml", "test2.xml"]

        # Glob pattern
        reports = GitLabCIArtifactsReports(junit="**/test-*.xml")
        assert reports.junit == ["**/test-*.xml"]

    def test_coverage_report(self):
        """Test coverage report configuration."""
        reports = GitLabCIArtifactsReports(coverage_report={"coverage_format": "cobertura", "path": "coverage.xml"})
        assert reports.coverage_report == {"coverage_format": "cobertura", "path": "coverage.xml"}

    def test_all_report_types(self):
        """Test all supported report types."""
        reports = GitLabCIArtifactsReports(
            junit=["junit.xml"],
            coverage_report={"coverage_format": "cobertura", "path": "coverage.xml"},
            codequality="codequality.json",
            dotenv="build.env",
            lsif="lsif.json",
            sast="sast.json",
            dependency_scanning="dependency-scanning.json",
            container_scanning="container-scanning.json",
            dast="dast.json",
            license_scanning="license-scanning.json",
            license_management="license-management.json",
            performance="performance.json",
            requirements="requirements.json",
            secret_detection="secrets.json",
            terraform="tfplan.json",
            cyclonedx="sbom.xml",
            annotations="annotations.json",
        )

        dumped = reports.model_dump()
        assert len(dumped) == 17  # All report types
        assert dumped["junit"] == ["junit.xml"]
        assert dumped["codequality"] == ["codequality.json"]

    def test_path_normalization(self):
        """Test that paths are normalized to lists."""
        reports = GitLabCIArtifactsReports(sast="gl-sast-report.json", dependency_scanning=["dep1.json", "dep2.json"])

        assert isinstance(reports.sast, list)
        assert reports.sast == ["gl-sast-report.json"]
        assert reports.dependency_scanning == ["dep1.json", "dep2.json"]

    def test_extra_fields(self):
        """Test that extra fields are allowed for future report types."""
        reports = GitLabCIArtifactsReports(
            junit="junit.xml", custom_report="custom.json", future_report_type=["report1.json", "report2.json"]
        )

        assert reports.junit == ["junit.xml"]
        assert reports.custom_report == "custom.json"
        assert reports.future_report_type == ["report1.json", "report2.json"]


class TestGitLabCIArtifacts:
    """Test GitLabCIArtifacts model."""

    def test_minimal_artifacts(self):
        """Test minimal artifacts configuration."""
        artifacts = GitLabCIArtifacts(paths=["dist/"])
        assert artifacts.paths == ["dist/"]
        assert artifacts.exclude is None
        assert artifacts.expire_in is None

    def test_paths_normalization(self):
        """Test paths normalization from string to list."""
        # Single path as string
        artifacts = GitLabCIArtifacts(paths="build/output.jar")
        assert artifacts.paths == ["build/output.jar"]

        # Multiple paths as list
        artifacts = GitLabCIArtifacts(paths=["dist/", "build/", "*.log"])
        assert artifacts.paths == ["dist/", "build/", "*.log"]

    def test_exclude_paths(self):
        """Test exclude paths configuration."""
        artifacts = GitLabCIArtifacts(paths=["binaries/"], exclude=["binaries/**/*.tmp", "binaries/**/temp/*"])
        assert artifacts.paths == ["binaries/"]
        assert artifacts.exclude == ["binaries/**/*.tmp", "binaries/**/temp/*"]

    def test_expire_in(self):
        """Test expire_in configuration."""
        valid_values = [
            "30 days",
            "1 week",
            "3 months",
            "1 year",
            "never",
            "42 seconds",
            "3 mins 4 sec",
            "2h20min",
            "6 mos 1 day",
        ]

        for value in valid_values:
            artifacts = GitLabCIArtifacts(paths=["test/"], expire_in=value)
            assert artifacts.expire_in == value

    def test_expose_as(self):
        """Test expose_as configuration."""
        artifacts = GitLabCIArtifacts(paths=["public/"], expose_as="static-site")
        assert artifacts.expose_as == "static-site"

    def test_name(self):
        """Test artifacts name configuration."""
        artifacts = GitLabCIArtifacts(paths=["binaries/"], name="$CI_JOB_NAME-$CI_COMMIT_REF_SLUG")
        assert artifacts.name == "$CI_JOB_NAME-$CI_COMMIT_REF_SLUG"

    def test_public(self):
        """Test public artifacts configuration."""
        artifacts = GitLabCIArtifacts(paths=["public/"], public=False)
        assert artifacts.public is False

    def test_untracked(self):
        """Test untracked files configuration."""
        artifacts = GitLabCIArtifacts(untracked=True, paths=["binaries/"])
        assert artifacts.untracked is True

    def test_when(self):
        """Test when configuration."""
        when_values = ["on_success", "on_failure", "always"]

        for when in when_values:
            artifacts = GitLabCIArtifacts(paths=["test/"], when=when)
            assert artifacts.when == when

    def test_reports(self):
        """Test artifacts reports."""
        artifacts = GitLabCIArtifacts(
            paths=["coverage/"],
            reports={
                "junit": ["test-results/*.xml"],
                "coverage_report": {"coverage_format": "cobertura", "path": "coverage/cobertura-coverage.xml"},
            },
        )

        assert isinstance(artifacts.reports, GitLabCIArtifactsReports)
        assert artifacts.reports.junit == ["test-results/*.xml"]
        assert artifacts.reports.coverage_report == {
            "coverage_format": "cobertura",
            "path": "coverage/cobertura-coverage.xml",
        }

    def test_access(self):
        """Test access level configuration."""
        access_values = ["none", "developer", "all"]

        for access in access_values:
            artifacts = GitLabCIArtifacts(paths=["secure/"], access=access)
            assert artifacts.access == access

    def test_complex_artifacts(self):
        """Test complex artifacts configuration."""
        artifacts = GitLabCIArtifacts(
            paths=["dist/", "build/"],
            exclude=["**/*.tmp", "**/temp/*"],
            expire_in="1 week",
            expose_as="build-artifacts",
            name="$CI_JOB_NAME-$CI_COMMIT_SHORT_SHA",
            untracked=False,
            when="on_success",
            reports={
                "junit": "test-results.xml",
                "coverage_report": {"coverage_format": "cobertura", "path": "coverage.xml"},
            },
            access="developer",
        )

        dumped = artifacts.model_dump()
        assert dumped["paths"] == ["dist/", "build/"]
        assert dumped["exclude"] == ["**/*.tmp", "**/temp/*"]
        assert dumped["expire_in"] == "1 week"
        assert dumped["expose_as"] == "build-artifacts"
        assert dumped["name"] == "$CI_JOB_NAME-$CI_COMMIT_SHORT_SHA"
        assert dumped["untracked"] is False
        assert dumped["when"] == "on_success"
        assert "reports" in dumped
        assert dumped["access"] == "developer"

    def test_from_dict(self):
        """Test creating artifacts from dictionary."""
        artifacts_dict = {
            "paths": ["target/*.jar", "target/*.war"],
            "expire_in": "30 days",
            "reports": {"junit": "target/surefire-reports/TEST-*.xml"},
        }

        artifacts = GitLabCIArtifacts(**artifacts_dict)
        assert artifacts.paths == ["target/*.jar", "target/*.war"]
        assert artifacts.expire_in == "30 days"
        assert artifacts.reports.junit == ["target/surefire-reports/TEST-*.xml"]

    def test_validation_at_least_paths_or_reports(self):
        """Test that artifacts must have either paths or reports."""
        # Valid with paths
        artifacts1 = GitLabCIArtifacts(paths=["dist/"])
        assert artifacts1.paths == ["dist/"]

        # Valid with reports only
        artifacts2 = GitLabCIArtifacts(reports={"junit": "test.xml"})
        assert artifacts2.reports.junit == ["test.xml"]

        # Valid with both
        artifacts3 = GitLabCIArtifacts(paths=["dist/"], reports={"junit": "test.xml"})
        assert artifacts3.paths == ["dist/"]
        assert artifacts3.reports.junit == ["test.xml"]

        # Valid - empty artifacts are allowed (they can have other fields like expire_in)
        artifacts4 = GitLabCIArtifacts()
        assert artifacts4.paths is None
        assert artifacts4.reports is None

    def test_extra_fields(self):
        """Test that extra fields are preserved."""
        artifacts = GitLabCIArtifacts(paths=["dist/"], custom_field="custom_value", future_option=True)

        assert artifacts.paths == ["dist/"]
        assert artifacts.custom_field == "custom_value"
        assert artifacts.future_option is True
