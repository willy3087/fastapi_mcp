#!/usr/bin/env python
"""
Run the FastAPI-MCP example.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting FastAPI-MCP example...")
    print("Visit http://localhost:8000/docs to see the API documentation")
    print("Your MCP server is available at http://localhost:8000/mcp")

    uvicorn.run(
        "simple_integration:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
