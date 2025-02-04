from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
# from iot_analytics_project.api.db.db_connection import get_db_connection
# from iot_analytics_project.api.db.models import IoTData
from db.db_connection import get_db_connection
from db.models import IoTData
from pydantic import BaseModel

router = APIRouter()


class IoTDataResponse(BaseModel):
    timestamp: datetime
    device_id: str
    voltage: float
    current: float
    device_type: str
    location: str


class DeviceResponse(BaseModel):
    device_id: str
    device_type: str
    location: str


@router.post("/data")
async def create_iot_data(data: IoTData):
    # Connect to the database
    conn = await get_db_connection()

    # Prepare the query
    query = """
        INSERT INTO iot_data(timestamp, device_id, voltage, current, device_type, location)
        VALUES($1, $2, $3, $4, $5, $6)
    """

    # Insert the data into the table
    try:
        await conn.execute(
            query,
            data.timestamp or datetime.utcnow(),  # Use UTC now if no timestamp provided
            data.device_id,
            data.voltage,
            data.current,
            data.device_type,
            data.location,
        )
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    # Close the connection
    await conn.close()

    return {"message": "Data inserted successfully"}


@router.get("/data/{device_id}")
async def get_iot_data_by_device_id(device_id: str, limit:  int = Query(default=100, ge=0, le=1000),
                           offset: int = Query(default=0, ge=0, le=1000)):
    conn = await get_db_connection()

    query = """
        SELECT * FROM iot_data WHERE device_id = $1
    """

    try:
        result = await conn.fetch(query, device_id)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    await conn.close()

    # Apply offset manually by slicing the result
    paginated_result = result[offset:offset + limit]

    # Format the response as a list of IoTDataResponse objects
    data = [
        IoTDataResponse(
            timestamp=row["timestamp"],
            device_id=row["device_id"],
            voltage=row["voltage"],
            current=row["current"],
            device_type=row["device_type"],
            location=row["location"],
        )
        for row in paginated_result
    ]

    return data, offset

@router.get("/data")
async def get_all_iot_data(limit:  int = Query(default=100, ge=0, le=1000),
                           offset: int = Query(default=0, ge=0, le=1000)):
    """
    Fetch all IoT data with pagination for QuestDB.

    Query Parameters:
    - limit: Maximum number of records to retrieve (default: 100).
    - offset: Starting point for the query (default: 0).

    Returns:
    - List of IoT data records.
    """
    conn = await get_db_connection()

    # Fetch more rows than needed, and apply offset manually
    query = f"""
        SELECT * 
        FROM iot_data 
        ORDER BY timestamp DESC 
        LIMIT {limit + offset}
    """

    try:
        result = await conn.fetch(query)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    await conn.close()

    # Apply offset manually by slicing the result
    paginated_result = result[offset:offset + limit]

    # Format the response as a list of IoTDataResponse objects
    data = [
        IoTDataResponse(
            timestamp=row["timestamp"],
            device_id=row["device_id"],
            voltage=row["voltage"],
            current=row["current"],
            device_type=row["device_type"],
            location=row["location"],
        )
        for row in paginated_result
    ]

    return data, offset


@router.get("/devices")
async def get_all_devices():
    conn = await get_db_connection()

    query = f"""
        SELECT DISTINCT device_id
        FROM iot_data
    """

    try:
        result = await conn.fetch(query)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    await conn.close()

    return list(map(lambda x: x.get('device_id'), result))