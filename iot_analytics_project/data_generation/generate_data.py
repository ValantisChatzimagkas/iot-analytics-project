from random import choice
from quixstreams import Application
from synthetic_iot_data_generator import (Device, DeviceTypeOptions, FrequencyOptions, produce_data)


#BROKER_ADDRESS = "localhost:29093" # Localhost
BROKER_ADDRESS = "kafka1:9092,kafka2:9093,kafka3:9094"


def main():

    options = DeviceTypeOptions.list()
    locations = ["packaging", "production", "warehouse"]

    devices = [Device(device_type=choice(options),
                      location=choice(locations)) for _ in range(10)]

    app = Application(broker_address=BROKER_ADDRESS,
                      loglevel="DEBUG")

    for device in devices:
        device_data = device.create_data_records(24*7, FrequencyOptions.hour)
        produce_data(topic="machinery-data",
                     device_id=device.device_id,
                     records=device_data,
                     app=app)


if __name__ == '__main__':
    main()