import warnings
from datetime import datetime
from typing import Optional

import dateutil.parser
import requests

from marble_client.exceptions import ServiceNotAvailableError
from marble_client.services import MarbleService

__all__ = ["MarbleNode"]


class MarbleNode:
    """A node in the Marble network."""

    def __init__(self, nodeid: str, jsondata: dict[str]) -> None:
        self._nodedata = jsondata
        self._id = nodeid
        self._name = jsondata["name"]

        self._links_service = None
        self._links_collection = None
        self._links_version = None

        for item in jsondata["links"]:
            if item.get("rel") in ("service", "collection", "version"):
                setattr(self, "_links_" + item["rel"], item["href"])

        self._services: dict[str, MarbleService] = {}

        for service in jsondata.get("services", []):
            s = MarbleService(service, self)
            if not getattr(self, s.name, False):
                setattr(self, s.name, s)
            self._services[s.name] = s

    def is_online(self) -> bool:
        """Return True iff the node is currently online."""
        try:
            registry = requests.get(self.url)
            registry.raise_for_status()
            return True
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            return False

    @property
    def id(self) -> str:
        """Return the unique id for this node in the Marble network."""
        return self._id

    @property
    def name(self) -> str:
        """
        Return the name of the node.

        Note that this is not guarenteed to be unique (like the id) but represents
        how the node is often referred to in other documentation.
        """
        return self._name

    @property
    def description(self) -> str:
        """Return a description of the node."""
        return self._nodedata["description"]

    @property
    def url(self) -> Optional[str]:
        """Return the root URL of the node."""
        return self._links_service

    @property
    def collection_url(self) -> Optional[str]:
        """Return a URL to the node's services endpoint."""
        warnings.warn("collection_url has been renamed to services_url", DeprecationWarning, 2)
        return self._links_collection

    @property
    def services_url(self) -> Optional[str]:
        """Return a URL to the node's services endpoint."""
        return self._links_collection

    @property
    def version_url(self) -> Optional[str]:
        """Return a URL to the node's version endpoint."""
        return self._links_version

    @property
    def date_added(self) -> datetime:
        """Return datetime representing when the node was added to the Marble network."""
        return dateutil.parser.isoparse(self._nodedata["date_added"])

    @property
    def affiliation(self) -> str:
        """Return affiliation information for the node."""
        return self._nodedata["affiliation"]

    @property
    def location(self) -> dict[str, float]:
        """Return the geographical location of the node."""
        return self._nodedata["location"]

    @property
    def contact(self) -> str:
        """Return contact information for the node."""
        return self._nodedata["contact"]

    @property
    def last_updated(self) -> datetime:
        """Return datetime representing the last time the node's metadata was updated."""
        return dateutil.parser.isoparse(self._nodedata["last_updated"])

    @property
    def marble_version(self) -> str:
        """Return node version."""
        warnings.warn("marble_version has been renamed to version", DeprecationWarning, 2)
        return self._nodedata["version"]

    @property
    def version(self) -> str:
        """Return node version."""
        return self._nodedata["version"]

    @property
    def services(self) -> list[str]:
        """Return node services."""
        return list(self._services)

    @property
    def links(self) -> list[dict[str, str]]:
        """Return node links."""
        return self._nodedata["links"]

    def __getitem__(self, service: str) -> MarbleService:
        """Get a service at a node by specifying its name.

        :param service: Name of the Marble service
        :type service: str
        :raises ServiceNotAvailable: This exception is raised if the service is not available at the node
        :return: _description_
        :rtype: MarbleService
        """
        try:
            return self._services[service]
        except KeyError as e:
            raise ServiceNotAvailableError(f"A service named '{service}' is not available on this node.") from e

    def __contains__(self, service: str) -> bool:
        """
        Check if a service is available at a node.

        :param service: Name of the Marble service
        :type service: str
        :return: True if the service is available, False otherwise
        :rtype: bool
        """
        return service in self._services

    def __repr__(self) -> str:
        """Return a repr containing id and name."""
        return f"<{self.__class__.__name__}(id: '{self.id}', name: '{self.name}')>"
