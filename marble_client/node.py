import json
from datetime import datetime

import dateutil.parser
import requests

from marble_client.exceptions import ServiceNotAvailableError
from marble_client.services import MarbleService

__all__ = ["MarbleNode"]


class MarbleNode:
    def __init__(self, nodename: str, jsondata: dict[str]) -> None:
        self._nodedata = jsondata
        self._name = nodename

        for item in jsondata["links"]:
            setattr(self, "_links_" + item["rel"].replace("-", "_"), item["href"])

        self._services: list[str] = []

        if jsondata["status"] != "offline":
            for service in jsondata["services"]:
                s = MarbleService(service)
                setattr(self, s.name, s)
                self._services.append(s.name)

    def is_online(self) -> bool:
        try:
            registry = requests.get(self.url)
            registry.raise_for_status()
            return True
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            return False

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._nodedata["description"]

    @property
    def url(self) -> str:
        return self._links_service

    @property
    def collection_url(self) -> str:
        return self._links_collection

    @property
    def version_url(self) -> str:
        return self._links_version

    @property
    def date_added(self) -> datetime:
        return dateutil.parser.isoparse(self._nodedata["date_added"])

    @property
    def affiliation(self) -> str:
        return self._nodedata["affiliation"]

    @property
    def location(self) -> dict[str, float]:
        return self._nodedata["location"]

    @property
    def contact(self) -> str:
        return self._nodedata["contact"]

    @property
    def last_updated(self) -> datetime:
        return dateutil.parser.isoparse(self._nodedata["last_updated"])

    @property
    def marble_version(self) -> str:
        return self._nodedata["version"]

    @property
    def services(self) -> list[str]:
        return self._services

    def __getitem__(self, service: str) -> MarbleService:
        """Get a service at a node by specifying its name.

        :param service: Name of the Marble service
        :type service: str
        :raises ServiceNotAvailable: This exception is raised if the service is not available at the node
        :return: _description_
        :rtype: Marbleservice
        """
        try:
            s = getattr(self, service)
            return s
        except AttributeError:
            raise ServiceNotAvailableError() from None

    def __contains__(self, service: str) -> bool:
        """Check if a service is available at a node

        :param service: Name of the Marble service
        :type service: str
        :return: True if the service is available, False otherwise
        :rtype: bool
        """
        return service in self._services
