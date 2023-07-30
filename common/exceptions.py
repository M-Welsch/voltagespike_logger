class ExternalDeviceNotAvailableError(Exception):
    pass


class DeviceError(Exception):
    pass


class OverTemperature(Exception):
    pass


class ConfigError(Exception):
    pass


class StimulationError(Exception):
    pass


class ResponseError(Exception):
    pass


class DatabaseAdministrationError(Exception):
    pass
