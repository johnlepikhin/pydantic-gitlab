# Pydantic GitLab

A modern Python library for parsing and validating GitLab CI YAML files using Pydantic dataclasses.

## Features

- ✅ Full support for GitLab CI YAML syntax
- 🔍 Comprehensive validation with helpful error messages
- 📦 Type-safe dataclasses for all GitLab CI structures
- 🐍 Python 3.8+ support
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
