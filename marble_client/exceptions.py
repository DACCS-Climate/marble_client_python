class MarbleBaseError(Exception):
    """Base Error for all exceptions for this package."""


class ServiceNotAvailableError(MarbleBaseError):
    """Indicates that a given service is not available."""


class UnknownNodeError(MarbleBaseError):
    """Indicates that the given node cannot be found."""


class JupyterEnvironmentError(MarbleBaseError):
    """Indicates that there is an issue detecting features only available in Jupyterlab."""
