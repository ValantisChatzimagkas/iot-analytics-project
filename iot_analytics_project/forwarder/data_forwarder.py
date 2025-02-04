import json
import time
import uuid
import asyncio
import httpx
from quixstreams import Application
from loguru import logger

#API_URL = "http://localhost:8000/data"
API_URL = "http://api:8000/data"

# Kafka configuration
BROKER_ADDRESS = "kafka1:9092,kafka2:9093,kafka3:9094"
TOPIC_NAME = "machinery-data"

# Asynchronous function to send data to the API
async def send_to_api(data,max_retries: int = 3, retry_delay=5.0):
    """
    Forward data from topic that we subscribe to the API
    :param data:
    :return:
    """
    async with httpx.AsyncClient() as client:

        retries = 0
        success = False

        while retries < max_retries and not success:
            try:
                response = await client.post(API_URL, json=data)
                response.raise_for_status()  # Raise an error for bad responses
                logger.info(f"Data sent successfully: {data}")
                success = True  # Message sent successfully
            except httpx.RequestError as ex:
                retries += 1
                if retries < max_retries:
                    logger.error(f"Exception: {ex}")
                    logger.info(f"Retrying ({retries}/{max_retries}) in {retry_delay} seconds...")
                    time.sleep(retry_delay)
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e}")

# Main async function for consuming Kafka messages
async def main():
    app = Application(broker_address=BROKER_ADDRESS,
                      loglevel="DEBUG",
                      consumer_group=str(uuid.uuid4()),
                      auto_offset_reset='earliest',
                      )

    with app.get_consumer() as consumer:
        consumer.subscribe([TOPIC_NAME])
        logger.info(f"Subscribed to Kafka topic: {TOPIC_NAME}")

        while True:
            msg = consumer.poll(timeout=1)

            if msg is None:
                logger.info("Waiting for message...")
            elif msg.error() is not None:
                logger.error(f"Error in message: {msg.error()}")
            else:
                key = msg.key().decode("utf-8")
                value = json.loads(msg.value())
                offset = msg.offset()

                logger.info(f"Received message {offset} {key}: {value}")
                consumer.store_offsets(msg)

                data = {
                    "device_id": key,
                    "device_type": value.get("device_type"),
                    "timestamp": value.get("timestamp"),
                    "current": value.get("current"),
                    "voltage": value.get("voltage"),
                    "location": value.get("location")
                }

                # Send the data asynchronously to the API
                await send_to_api(data)

# Start the async event loop
if __name__ == '__main__':
    asyncio.run(main())
