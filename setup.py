from setuptools import setup

setup(
    name="fastapi-mcp",
    version="0.1.0",
    description="Automatic MCP server generator for FastAPI applications",
    author="FastAPI MCP Team",
    author_email="contact@example.com",
    packages=["fastapi_mcp"],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.100.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "mcp>=1.3.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.20.0",
        "inspect-mate>=0.0.2",
    ],
    entry_points={
        "console_scripts": [
            "fastapi-mcp=fastapi_mcp.cli:app",
        ],
    },
) 