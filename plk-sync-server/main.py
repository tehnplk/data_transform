import os
import json
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Json

from config import settings
from db import close_connection_pool, get_connection, init_connection_pool


class RawCreateRequest(BaseModel):
    hoscode: str = Field(min_length=1, max_length=20)
    source: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]
    sync_datetime: datetime | None = None


app = FastAPI(title="PLK Sync Raw API", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    await init_connection_pool()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_connection_pool()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/raw")
async def create_raw_record(request: RawCreateRequest):
    insert_sql = """
        INSERT INTO raw (hoscode, source, payload, sync_datetime)
        VALUES (%s, %s, %s::jsonb, COALESCE(%s, NOW()))
        RETURNING hoscode, source, payload, sync_datetime;
    """
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    insert_sql,
                    (
                        request.hoscode,
                        request.source,
                        Json(request.payload),
                        request.sync_datetime,
                    ),
                )
                created = await cur.fetchone()
            await conn.commit()
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {error}")

    return {
        "message": "inserted",
        "data": {
            "hoscode": created[0],
            "source": created[1],
            "payload": created[2],
            "sync_datetime": created[3],
        },
    }


@app.get("/check_last")
async def check_last_record():
    select_sql = """
        SELECT hoscode, source, payload, sync_datetime, transform_datetime
        FROM raw
        ORDER BY sync_datetime DESC
        LIMIT 1;
    """

    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(select_sql)
                result = await cur.fetchone()

        if not result:
            return {"message": "No records found", "data": None}

        return {
            "message": "Last record found",
            "data": {
                "hoscode": result[0],
                "source": result[1],
                "payload": result[2],
                "sync_datetime": result[3],
                "transform_datetime": result[4],
            }
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}")


@app.get("/sync-scripts")
async def get_sync_scripts():
    select_sql = "SELECT script_name, description, sql_content FROM c_scripts ORDER BY script_name;"
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(select_sql)
                results = await cur.fetchall()
        
        scripts = {}
        for row in results:
            scripts[row[0]] = {
                "description": row[1],
                "sql": row[2]
            }
        return scripts
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}")


@app.get("/sync-scripts/{script_name}")
async def get_single_sync_script(script_name: str):
    select_sql = "SELECT script_name, description, sql_content FROM c_scripts WHERE script_name = %s;"
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(select_sql, (script_name,))
                result = await cur.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found")
            
        return {
            "description": result[1],
            "sql": result[2]
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database query failed: {error}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
