class DACCSBaseError(Exception):
    pass


class ServiceNotAvailableError(DACCSBaseError):
    pass


class UnknownNodeError(DACCSBaseError):
    pass
