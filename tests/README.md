# FastAPI-MCP Test Suite

This directory contains automated tests for the FastAPI-MCP library.

## Test Files

- `test_tool_generation.py`: Tests the basic functionality of generating MCP tools from FastAPI endpoints
- `test_http_tools.py`: Tests the core HTTP tools module that converts FastAPI endpoints to MCP tools
- `test_server.py`: Tests the server module for creating and mounting MCP servers

## Running Tests

To run the tests, make sure you have installed the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run the tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fastapi_mcp

# Run a specific test file
pytest tests/test_tool_generation.py
```

## Test Structure

Each test file follows this general structure:

1. **Fixtures**: Define test fixtures for creating sample FastAPI applications
2. **Unit Tests**: Individual test functions that verify specific aspects of the library
3. **Integration Tests**: Tests that verify components work together correctly

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create a test function with a clear name that indicates what functionality it's testing
2. Use descriptive assertions that explain what is being tested
3. Keep tests focused on a single aspect of functionality
4. Use fixtures to avoid code duplication

## Manual Testing

In addition to these automated tests, manual testing can be performed using the `test_mcp_tools.py` script in the project root. This script connects to a running MCP server, initializes a session, and requests a list of available tools.

To run the manual test:

1. Start your FastAPI app with an MCP server
2. Run the test script:

```bash
python test_mcp_tools.py http://localhost:8000/mcp
```

The script will output the results of each request for manual inspection. 