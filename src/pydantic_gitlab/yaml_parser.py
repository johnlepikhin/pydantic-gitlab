"""YAML parser with GitLab CI specific tag support."""

from typing import Any

import yaml


class GitLabReference:
    """Represents a GitLab CI !reference tag."""

    def __init__(self, path: list[str]):
        self.path = path

    def __repr__(self) -> str:
        return f"GitLabReference({self.path})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on path."""
        if not isinstance(other, GitLabReference):
            return False
        return self.path == other.path

    def __hash__(self) -> int:
        """Make GitLabReference hashable."""
        return hash(tuple(self.path))


class GitLabYAMLLoader(yaml.SafeLoader):
    """Custom YAML loader with support for GitLab CI tags."""

    pass


class GitLabYAMLDumper(yaml.SafeDumper):
    """Custom YAML dumper with support for GitLab CI tags."""

    pass


def reference_constructor(loader: GitLabYAMLLoader, node: yaml.nodes.Node) -> GitLabReference:
    """Constructor for !reference tag."""
    if isinstance(node, yaml.SequenceNode):
        # !reference [.job, script] returns a reference object
        refs = loader.construct_sequence(node)
        return GitLabReference(refs)
    # Single reference
    value = loader.construct_scalar(node)  # type: ignore[arg-type]
    return GitLabReference([value])


# Register GitLab CI specific tags
GitLabYAMLLoader.add_constructor("!reference", reference_constructor)


def reference_representer(dumper: GitLabYAMLDumper, data: GitLabReference) -> yaml.nodes.Node:
    """Representer for GitLabReference objects."""
    return dumper.represent_sequence("!reference", data.path)


# Register representers for dumping
GitLabYAMLDumper.add_representer(GitLabReference, reference_representer)


# Support for other GitLab CI tags
# For now, we'll just pass them through as strings
def generic_tag_constructor(loader: GitLabYAMLLoader, suffix: str, node: yaml.nodes.Node) -> str:
    """Generic constructor for unknown tags - just preserve as string."""
    if isinstance(node, yaml.ScalarNode):
        return f"!{suffix} {loader.construct_scalar(node)}"
    if isinstance(node, yaml.SequenceNode):
        return f"!{suffix} {loader.construct_sequence(node)}"
    if isinstance(node, yaml.MappingNode):
        return f"!{suffix} {loader.construct_mapping(node)}"
    return f"!{suffix}"


# Add support for unknown tags (multi-constructor)
GitLabYAMLLoader.add_multi_constructor("!", generic_tag_constructor)  # type: ignore[no-untyped-call]


def resolve_references(data: Any, root: dict[str, Any]) -> Any:
    """Resolve GitLab references in the data structure.

    Args:
        data: Data structure potentially containing GitLabReference objects
        root: Root document for reference resolution

    Returns:
        Data structure with resolved references
    """
    if isinstance(data, GitLabReference):
        # Resolve the reference
        current = root
        for part in data.path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Reference not found, return as-is
                return data
        return current
    if isinstance(data, dict):
        return {k: resolve_references(v, root) for k, v in data.items()}
    if isinstance(data, list):
        result = []
        for item in data:
            resolved = resolve_references(item, root)
            # If the resolved item is a list (e.g., from reference), extend instead of append
            if isinstance(resolved, list) and isinstance(item, GitLabReference):
                result.extend(resolved)
            else:
                result.append(resolved)
        return result
    return data


def parse_gitlab_yaml(yaml_content: str, resolve_refs: bool = True) -> dict[str, Any]:
    """Parse GitLab CI YAML content with custom tag support.

    Args:
        yaml_content: YAML content as string
        resolve_refs: Whether to resolve !reference tags

    Returns:
        Parsed YAML as dictionary
    """
    data = yaml.load(yaml_content, Loader=GitLabYAMLLoader)

    if resolve_refs and isinstance(data, dict):
        # Resolve all references
        data = resolve_references(data, data)

    return data  # type: ignore[no-any-return]


def safe_load_gitlab_yaml(yaml_content: str, resolve_refs: bool = True) -> dict[str, Any]:
    """Safely parse GitLab CI YAML content with custom tag support.

    This is an alias for parse_gitlab_yaml for consistency with yaml.safe_load.

    Args:
        yaml_content: YAML content as string
        resolve_refs: Whether to resolve !reference tags

    Returns:
        Parsed YAML as dictionary
    """
    return parse_gitlab_yaml(yaml_content, resolve_refs=resolve_refs)


def dump_gitlab_yaml(data: dict[str, Any], stream: Any = None, **kwargs: Any) -> str:
    """Dump data to YAML with GitLab CI specific tag support.

    Args:
        data: Data to serialize
        stream: Optional stream to write to
        **kwargs: Additional arguments passed to yaml.dump

    Returns:
        YAML string if stream is None
    """
    kwargs.setdefault("Dumper", GitLabYAMLDumper)
    kwargs.setdefault("default_flow_style", False)
    kwargs.setdefault("sort_keys", False)
    return yaml.dump(data, stream=stream, **kwargs)  # type: ignore[no-any-return]


def safe_dump_gitlab_yaml(data: dict[str, Any], stream: Any = None, **kwargs: Any) -> str:
    """Safely dump data to YAML with GitLab CI specific tag support.

    This is an alias for dump_gitlab_yaml for consistency with yaml.safe_dump.

    Args:
        data: Data to serialize
        stream: Optional stream to write to
        **kwargs: Additional arguments passed to yaml.dump

    Returns:
        YAML string if stream is None
    """
    return dump_gitlab_yaml(data, stream=stream, **kwargs)
