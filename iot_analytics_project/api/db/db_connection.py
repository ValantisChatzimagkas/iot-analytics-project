import asyncio
import os
import asyncpg
from loguru import logger


async def get_db_connection():
    """Establish a connection to the database with retries."""
    RETRIES = 5  # Maximum number of retries
    while RETRIES > 0:
        try:
            logger.info(f"Attempting to connect to the database (retries left: {RETRIES})...")
            connection = await asyncpg.connect(
                user=os.getenv('DB_USER', 'admin'),
                password=os.getenv('DB_PASSWORD', 'quest'),
                database=os.getenv('DB_NAME', 'qdb'),
                host=os.getenv('DB_HOST', 'questdb'),
                port=int(os.getenv('DB_PORT', 8812)),
            )
            logger.info("Successfully connected to the database.")
            return connection  # Return the connection if successful
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            RETRIES -= 1
            if RETRIES == 0:
                logger.error("All retry attempts failed. Giving up.")
                raise  # Rethrow the exception after exhausting retries
            await asyncio.sleep(5)  # Wait before retrying


async def init_db():
    """Initialize the database and ensure the required table exists."""
    conn = None
    try:
        conn = await get_db_connection()  # Get the database connection
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS iot_data (
            timestamp TIMESTAMP,
            device_id TEXT NOT NULL,
            voltage DOUBLE NOT NULL,
            current DOUBLE NOT NULL,
            device_type TEXT NOT NULL,
            location TEXT NOT NULL
        )
        """)
        logger.info("Database initialized and 'iot_data' table ensured.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")
