from time import sleep
import paho.mqtt.client as mqtt

from device.hp90epc import Hp90Epc
from datetime import datetime


def _save_to_logfile(value: float) -> None:
    with open("logfile.log", "a") as logfile:
        ts = datetime.now().isoformat()
        logfile.write(f"{ts}, {value}")


def _mqtt_publish(client: mqtt.Client, key: str, value: float) -> None:
    client.connect("192.168.0.2")
    client.publish(topic="voltagespike_logger", payload='{{ ' + f'"{key}": {value}' + ' }}')
    client.disconnect()


def main():
    multimeter = Hp90Epc()
    client = mqtt.Client()
    client.username_pw_set("iot", "test123")

    while True:
        try:
            voltage = multimeter.read_display()
        except KeyError:
            continue
        print(f"logging voltage={voltage}")
        _save_to_logfile(voltage)
        _mqtt_publish(client, "voltage_pe_l", voltage)
        sleep(1)


if __name__ == "__main__":
    main()
