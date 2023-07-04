from datetime import datetime

import dateutil.parser

from daccs_client.exceptions import ServiceNotAvailableError
from daccs_client.services import DACCSService

__all__ = ["DACCSNode"]


class DACCSNode:
    def __init__(self, nodename: str, jsondata: dict[str]) -> None:
        self._name = nodename
        self._url = jsondata["url"]
        self._date_added = dateutil.parser.isoparse(jsondata["date_added"])
        self._affiliation = jsondata["affiliation"]
        self._icon_url = jsondata["icon_url"]
        self._location = jsondata["location"]
        self._contact = jsondata["contact"]
        self._last_updated = dateutil.parser.isoparse(jsondata["last_updated"])
        self._daccs_version = jsondata["version"]
        self._status = jsondata["status"]

        self._services: list[str] = []

        for service in jsondata["services"]:
            s = DACCSService(service)
            setattr(self, s.name, s)
            self._services.append(s.name)

    def is_online(self) -> bool:
        return self._status == "online"

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def date_added(self) -> datetime:
        return self._date_added

    @property
    def affiliation(self) -> str:
        return self._affiliation

    @property
    def icon_url(self) -> str:
        return self._icon_url

    @property
    def location(self) -> dict[str, float]:
        return self._location

    @property
    def contact(self) -> str:
        return self._contact

    @property
    def last_updated(self) -> datetime:
        return self._last_updated

    @property
    def daccs_version(self) -> str:
        return self._daccs_version

    @property
    def status(self) -> str:
        return self._status

    @property
    def services(self) -> list[str]:
        return self._services

    def __getitem__(self, service: str) -> DACCSService:
        """Get a service at a node by specifying its name.

        :param service: Name of the DACCS service
        :type service: str
        :raises ServiceNotAvailable: This exception is raised if the service is not available at the node
        :return: _description_
        :rtype: DACCSservice
        """
        try:
            s = getattr(self, service)
            return s
        except AttributeError:
            raise ServiceNotAvailableError() from None

    def __contains__(self, service: str) -> bool:
        """Check if a service is available at a node

        :param service: Name of the DACCS service
        :type service: str
        :return: True if the service is available, False otherwise
        :rtype: bool
        """
        return service in self._services
