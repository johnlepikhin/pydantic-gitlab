"""Tests for GitLab CI cache."""

import pytest
from pydantic import ValidationError

from pydantic_gitlab.cache import GitLabCICache, GitLabCICacheKey


class TestGitLabCICacheKey:
    """Test GitLabCICacheKey model."""

    def test_simple_key_string(self):
        """Test simple cache key as string."""
        key = GitLabCICacheKey(key="my-cache-key")
        assert key.key == "my-cache-key"
        assert key.files is None
        assert key.prefix is None

    def test_key_with_files(self):
        """Test cache key with files."""
        key = GitLabCICacheKey(files=["package-lock.json", "yarn.lock"])
        assert key.key is None
        assert key.files == ["package-lock.json", "yarn.lock"]
        assert key.prefix is None

    def test_key_with_files_and_prefix(self):
        """Test cache key with files and prefix."""
        key = GitLabCICacheKey(files=["Gemfile.lock"], prefix="$CI_JOB_NAME")
        assert key.files == ["Gemfile.lock"]
        assert key.prefix == "$CI_JOB_NAME"

    def test_files_normalization(self):
        """Test files normalization from string to list."""
        key = GitLabCICacheKey(files="package.json")
        assert key.files == ["package.json"]

    def test_validation_key_or_files_required(self):
        """Test that either key or files is required."""
        # Valid with key
        key1 = GitLabCICacheKey(key="cache-key")
        assert key1.key == "cache-key"

        # Valid with files
        key2 = GitLabCICacheKey(files=["pom.xml"])
        assert key2.files == ["pom.xml"]

        # Invalid - neither key nor files
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey()

        assert "key" in str(exc_info.value).lower() or "files" in str(exc_info.value).lower()

    def test_both_key_and_files(self):
        """Test that both key and files cannot be specified."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey(key="my-key", files=["package.json"])

        assert "cannot specify both" in str(exc_info.value).lower()

    def test_prefix_requires_files(self):
        """Test that prefix requires files."""
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICacheKey(key="my-key", prefix="prefix")

        assert "prefix" in str(exc_info.value).lower()


class TestGitLabCICache:
    """Test GitLabCICache model."""

    def test_simple_cache(self):
        """Test simple cache configuration."""
        cache = GitLabCICache(key="cache-key", paths=["vendor/", "node_modules/"])
        assert cache.key == "cache-key"
        assert cache.paths == ["vendor/", "node_modules/"]

    def test_cache_with_key_object(self):
        """Test cache with key as object."""
        cache = GitLabCICache(key={"files": ["package-lock.json"], "prefix": "$CI_JOB_NAME"}, paths=["node_modules/"])

        assert isinstance(cache.key, GitLabCICacheKey)
        assert cache.key.files == ["package-lock.json"]
        assert cache.key.prefix == "$CI_JOB_NAME"

    def test_paths_normalization(self):
        """Test paths normalization from string to list."""
        cache = GitLabCICache(key="cache-key", paths="vendor/")
        assert cache.paths == ["vendor/"]

    def test_cache_policy(self):
        """Test cache policy options."""
        policies = ["pull", "push", "pull-push"]

        for policy in policies:
            cache = GitLabCICache(key="cache-key", paths=["vendor/"], policy=policy)
            assert cache.policy == policy

    def test_cache_untracked(self):
        """Test cache untracked files."""
        cache = GitLabCICache(key="cache-key", untracked=True)
        assert cache.untracked is True
        assert cache.paths is None

    def test_cache_unprotect(self):
        """Test cache unprotect option."""
        cache = GitLabCICache(key="cache-key", paths=["vendor/"], unprotect=True)
        assert cache.unprotect is True

    def test_cache_when(self):
        """Test cache when option."""
        when_values = ["on_success", "on_failure", "always"]

        for when in when_values:
            cache = GitLabCICache(key="cache-key", paths=["vendor/"], when=when)
            assert cache.when == when

    def test_cache_fallback_keys(self):
        """Test cache fallback keys."""
        cache = GitLabCICache(key="primary-key", paths=["vendor/"], fallback_keys=["fallback-1", "fallback-2"])
        assert cache.fallback_keys == ["fallback-1", "fallback-2"]

    def test_complex_cache(self):
        """Test complex cache configuration."""
        cache = GitLabCICache(
            key={"files": ["Gemfile.lock", ".ruby-version"], "prefix": "$CI_JOB_NAME"},
            paths=["vendor/ruby/", ".bundle/"],
            policy="pull-push",
            untracked=False,
            unprotect=False,
            when="on_success",
            fallback_keys=["$CI_COMMIT_REF_SLUG", "default"],
        )

        dumped = cache.model_dump()
        assert isinstance(dumped["key"], dict)
        assert dumped["key"]["files"] == ["Gemfile.lock", ".ruby-version"]
        assert dumped["key"]["prefix"] == "$CI_JOB_NAME"
        assert dumped["paths"] == ["vendor/ruby/", ".bundle/"]
        assert dumped["policy"] == "pull-push"
        assert dumped["untracked"] is False
        assert dumped["unprotect"] is False
        assert dumped["when"] == "on_success"
        assert dumped["fallback_keys"] == ["$CI_COMMIT_REF_SLUG", "default"]

    def test_cache_as_list(self):
        """Test that cache can be provided as a list."""
        # This is typically handled at a higher level, but we can test the model
        cache1 = GitLabCICache(key="cache-1", paths=["vendor/"])
        cache2 = GitLabCICache(key="cache-2", paths=["node_modules/"])

        caches = [cache1, cache2]
        assert len(caches) == 2
        assert caches[0].key == "cache-1"
        assert caches[1].key == "cache-2"

    def test_from_dict(self):
        """Test creating cache from dictionary."""
        cache_dict = {"key": {"files": ["yarn.lock"]}, "paths": ["node_modules/", ".yarn/"], "policy": "pull"}

        cache = GitLabCICache(**cache_dict)
        assert isinstance(cache.key, GitLabCICacheKey)
        assert cache.key.files == ["yarn.lock"]
        assert cache.paths == ["node_modules/", ".yarn/"]
        assert cache.policy == "pull"

    def test_validation_paths_or_untracked_required(self):
        """Test that either paths or untracked is required."""
        # Valid with paths
        cache1 = GitLabCICache(key="key", paths=["vendor/"])
        assert cache1.paths == ["vendor/"]

        # Valid with untracked
        cache2 = GitLabCICache(key="key", untracked=True)
        assert cache2.untracked is True

        # Valid with both
        cache3 = GitLabCICache(key="key", paths=["vendor/"], untracked=True)
        assert cache3.paths == ["vendor/"]
        assert cache3.untracked is True

        # Invalid - neither paths nor untracked
        with pytest.raises(ValidationError) as exc_info:
            GitLabCICache(key="key")

        assert "paths" in str(exc_info.value).lower() or "untracked" in str(exc_info.value).lower()

    def test_extra_fields(self):
        """Test that extra fields are preserved."""
        cache = GitLabCICache(key="cache-key", paths=["vendor/"], custom_option="value", future_feature=True)

        assert cache.key == "cache-key"
        assert cache.paths == ["vendor/"]
        assert cache.custom_option == "value"
        assert cache.future_feature is True

    def test_cache_key_with_variables(self):
        """Test cache key with CI/CD variables."""
        cache = GitLabCICache(key="$CI_COMMIT_REF_SLUG-$CI_JOB_NAME", paths=["build/"])
        assert cache.key == "$CI_COMMIT_REF_SLUG-$CI_JOB_NAME"

    def test_model_dump_excludes_none(self):
        """Test that None values are excluded from dump."""
        cache = GitLabCICache(key="cache-key", paths=["vendor/"])

        dumped = cache.model_dump()
        assert "key" in dumped
        assert "paths" in dumped
        assert "policy" not in dumped  # None values excluded
        assert "untracked" not in dumped
        assert "when" not in dumped
