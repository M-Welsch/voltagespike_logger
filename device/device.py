import logging
from typing import Callable, Dict

LOG = logging.getLogger(__name__)


class Device:
    __name = "overwrite this in subclass. Shame on you if you didn't!"

    def __init__(self):
        self._stimuli: Dict[str, Callable] = {}

    @property
    def valid_measurements(self) -> list:
        return []

    def setup(self, settings: dict):
        LOG.info(f"nothing to setup for {self.__class__}")

    def set_stimulus(self, kind, val):
        try:
            self._stimuli[kind](val)
        except KeyError:
            LOG.error(f"no such stimulus as {kind} for device {self.__name}")

    def get_response(self, response):
        return 0.0

    def get_settings(self) -> dict:
        return {"name": self.__name}

    def close(self):
        LOG.info(f"nothing to close for {self.__class__}")
