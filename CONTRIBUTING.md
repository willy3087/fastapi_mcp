# Contributing to FastAPI-MCP

First off, thank you for considering contributing to FastAPI-MCP! 

## Development Setup

1. Make sure you have Python 3.10+ installed
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
3. Fork the repository
4. Clone your fork

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/fastapi_mcp.git
cd fastapi-mcp

# Add the upstream remote
git remote add upstream https://github.com/tadata-org/fastapi_mcp.git
```

5. Set up the development environment:

```bash
# Create a virtual environment with uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies with uv
uv sync --extra dev

# Alternatively, using pip
# python -m venv venv
# source venv/bin/activate  # On Windows: venv\Scripts\activate
# pip install -e ".[dev]"
```

## Development Process

1. Fork the repository and set the upstream remote
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run type checking (`uv run mypy .`)
5. Run the tests (`uv run pytest`)
6. Format your code (`uv run ruff check .` and `uv run ruff format .`)
7. Commit your changes (`git commit -m 'Add some amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request on [the project repository](https://github.com/tadata-org/fastapi_mcp/)

## Code Style

We use the following tools to ensure code quality:

- **ruff** for linting
- **mypy** for type checking

Please make sure your code passes all checks before submitting a pull request:

```bash
# Using uv
uv run ruff check .
uv run mypy .

# Or directly if tools are installed
ruff check .
mypy .
```

## Testing

We use pytest for testing. Please write tests for any new features and ensure all tests pass:

```bash
# Using uv
uv run pytest

# Or directly
pytest
```

## Pull Request Process

1. Ensure your code follows the style guidelines of the project
2. Update the README.md with details of changes if applicable
3. The versioning scheme we use is [SemVer](http://semver.org/)
4. Include a descriptive commit message
5. Your pull request will be merged once it's reviewed and approved

## Code of Conduct

Please note we have a code of conduct, please follow it in all your interactions with the project.

- Be respectful and inclusive
- Be collaborative
- When disagreeing, try to understand why
- A diverse community is a strong community

## Questions?

Don't hesitate to open an issue if you have any questions about contributing to FastAPI-MCP. 