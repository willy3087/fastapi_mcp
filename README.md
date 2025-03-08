# FastAPI-MCP

A magical, zero-configuration tool for generating Model Context Protocol (MCP) servers from FastAPI applications.

## Features

- **Automatic discovery** of all FastAPI endpoints in your application
- **Zero configuration** required - just point it at your FastAPI app and it works
- **CLI tool** for easy generation and execution of MCP servers
- **Stdio support** for MCP protocol communication
- **Type-safe conversion** from FastAPI endpoints to MCP tools
- **Documentation preservation** from FastAPI to MCP
- **Claude integration** for easy installation and use with Claude desktop application
- **API Integration** - automatically makes HTTP requests to your FastAPI endpoints

## Installation

```bash
pip install fastapi-mcp
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Usage

### Generate an MCP server from a FastAPI app

```bash
# Point to a FastAPI application file or module
fastapi-mcp generate app.py

# Or specify the app variable if it's not named 'app'
fastapi-mcp generate module.py:my_app

# Use a custom base URL for the API endpoints (default: http://localhost:8000)
fastapi-mcp generate app.py --base-url https://api.example.com
```

### Preview the generated MCP server

```bash
fastapi-mcp preview
```

### Run the generated MCP server

```bash
fastapi-mcp run
```

### Install the server for Claude

```bash
fastapi-mcp install
```

## How It Works

FastAPI-MCP automatically:

1. Discovers all FastAPI endpoints in your application
2. Converts route handlers to MCP tools
3. Maps request/response models to MCP schemas
4. Preserves documentation and type information
5. Generates a standalone MCP server that uses the official MCP Python SDK
6. **Makes actual HTTP requests** to the underlying FastAPI endpoints

## Example

Original FastAPI code:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    """Get details for a specific item"""
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """Update an item with new information"""
    return {"item_id": item_id, "item": item}
```

Generated MCP server:

```python
# Generated MCP server
# Original FastAPI app: FastAPI

from mcp.server import FastMCP
import json
import requests
from typing import Dict, List, Optional, Union, Any
try:
    from pydantic import BaseModel
except ImportError:
    from pydantic.main import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None

# Original handler: __main__.read_item
# Original handler: __main__.update_item

mcp = FastMCP("FastAPI")

@mcp.tool()
async def read_item(item_id: int, q: str = None) -> Any:
    """Get details for a specific item

    Original route: GET /items/{item_id}
    """
    # Original handler: __main__.read_item
    url = f'http://localhost:8000/items/{item_id}'
    params = {}
    if q is not None:
        params['q'] = q
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

@mcp.tool()
async def update_item(item_id: int, name: str, price: float, is_offer: bool = None) -> Any:
    """Update an item with new information

    Original route: PUT /items/{item_id}
    """
    # Original handler: __main__.update_item
    url = f'http://localhost:8000/items/{item_id}'
    item = Item(**{"name": name, "price": price, "is_offer": is_offer})
    json_data = item.dict()
    response = requests.put(url, json=json_data)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
```

## Integration with FastAPI

The generated MCP server makes HTTP requests to your actual FastAPI server, which must be running separately. You can:

1. Run your FastAPI application normally (e.g., with `uvicorn app:app`)
2. Generate the MCP server with a base URL pointing to your running FastAPI server
3. Run the MCP server separately to provide MCP tools for LLMs

If your API requires authentication, you can customize the generated server code to include the necessary headers or tokens.

## Using with Claude

FastAPI-MCP makes it easy to use your API endpoints with Claude:

1. Generate an MCP server from your FastAPI app
2. Install the server: `fastapi-mcp install`
3. Open Claude desktop app
4. Your API endpoints will be available as tools to Claude

## Examples

For more examples, see the [examples](examples) directory.

## Requirements

- Python 3.10+
- FastAPI 0.100.0+
- Pydantic 2.0.0+
- mcp 1.3.0+
- requests 2.25.0+

## Contributing

Contributions are welcome! Please feel free to submit a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## License

MIT License. Copyright (c) 2024 Tadata Inc.

## About

Developed and maintained by [Tadata Inc.](https://github.com/tadata-org)
