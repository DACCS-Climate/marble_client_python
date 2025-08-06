import os
from functools import cache, wraps
from typing import Any, Callable

from marble_client.exceptions import JupyterEnvironmentError


@cache
def check_rich_output_shell() -> bool:
    """Return True iff running in an ipython compatible environment that can display rich outputs like widgets."""
    try:
        from IPython import get_ipython  # type: ignore

        ipython_class = get_ipython().__class__
    except (ImportError, NameError):
        return False
    else:
        full_path = f"{ipython_class.__module__}.{ipython_class.__qualname__}"
        return full_path in {
            "ipykernel.zmqshell.ZMQInteractiveShell",
            "google.colab._shell.Shell",
        }  # TODO: add more shells as needed


def check_jupyterlab(f: Callable) -> Callable:
    """
    Raise an error if not running in a Jupyterlab instance.

    Wraps the function f by first checking if the current script is running in a
    Marble Jupyterlab environment and raising a JupyterEnvironmentError if not.

    This is used as a pre-check for functions that only work in a Marble Jupyterlab
    environment.

    Note that this checks if either the BIRDHOUSE_HOST_URL or PAVICS_HOST_URL are present to support
    versions of birdhouse-deploy prior to 2.4.0.
    """

    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        birdhouse_host_var = ("PAVICS_HOST_URL", "BIRDHOUSE_HOST_URL")
        jupyterhub_env_vars = ("JUPYTERHUB_API_URL", "JUPYTERHUB_USER", "JUPYTERHUB_API_TOKEN")
        if any(os.getenv(var) for var in birdhouse_host_var) and all(os.getenv(var) for var in jupyterhub_env_vars):
            return f(*args, **kwargs)
        raise JupyterEnvironmentError("Not in a Marble jupyterlab environment")

    return wrapper
