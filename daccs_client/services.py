from typing import Any

__all__ = ["DACCSService"]


class DACCSService:
    def __init__(self, servicejson: dict[str, Any]) -> None:
        """Constructor method

        :param servicejson: A JSON representing the service according to the schema defined for the DACCS node registry
        :type servicejson: dict[str, Any]
        """
        self._name = servicejson["name"]
        self._keywords = servicejson["keywords"]
        self._description = servicejson["description"]

        self._service = None
        self._service_doc = None
        self._service_desc = None
        self._conformance = None

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
    def conformance(self) -> str:
        """Access the URL that defines the conformances of this service

        :return: Link to conformance page
        :rtype: str
        """
        return self._conformance

    @property
    def service_url(self) -> str:
        """Access the URL for the service itself. Note: the preferred approach to access the service
        URL is via just using the name of the DACCSService object.

        E.g.::

            s = DACCSService(jsondata)
            s  # this prints http://url-of-service

        :return: Service URL
        :rtype: str
        """
        return self._service

    @property
    def service_doc_url(self) -> str:
        return self._service_doc

    @property
    def service_desc_url(self) -> str:
        return self._service_desc

    def __str__(self) -> str:
        s = f"DACCS service: {self.name}\n"
        return s

    def __repr__(self) -> str:
        return self._service
