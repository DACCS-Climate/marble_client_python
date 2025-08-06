import getpass
import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

import dateutil.parser
import requests

from marble_client.exceptions import ServiceNotAvailableError
from marble_client.services import MarbleService
from marble_client.utils import check_rich_output_shell

if TYPE_CHECKING:
    from marble_client.client import MarbleClient

__all__ = ["MarbleNode"]


class MarbleNode:
    """A node in the Marble network."""

    def __init__(self, nodeid: str, jsondata: dict[str], client: "MarbleClient") -> None:
        self._nodedata = jsondata
        self._id = nodeid
        self._name = jsondata["name"]
        self._client = client

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

    def _login(self, session: requests.Session, user_name: str | None, password: str | None) -> None:
        if user_name is None or not user_name.strip():
            raise RuntimeError("Username or email is required")
        if password is None or not password.strip():
            raise RuntimeError("Password is required")
        response = session.post(
            self.url.rstrip("/") + "/magpie/signin",
            json={"user_name": user_name, "password": password},
        )
        if response.ok:
            return response.json().get("detail", "Success")
        try:
            raise RuntimeError(response.json().get("detail", "Unable to log in"))
        except requests.exceptions.JSONDecodeError as e:
            raise RuntimeError("Unable to log in") from e

    def _widget_login(self, session: requests.Session) -> tuple[str, str]:
        import ipywidgets  # type: ignore
        from IPython.display import display  # type: ignore

        font_family = "Helvetica Neue"
        font_size = "16px"
        primary_colour = "#304FFE"
        label_style = {"font_family": font_family, "font_size": font_size, "text_color": primary_colour}
        input_style = {"description_width": "initial"}
        button_style = {
            "font_family": font_family,
            "font_size": font_size,
            "button_color": primary_colour,
            "text_color": "white",
        }
        credentials = {}

        username_label = ipywidgets.Label(value="Username or email", style=label_style)
        username_input = ipywidgets.Text(style=input_style)
        password_label = ipywidgets.Label(value="Password", style=label_style)
        password_input = ipywidgets.Password(style=input_style)
        login_button = ipywidgets.Button(description="Login", tooltip="Login", style=button_style)
        output = ipywidgets.Output()
        widgets = ipywidgets.VBox(
            [username_label, username_input, password_label, password_input, login_button, output]
        )

        def _on_username_change(change: dict) -> None:
            try:
                credentials["user_name"] = change["new"]
            except KeyError as e:
                raise Exception(str(e), change)

        username_input.observe(_on_username_change, names="value")

        def _on_password_change(change: dict) -> None:
            credentials["password"] = change["new"]

        password_input.observe(_on_password_change, names="value")

        def _on_login_click(*_) -> None:
            output.clear_output()
            with output:
                try:
                    message = self._login(session, credentials.get("user_name"), credentials.get("password"))
                except RuntimeError as e:
                    display(ipywidgets.Label(value=str(e), style={**label_style, "text_color": "red"}))
                else:
                    display(ipywidgets.Label(value=message, style={**label_style, "text_color": "green"}))

        login_button.on_click(_on_login_click)
        display(widgets)

    def _stdin_login(self, session: requests.Session) -> tuple[str, str]:
        message = self._login(session, input("Username or email: "), getpass.getpass("Password: "))
        print(message)

    def login(
        self, session: requests.Session | None = None, input_type: Literal["stdin", "widget"] | None = None
    ) -> requests.Session:
        """
        Return a requests session containing login cookies for this node.

        This will get user name and password using user input using jupyter widgets
        if available. Otherwise it will prompt the user to input details from stdin.

        If you want to force the function to use either stdin or widgets specify "stdin"
        or "widget" as the input type. Otherwise, this function will make its best guess
        which one to use.
        """
        if session is None:
            session = requests.Session()
        if input_type is None:
            input_type = "widget" if check_rich_output_shell() else "stdin"
        if input_type == "widget":
            self._widget_login(session)
        elif input_type == "stdin":
            self._stdin_login(session)
        else:
            raise TypeError("input_type must be one of 'stdin', 'widget' or None.")

        return session
