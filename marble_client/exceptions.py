class MarbleBaseError(Exception):
    pass


class ServiceNotAvailableError(MarbleBaseError):
    pass


class UnknownNodeError(MarbleBaseError):
    pass


class JupyterEnvironmentError(MarbleBaseError):
    pass
