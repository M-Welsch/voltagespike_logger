import logging
from sys import platform
from time import sleep

import serial.tools.list_ports as list_ports
from serial import Serial, SerialException

from testbench.common.exceptions import ExternalDeviceNotAvailableError
from testbench.device.device import Device
from testbench.documentation.result import Result

# import skrf as rf  # check whether this interferes with GUI again


LOG = logging.getLogger(__name__)


class TinySaNanoVnaCommons(Device):
    def __init__(self):
        self._port = self._get_comport()

    @staticmethod
    def cmd_raw(command, port) -> str:
        with Serial(port, 9600, timeout=1) as ser:
            ser.write(f"{command}\r\n".encode())
            resp = ser.read_until(b"ch>")
        return resp.decode()

    @staticmethod
    def _list_comports() -> list:
        comports = list_ports.comports()
        if platform == "linux":
            return [port.device for port in comports]
        else:
            return [port.name for port in comports]

    def _get_comport(self) -> str:
        comport = None
        device = self._get_device_identifier()
        for port in self._list_comports():
            try:
                resp = self.cmd_raw("info", port)
                if "ch>" in resp:
                    resp = self.cmd_raw("info", port)
                    if device in resp:
                        comport = port
            except SerialException as e:
                pass
        if comport is None:
            raise ExternalDeviceNotAvailableError(device)
        return comport

    def _get_device_identifier(self) -> str:
        if "NanoVna" in str(self.__class__):
            device = "NanoVNA"
        elif "TinySa" in str(self.__class__):
            device = "tinySA"
        else:
            raise RuntimeError(f"what the heck is {self.__class__}?")
        return device

    def cmd(self, command) -> list:
        resp = self.cmd_raw(command, self._port)
        return resp.split("\r\n")[1:-1]

    def get_freqs(self) -> list:
        return [float(freq) for freq in self.cmd("frequencies")]

    def set_sweep_range(self, start_hz: int, stop_hz: int):
        self.cmd(f"sweep {start_hz}Hz {stop_hz}Hz")

    def get_version(self) -> str:
        return self.cmd("version")[0]

    def device_info(self) -> dict:
        d = {}
        for index, line in enumerate(self.cmd("info")):
            d.update({f"Info {index}": line})
        return d


rbws_khz = ["auto", 3, 10, 30, 100, 300, 600]


class TinySa(TinySaNanoVnaCommons):
    name = "tinysa"

    def __init__(self):
        super().__init__()
        self._special_result: Result

    def set_special_result(self, special_result: Result, stimuli: list):
        self._special_result = special_result
        self._special_result.write_header_userdefined(stimuli[::-1] + self.get_freqs())

    def setup(self, settings: dict):
        try:
            start_freq = settings["start_freq"]
            stop_freq = settings["stop_freq"]
            self.set_sweep_range(start_freq, stop_freq)
        except KeyError:
            LOG.error("no start and stop frequency given! Using what ever is currently set in tinysa")

    def get_settings(self) -> dict:
        settings = {
            "name": "TinySA Spectrum Analyzer",
            "device ID": self.device_id(),
            "version": self.get_version(),
        }
        settings.update(self.device_info())
        return settings

    def get_response(self, response) -> list:
        return self.values()

    def save_special_result(self, addr: list):
        data_point = addr + self.values()
        self._special_result.append_row(data_point)

    def values(self) -> list:
        sleep(0.5)  # mimicks scan time. Could be calculated somehow
        return [float(value) for value in self.cmd("data 2")]

    def device_id(self) -> str:
        return self.cmd("deviceid")[0]

    def config_tinysa(self, start_hz: int, stop_hz: int, rbw="auto"):
        self.set_sweep_range(start_hz, stop_hz)
        self.set_rbw(rbw)

    def set_rbw(self, rbw):
        if rbw not in rbws_khz:
            rbw = "auto"
        self.cmd(f"rbw {rbw}")


class NanoVna(TinySaNanoVnaCommons):
    name = "nanovna"

    def __init__(self):
        super().__init__()
        self._measurements = {
            "freqs": self.get_freqs,
            "s11": self.get_s11,
            "s21": self.get_s21,
        }

    def setup(self, settings: dict):
        try:
            start_freq = settings["start_freq"]
            stop_freq = settings["stop_freq"]
            self.set_sweep_range(start_freq, stop_freq)
        except KeyError:
            LOG.error("no start and stop frequency given! Using what ever is currently set in tinysa")

    def get_settings(self) -> dict:
        settings = {
            "name": "NanoVNA Vector Network Analyzer",
            "version": self.get_version(),
        }
        settings.update(self.device_info())
        return settings

    def get_response(self, response) -> list:
        return self._measurements[response]()

    def get_s11(self) -> list:
        sleep(0.5)  # wait for a complete measurement
        return self.raw2complex(self.get_raw_data(0))

    def get_s21(self) -> list:
        sleep(0.5)  # wait for a complete measurement
        return self.raw2complex(self.get_raw_data(1))

    @staticmethod
    def raw2complex(raw: list) -> list:
        return [raw[0][i] + 1j * raw[1][i] for i in range(len(raw[0]))]

    def get_raw_data(self, slot: int) -> list:
        dat_raw = self.cmd(f"data {slot}")
        dat = []
        for col in range(len(dat_raw[0].split(" "))):
            dat.append([float(item.split(" ")[col]) for item in dat_raw])
        return dat
