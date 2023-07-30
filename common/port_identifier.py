from pathlib import Path
from sys import platform

if platform != "linux":
    import serial.tools.list_ports as list_ports

import logging

import pyvisa as visa

LOG = logging.getLogger(__name__)


def list_serial_ports() -> list:
    if platform == "linux":
        return [str(item) for item in list(Path("/dev").glob("ttyUSB*"))]
    else:
        return [port.name for port in list_ports.comports()]


def identify_comport_by_name(device_name: str) -> list:
    if platform == "linux":
        return list_serial_ports()
    else:
        return [port.name for port in list_serial_ports() if device_name in str(port)]


def identify_visa_device_by_name(device_name: str, res_manager: visa.highlevel.ResourceManager):
    visa_device = None
    for re in res_manager.list_resources():
        LOG.debug(f"challanging {re}")
        try:
            potential_visa_device: visa.resources.serial.SerialInstrument = res_manager.open_resource(re)
            potential_visa_device.timeout = 100
            idn = potential_visa_device.query("*IDN?")
            if device_name in idn:
                visa_device = potential_visa_device
                visa_device.timeout = 5000  # 5 seconds
                LOG.info(f"found visa device {device_name}!")
                break
        except Exception as e:
            LOG.debug(f"resouce {re} could not be opened! {e}")
    return visa_device


if __name__ == "__main__":
    comport = identify_comport_by_name("Prolific USB-to-Serial Comm Port")[0]
    print(comport)
