# Installation Guide

This guide will help you install and set up FastAPI-MCP on your system.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

## Installation from PyPI (Recommended)

The recommended way to install FastAPI-MCP is directly from [PyPI](https://pypi.org/project/fastapi-mcp/):

```bash
pip install fastapi-mcp
```

This will install the latest stable version of FastAPI-MCP along with all its dependencies.

## Installation from Source

If you need the latest development version or want to contribute to the project, you can install FastAPI-MCP from source:

```bash
# Clone the repository
git clone https://github.com/tadata-org/fastapi_mcp.git
cd fastapi-mcp

# Install the package
pip install -e .
```

## Verifying Installation

To verify that FastAPI-MCP is installed correctly, run:

```bash
fastapi-mcp --help
```

You should see the help message for the FastAPI-MCP CLI.

## Installing Development Dependencies

If you want to contribute to FastAPI-MCP or run the tests, you can install the development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

To run the tests, make sure you have installed the development dependencies, then run:

```bash
pytest
```
