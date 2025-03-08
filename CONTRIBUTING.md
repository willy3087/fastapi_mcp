# Contributing to FastAPI-MCP

First off, thank you for considering contributing to FastAPI-MCP! 

## Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`pytest`)
5. Format your code (`black .` and `isort .`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/tadata-org/fastapi_mcp
cd fastapi-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## Code Style

We use the following tools to ensure code quality:

- **Black** for code formatting
- **isort** for import sorting
- **ruff** for linting
- **mypy** for type checking

Please make sure your code passes all checks before submitting a pull request:

```bash
black .
isort .
ruff check .
mypy .
```

## Testing

We use pytest for testing. Please write tests for any new features and ensure all tests pass:

```bash
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