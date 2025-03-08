from setuptools import setup

setup(
    name="fastapi-mcp",
    version="0.1.0",
    description="Automatic MCP server generator for FastAPI applications - converts FastAPI endpoints to MCP tools for LLM integration",
    author="Tadata Inc.",
    author_email="itay@tadata.com",
    packages=["fastapi_mcp"],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.100.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "mcp>=1.3.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.20.0",
        "requests>=2.25.0",
        "inspect-mate>=0.0.2",
    ],
    entry_points={
        "console_scripts": [
            "fastapi-mcp=fastapi_mcp.cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Framework :: FastAPI",
    ],
    keywords=["fastapi", "mcp", "llm", "claude", "ai", "tools", "api", "conversion"],
) 