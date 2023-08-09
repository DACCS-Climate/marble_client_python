from typing import Any

__all__ = ["MarbleService"]


class MarbleService:
    def __init__(self, servicejson: dict[str, Any]) -> None:
        """Constructor method

        :param servicejson: A JSON representing the service according to the schema defined for the Marble node registry
        :type servicejson: dict[str, Any]
        """
        self._name = servicejson["name"]
        self._keywords = servicejson["keywords"]
        self._description = servicejson["description"]

        self._service = None
        self._service_doc = None

        for item in servicejson["links"]:
            setattr(self, "_" + item["rel"].replace("-", "_"), item["href"])

    @property
    def name(self) -> str:
        """Name of the service

        :return: Name of the service
        :rtype: str
        """
        return self._name

    @property
    def keywords(self) -> list[str]:
        """Keywords associated with this service

        :return: Keywords associated with this service
        :rtype: list[str]
        """
        return self._keywords

    @property
    def description(self) -> str:
        """A short description of this service

        :return: A short description of this service
        :rtype: str
        """
        return self._description

    @property
    def url(self) -> str:
        """Access the URL for the service itself. Note: the preferred approach to access the service
        URL is via just using the name of the MarbleService object.

        E.g.::

            s = MarbleService(jsondata)
            s  # this prints http://url-of-service

        :return: Service URL
        :rtype: str
        """
        return self._service

    @property
    def doc_url(self) -> str:
        return self._service_doc

    def __str__(self) -> str:
        return f"Marble service: {self.name}\n"

    def __repr__(self) -> str:
        return self._service
