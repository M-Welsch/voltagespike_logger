import logging

import pydmm.pydmm as pd

from common.exceptions import ExternalDeviceNotAvailableError
from common.port_identifier import identify_comport_by_name
from device.device import Device

LOG = logging.getLogger(__name__)


class Hp90Epc(Device):
    name = "hp90epc"

    def __init__(self):
        self._port = self._get_comport()
        self._responses = {"display_value": self.read_display}

    def get_settings(self) -> dict:
        return {"name": self.name}

    @staticmethod
    def _get_comport() -> str:
        comport = identify_comport_by_name("Prolific USB-to-Serial Comm Port")[0]
        if not comport:
            raise ExternalDeviceNotAvailableError("Multimeter HP-90EPC")
        return comport

    def get_response(self, response: dict) -> float:
        try:
            return self._responses[response["name"]]()
        except KeyError:
            LOG.error(f"no such response as {response} for {self.name}.")

    def read_display(self) -> float:
        try:
            res = float(pd.read_dmm(port=self._port, timeout=3))
        except ValueError as e:
            LOG.error(f"{self.name} cannot read from display: {e}")
            res = 0
        return res
