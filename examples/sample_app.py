"""
A sample FastAPI application for demonstration purposes.
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Sample API",
    description="A sample FastAPI application for demonstration purposes.",
    version="0.1.0",
)

class Item(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="The name of the item")
    description: Optional[str] = Field(None, description="The description of the item")
    price: float = Field(..., description="The price of the item", gt=0)
    tax: Optional[float] = Field(None, description="The tax rate for the item")
    tags: List[str] = Field(default_factory=list, description="Tags for the item")

# In-memory database
items_db = {}
item_id_counter = 1

@app.get("/items/", response_model=List[Item], tags=["items"])
def list_items(skip: int = 0, limit: int = 10):
    """
    List all items in the database.
    
    Returns a list of items, with pagination support.
    """
    return list(items_db.values())[skip : skip + limit]

@app.get("/items/{item_id}", response_model=Item, tags=["items"])
def read_item(item_id: int):
    """
    Get a specific item by its ID.
    
    Raises a 404 error if the item does not exist.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items/", response_model=Item, tags=["items"])
def create_item(item: Item):
    """
    Create a new item in the database.
    
    Returns the created item with its assigned ID.
    """
    global item_id_counter
    item.id = item_id_counter
    items_db[item_id_counter] = item
    item_id_counter += 1
    return item

@app.put("/items/{item_id}", response_model=Item, tags=["items"])
def update_item(item_id: int, item: Item):
    """
    Update an existing item.
    
    Raises a 404 error if the item does not exist.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Preserve the item ID
    item.id = item_id
    items_db[item_id] = item
    return item

@app.delete("/items/{item_id}", tags=["items"])
def delete_item(item_id: int):
    """
    Delete an item from the database.
    
    Raises a 404 error if the item does not exist.
    """
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items_db[item_id]
    return {"message": "Item deleted successfully"}

@app.get("/items/search/", response_model=List[Item], tags=["search"])
def search_items(
    q: Optional[str] = Query(None, description="Search query string"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    tags: List[str] = Query([], description="Filter by tags"),
):
    """
    Search for items with various filters.
    
    Returns a list of items that match the search criteria.
    """
    results = list(items_db.values())
    
    # Filter by search query
    if q:
        q = q.lower()
        results = [
            item for item in results
            if q in item.name.lower() or (item.description and q in item.description.lower())
        ]
    
    # Filter by price range
    if min_price is not None:
        results = [item for item in results if item.price >= min_price]
    if max_price is not None:
        results = [item for item in results if item.price <= max_price]
    
    # Filter by tags
    if tags:
        results = [
            item for item in results
            if all(tag in item.tags for tag in tags)
        ]
    
    return results


if __name__ == "__main__":
    import uvicorn
    
    # Create some sample items
    sample_items = [
        Item(name="Hammer", description="A tool for hammering nails", price=9.99, tags=["tool", "hardware"]),
        Item(name="Screwdriver", description="A tool for driving screws", price=7.99, tags=["tool", "hardware"]),
        Item(name="Wrench", description="A tool for tightening bolts", price=12.99, tags=["tool", "hardware"]),
        Item(name="Saw", description="A tool for cutting wood", price=19.99, tags=["tool", "hardware", "cutting"]),
        Item(name="Drill", description="A tool for drilling holes", price=49.99, tags=["tool", "hardware", "power"]),
    ]
    
    # Add the sample items to the database
    for item in sample_items:
        create_item(item)
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8000) 