from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from marble_client.node import MarbleNode

__all__ = ["MarbleService"]


class MarbleService:
    """Service offered by a Marble node."""

    def __init__(self, servicejson: dict[str, Any], node: "MarbleNode") -> None:
        """
        Initialize a marble service instance.

        :param servicejson: A JSON representing the service according to the schema defined for the Marble node registry
        :type servicejson: dict[str, Any]
        """
        self._servicedata = servicejson
        self._node = node

        self._service = None
        self._service_doc = None
        self._links = {}
        for item in servicejson["links"]:
            if item.get("rel") in ("service", "service-doc"):
                setattr(self, "_" + item["rel"].replace("-", "_"), item["href"])

    @property
    def name(self) -> str:
        """
        Name of the service.

        :return: Name of the service
        :rtype: str
        """
        return self._servicedata["name"]

    @property
    def keywords(self) -> list[str]:
        """
        Keywords associated with this service.

        :return: Keywords associated with this service
        :rtype: list[str]
        """
        return self._servicedata["keywords"]

    @property
    def description(self) -> str:
        """
        A short description of this service.

        :return: A short description of this service
        :rtype: str
        """
        return self._servicedata["description"]

    @property
    def url(self) -> str:
        """
        Access the URL for the service itself. Note: the preferred approach to access the service.

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
        """Return documentation URL."""
        return self._service_doc

    def __str__(self) -> str:
        """Return string containing name and node_id."""
        return f"<{self.__class__.__name__}(name: '{self.name}', node_id: '{self._node.id}')>"

    def __repr__(self) -> str:
        """Return service URL."""
        return self._service
