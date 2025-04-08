from typing import Optional, List

from fastapi import FastAPI, Query, Path, Body
import pytest

from .types import Item


@pytest.fixture
def simple_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Test API",
        description="A test API app for unit testing",
        version="0.1.0",
    )

    @app.get("/items/", response_model=List[Item], tags=["items"], operation_id="list_items")
    async def list_items(
        skip: int = Query(0, description="Number of items to skip"),
        limit: int = Query(10, description="Max number of items to return"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
    ):
        """List all items with pagination and sorting options."""
        return []

    @app.get("/items/{item_id}", response_model=Item, tags=["items"], operation_id="get_item")
    async def read_item(
        item_id: int = Path(..., description="The ID of the item to retrieve"),
        include_details: bool = Query(False, description="Include additional details"),
    ):
        """Get a specific item by its ID with optional details."""
        return {"id": item_id, "name": "Test Item", "price": 10.0}

    @app.post("/items/", response_model=Item, tags=["items"], operation_id="create_item")
    async def create_item(item: Item = Body(..., description="The item to create")):
        """Create a new item in the database."""
        return item

    @app.put("/items/{item_id}", response_model=Item, tags=["items"], operation_id="update_item")
    async def update_item(
        item_id: int = Path(..., description="The ID of the item to update"),
        item: Item = Body(..., description="The updated item data"),
    ):
        """Update an existing item."""
        item.id = item_id
        return item

    @app.delete("/items/{item_id}", tags=["items"], operation_id="delete_item")
    async def delete_item(item_id: int = Path(..., description="The ID of the item to delete")):
        """Delete an item from the database."""
        return {"message": "Item deleted successfully"}

    return app
