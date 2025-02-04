import json
import time

import numpy as np
import uuid
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Dict, List
from collections import namedtuple
from loguru import logger
from pandas import date_range
from quixstreams import Application


class BaseOptions(str, Enum):

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


LOW_VOLTAGE = (0, 5)  # 0 to 5V
MEDIUM_VOLTAGE = (5, 12)  # 5 to 12V
HIGH_VOLTAGE = (110, 240)  # 110 to 24

LOW_CURRENT = (0, 0.1)  # 0 to 0.1A
MEDIUM_CURRENT = (0.1, 2)  # 0.1 to 2A
HIGH_CURRENT = (2, 20)  # 2 to 20A
VERY_HIGH_CURRENT = (20, 100)  # 20 to 100A


class FrequencyOptions(BaseOptions):
    hour = "h"


class VariableOptions(BaseOptions):
    temperature = "temperature"
    humidity = "humidity"
    voltage = "voltage"
    current = "current"
    rpm = "rpm"
    speed = "speed"


class DeviceTypeOptions(BaseOptions):
    SENSOR = "Sensor"
    ACTUATOR = "Actuator"
    CONTROLLER = "Controller"
    BATTERY_POWERED = "Battery Powered"
    HIGH_POWER_DEVICE = "High Power Device"


UNITS_MAPPER = {
    VariableOptions.temperature: "Celsius",
    VariableOptions.humidity: "%",
    VariableOptions.voltage: "V",
    VariableOptions.current: "A",
    VariableOptions.rpm: "RPM",
    VariableOptions.speed: "m/s",
}

DEVICE_TYPE_VOLTAGE_AND_CURRENT_RANGES = {
    DeviceTypeOptions.SENSOR: {
        "voltage_range": LOW_VOLTAGE,
        "current_range": LOW_CURRENT,
    },
    DeviceTypeOptions.ACTUATOR: {
        "voltage_range": MEDIUM_VOLTAGE,
        "current_range": MEDIUM_CURRENT,
    },
    DeviceTypeOptions.CONTROLLER: {
        "voltage_range": MEDIUM_VOLTAGE,
        "current_range": LOW_CURRENT,
    },
    DeviceTypeOptions.BATTERY_POWERED: {
        "voltage_range": LOW_VOLTAGE,
        "current_range": MEDIUM_CURRENT,
    },
    DeviceTypeOptions.HIGH_POWER_DEVICE: {
        "voltage_range": HIGH_VOLTAGE,
        "current_range": VERY_HIGH_CURRENT,
    },
}


@dataclass
class Device:
    location: str
    device_type: str
    device_id: str = None

    def __post_init__(self):
        self.device_id = str(uuid.uuid4())

    def create_data_records(self, number_of_records: int,
                            frequency: FrequencyOptions) -> List[Dict[str, str]]:
        """
        Create data records for a given device ID.
        :param number_of_records: Number of records to generate for given device.
        :param frequency: frequency of the records, e.g. hours, days, weeks, months, etc.
        :return: A list of data records, each containing a timestamp and device data.
        """

        voltage_range, current_range = DEVICE_TYPE_VOLTAGE_AND_CURRENT_RANGES[self.device_type].values()

        voltage_data = np.random.uniform(low=voltage_range[0], high=voltage_range[1], size=number_of_records).tolist()
        current_data = np.random.uniform(low=current_range[0], high=current_range[1], size=number_of_records).tolist()

        # Define the record structure
        Record = namedtuple("DeviceDataRecord", ["timestamp", "voltage",
                                                 "current", "device_type", "location"])

        # Generate timestamps
        timestamps = [
            ts.strftime("%Y-%m-%d %H:%M:%S")
            for ts in date_range(start=datetime.now(), periods=number_of_records, freq=frequency)
        ]

        records = [
            Record(
                timestamps[i], voltage_data[i], current_data[i], self.device_type, self.location
            )._asdict()
            for i in range(number_of_records)]

        return records


# def produce_data(topic: str,
#                  device_id: str,
#                  records: List[Dict[str, str]],
#                  app: Application):
#     """
#     Produce data records for a given topic to kafka topic.
#     :param topic: Kafka topic to push data.
#     :param device_id: ID of the device associated with the records.
#     :param records: List of data records of data for given device.
#     :param app: a quixstreams Application object needed to get a kafka application up.
#     :return:
#     """
#
#     with app.get_producer() as producer:
#         for record in records:
#             logger.debug(f"Got record:\n\t{record}")
#
#             producer.produce(
#                 topic=topic,
#                 key=str(device_id),
#                 value=json.dumps(record),
#             )
#
#             logger.info(f"Payload sent to topic: {topic}")

def produce_data(topic: str,
                 device_id: str,
                 records: List[Dict[str, str]],
                 app: Application,
                 max_retries: int = 3,
                 retry_delay: float = 5.0):
    """
    Produce data records for a given topic to Kafka topic with retry logic.
    :param topic: Kafka topic to push data.
    :param device_id: ID of the device associated with the records.
    :param records: List of data records of data for given device.
    :param app: a quixstreams Application object needed to get a kafka application up.
    :param max_retries: Maximum number of retry attempts for failed messages.
    :param retry_delay: Delay (in seconds) between retries.
    :return:
    """

    with app.get_producer() as producer:
        for record in records:
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    logger.debug(f"Got record:\n\t{record}")

                    producer.produce(
                        topic=topic,
                        key=str(device_id),
                        value=json.dumps(record),
                    )

                    logger.info(f"Payload sent to topic: {topic}")
                    success = True  # Message sent successfully

                except Exception as e:
                    retries += 1
                    logger.error(f"Error sending record to topic '{topic}': {e}")

                    if retries < max_retries:
                        logger.info(f"Retrying ({retries}/{max_retries}) in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Max retries reached. Failed to send record: {record}")