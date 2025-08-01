# Pydantic GitLab

[![PyPI version](https://badge.fury.io/py/pydantic-gitlab.svg)](https://badge.fury.io/py/pydantic-gitlab)
[![Python](https://img.shields.io/pypi/pyversions/pydantic-gitlab.svg)](https://pypi.org/project/pydantic-gitlab/)
[![Test](https://github.com/johnlepikhin/pydantic-gitlab/workflows/test/badge.svg)](https://github.com/johnlepikhin/pydantic-gitlab/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Python library for parsing and validating GitLab CI YAML files using Pydantic dataclasses.

## Features

- ✅ Full support for GitLab CI YAML syntax
- 🔍 Comprehensive validation with helpful error messages
- 📦 Type-safe dataclasses for all GitLab CI structures
- 🐍 Python 3.9+ support
- 📝 Excellent IDE support with autocompletion

## Installation

```bash
pip install pydantic-gitlab
```

## Quick Start

```python
import yaml
from pydantic_gitlab import GitLabCI

# Load your .gitlab-ci.yml file
with open(".gitlab-ci.yml", "r") as f:
    yaml_content = yaml.safe_load(f)

# Parse and validate
try:
    ci_config = GitLabCI(**yaml_content)
    print("✅ Valid GitLab CI configuration!")
    
    # Access configuration
    for job_name, job in ci_config.jobs.items():
        print(f"Job: {job_name}")
        print(f"  Stage: {job.stage}")
        print(f"  Script: {job.script}")
        
except Exception as e:
    print(f"❌ Invalid configuration: {e}")
```

## Supported GitLab CI Features

- ✅ Jobs with all keywords (script, image, services, artifacts, etc.)
- ✅ Stages and dependencies
- ✅ Rules and conditions
- ✅ Variables (global and job-level)
- ✅ Include configurations
- ✅ Workflow rules
- ✅ Caching
- ✅ Artifacts and reports
- ✅ Environments and deployments
- ✅ Parallel jobs and matrix builds
- ✅ Trigger jobs
- ✅ Pages job

## Example

```python
from pydantic_gitlab import GitLabCI, GitLabCIJob, WhenType

# Create a job programmatically
build_job = GitLabCIJob(
    stage="build",
    script=["echo 'Building...'", "make build"],
    artifacts={
        "paths": ["dist/"],
        "expire_in": "1 week"
    }
)

# Create CI configuration
ci = GitLabCI(
    stages=["build", "test", "deploy"],
    variables={"DOCKER_DRIVER": "overlay2"}
)

# Add job to configuration
ci.add_job("build", build_job)

# Validate dependencies
errors = ci.validate_job_dependencies()
if errors:
    for error in errors:
        print(f"Error: {error}")
```

## Why Pydantic GitLab?

### Comparison with Plain YAML Parsing

Using plain YAML parsing:
```python
import yaml

# Plain YAML - no validation, no type hints
with open(".gitlab-ci.yml") as f:
    config = yaml.safe_load(f)
    
# Risky - might fail at runtime
job_script = config["build"]["script"]  # KeyError?
job_image = config["build"]["image"]    # KeyError?
```

Using Pydantic GitLab:
```python
from pydantic_gitlab import GitLabCI

# Type-safe with validation
with open(".gitlab-ci.yml") as f:
    data = yaml.safe_load(f)
ci = GitLabCI(**data)

# IDE autocompletion, type checking
if build_job := ci.get_job("build"):
    print(build_job.script)  # Guaranteed to exist
    print(build_job.image)   # Optional[str] - might be None
```

### Benefits

- **🛡️ Validation**: Catch configuration errors before running pipelines
- **🔍 Type Safety**: Full type hints for better IDE support and fewer runtime errors
- **📝 Documentation**: Each field is documented with GitLab CI reference
- **🚀 Productivity**: Autocomplete for all GitLab CI keywords
- **🧪 Testing**: Easily create and validate CI configurations in tests

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/johnlepikhin/pydantic-gitlab.git
cd pydantic-gitlab

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Run linting
ruff check .

# Run type checking
mypy src

# Format code
ruff format .
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
