import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Example data
s1nray_items_db = [{"item_name": "Item One"}, {"item_name": "Item Two"}]

s1nray_login = "postgresql://username:password@localhost/dbname"


class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


@app.get("/")
async def read_root():
    return {"message": "Hello, S1nRay"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id >= len(s1nray_items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    return s1nray_items_db[item_id]


@app.post("/items/")
async def create_item(item: Item):
    s1nray_items_db.append(item.dict())
    return {"message": "Item created successfully"}


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    if item_id >= len(s1nray_items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    s1nray_items_db[item_id] = item.dict()
    return {"message": "Item updated successfully"}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id >= len(s1nray_items_db):
        raise HTTPException(status_code=404, detail="Item not found")
    del s1nray_items_db[item_id]
    return {"message": "Item deleted successfully"}


# Connect to PostgreSQL database
async def connect_to_db():
    return await asyncpg.connect(s1nray_login)


# Close database connection
async def close_db_connection(conn):
    await conn.close()


@app.on_event("startup")
async def startup_event():
    app.state.pg_pool = await asyncpg.create_pool(s1nray_login)


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.pg_pool.close()


# Example data model
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


# CRUD operations
async def create_item(conn, item: Item):
    await conn.execute("INSERT INTO items (name, description, price, tax) VALUES ($1, $2, $3, $4)",
                       item.name, item.description, item.price, item.tax)


async def get_item(conn, item_id: int):
    record = await conn.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return record


# FastAPI endpoints
@app.post("/items/")
async def create_item_endpoint(item: Item):
    conn = await app.state.pg_pool.acquire()
    try:
        await create_item(conn, item)
    finally:
        await app.state.pg_pool.release(conn)
    return {"message": "Item created successfully"}


@app.get("/items/{item_id}")
async def read_item_endpoint(item_id: int):
    conn = await app.state.pg_pool.acquire()
    try:
        return await get_item(conn, item_id)
    finally:
        await app.state.pg_pool.release(conn)
