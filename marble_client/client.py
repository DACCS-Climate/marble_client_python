import datetime
import json
import os
import shutil
import warnings
from functools import cache, wraps
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import dateutil.parser
import requests

from marble_client.constants import CACHE_FNAME, NODE_REGISTRY_URL
from marble_client.exceptions import JupyterEnvironmentError, UnknownNodeError
from marble_client.node import MarbleNode

__all__ = ["MarbleClient"]


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


class MarbleClient:
    """Client object representing the information in the Marble registry."""

    _registry_cache_key = "marble_client_python:cached_registry"
    _registry_cache_last_updated_key = "marble_client_python:last_updated"

    def __init__(self, fallback: bool = True) -> None:
        """
        Initialize a MarbleClient instance.

        :param fallback: If True, then fall back to a cached version of the registry
            if the cloud registry cannot be accessed, defaults to True
        :type fallback: bool
        :raises requests.exceptions.RequestException: Raised when there is an issue
            connecting to the cloud registry and `fallback` is False
        :raises UserWarning: Raised when there is an issue connecting to the cloud registry
            and `fallback` is True
        :raise RuntimeError: If cached registry needs to be read but there is no cache
        """
        self._nodes: dict[str, MarbleNode] = {}
        self._registry_uri: str
        self._registry: dict
        self._registry_uri, self._registry = self._load_registry(fallback)

        for node_id, node_details in self._registry.items():
            self._nodes[node_id] = MarbleNode(node_id, node_details)

    @property
    def nodes(self) -> dict[str, MarbleNode]:
        """Return nodes in the current registry."""
        return self._nodes

    @property
    @cache
    @check_jupyterlab
    def this_node(self) -> MarbleNode:
        """
        Return the node where this script is currently running.

        Note that this function only works in a Marble Jupyterlab environment.
        """
        # PAVICS_HOST_URL is the deprecated variable used in older versions (<2.4.0) of birdhouse-deploy
        url_string = os.getenv("BIRDHOUSE_HOST_URL", os.getenv("PAVICS_HOST_URL"))
        host_url = urlparse(url_string)
        for node in self.nodes.values():
            if urlparse(node.url).hostname == host_url.hostname:
                return node
        raise UnknownNodeError(f"No node found in the registry with the url '{url_string}'")

    @check_jupyterlab
    def this_session(self, session: Optional[requests.Session] = None) -> requests.Session:
        """
        Add the login session cookies of the user who is currently logged in to the session object.

        If a session object is not passed as an argument to this function, create a new session
        object as well.

        Note that this function only works in a Marble Jupyterlab environment.
        """
        if session is None:
            session = requests.Session()
        r = requests.get(
            f"{os.getenv('JUPYTERHUB_API_URL')}/users/{os.getenv('JUPYTERHUB_USER')}",
            headers={"Authorization": f"token {os.getenv('JUPYTERHUB_API_TOKEN')}"},
        )
        try:
            r.raise_for_status()
        except requests.HTTPError as err:
            raise JupyterEnvironmentError("Cannot retrieve login cookies through the JupyterHub API.") from err
        for name, value in r.json().get("auth_state", {}).get("magpie_cookies", {}).items():
            session.cookies.set(name, value)
        return session

    @property
    def registry_uri(self) -> str:
        """Return the URL of the currently used Marble registry."""
        return self._registry_uri

    def __getitem__(self, node: str) -> MarbleNode:
        """Return the node with the given name."""
        try:
            return self.nodes[node]
        except KeyError as err:
            raise UnknownNodeError(f"No node named '{node}' in the Marble network.") from err

    def __contains__(self, node: str) -> bool:
        """
        Check if a node is available.

        :param node: ID of the Marble node
        :type node: str
        :return: True if the node is present in the registry, False otherwise
        :rtype: bool
        """
        return node in self.nodes

    def _load_registry(self, fallback: bool = True) -> tuple[str, dict[str, Any]]:
        try:
            registry_response = requests.get(NODE_REGISTRY_URL)
            registry_response.raise_for_status()
            registry = registry_response.json()
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as err:
            error = err
            error_msg = f"Cannot retrieve registry from {NODE_REGISTRY_URL}."
        except json.JSONDecodeError as err:
            error = err
            error_msg = f"Could not parse JSON returned from the registry at {NODE_REGISTRY_URL}"
        else:
            self._save_registry_as_cache(registry)
            return NODE_REGISTRY_URL, registry

        if fallback:
            warnings.warn(f"{error_msg} Falling back to cached version")
            return f"file://{os.path.realpath(CACHE_FNAME)}", self._load_registry_from_cache()
        else:
            raise RuntimeError(error_msg) from error

    def _load_registry_from_cache(self) -> dict[str, Any]:
        try:
            with open(CACHE_FNAME) as f:
                cached_registry = json.load(f)
        except FileNotFoundError as err:
            raise RuntimeError(f"Local registry cache not found. No file named {CACHE_FNAME}.") from err
        except json.JSONDecodeError as err:
            raise RuntimeError(f"Could not parse JSON returned from the cached registry at {CACHE_FNAME}") from err
        else:
            if self._registry_cache_key in cached_registry:
                registry = cached_registry[self._registry_cache_key]
                date = dateutil.parser.isoparse(cached_registry[self._registry_cache_last_updated_key])
            else:
                # registry is cached in old format, re-cache it in the newer format
                registry = cached_registry
                self._save_registry_as_cache(registry)
                date = "Unknown"
            print(f"Registry loaded from cache dating: {date}")
            return registry

    def _save_registry_as_cache(self, registry: dict[str, Any]) -> None:
        cache_backup = CACHE_FNAME + ".backup"

        # Create cache parent directories if they don't exist
        os.makedirs(os.path.dirname(CACHE_FNAME), exist_ok=True)
        if os.path.isfile(CACHE_FNAME):
            shutil.copy(CACHE_FNAME, cache_backup)

        try:
            with open(CACHE_FNAME, "w") as f:
                data = {
                    self._registry_cache_key: registry,
                    self._registry_cache_last_updated_key: datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                }
                json.dump(data, f)
        except OSError:
            # If the cache file cannot be written, then restore from backup files
            shutil.copy(cache_backup, CACHE_FNAME)
        finally:
            if os.path.isfile(cache_backup):
                os.remove(cache_backup)


if __name__ == "__main__":
    d = MarbleClient()
    print(d.nodes)
