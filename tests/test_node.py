from unittest.mock import Mock, patch

import dateutil.parser
import pytest
import requests

import marble_client


def test_is_online(node, responses):
    responses.get(node.url)
    assert node.is_online()


def test_is_online_returns_error_status(node, responses):
    responses.get(node.url, status=500)
    assert not node.is_online()


def test_is_online_offline(node, responses):
    responses.get(node.url, body=requests.exceptions.ConnectionError())
    assert not node.is_online()


def test_id(node, registry_content):
    assert node.id in registry_content


def test_name(node, node_json):
    assert node.name == node_json["name"]


def test_description(node, node_json):
    assert node.description == node_json["description"]


def test_url(node, node_json):
    assert node.url == next(link["href"] for link in node_json["links"] if link["rel"] == "service")


def test_services_url(node, node_json):
    assert node.services_url == next(link["href"] for link in node_json["links"] if link["rel"] == "collection")


def test_version_url(node, node_json):
    assert node.version_url == next(link["href"] for link in node_json["links"] if link["rel"] == "version")


def test_date_added(node, node_json):
    assert node.date_added == dateutil.parser.isoparse(node_json["date_added"])


def test_affiliation(node, node_json):
    assert node.affiliation == node_json["affiliation"]


def test_location(node, node_json):
    assert node.location == node_json["location"]


def test_contact(node, node_json):
    assert node.contact == node_json["contact"]


def test_last_updated(node, node_json):
    assert node.last_updated == dateutil.parser.isoparse(node_json["last_updated"])


def test_version(node, node_json):
    assert node.version == node_json["version"]


def test_services(node, node_json):
    assert set(node.services) == {service_["name"] for service_ in node_json["services"]}


def test_links(node, node_json):
    assert node.links == node_json["links"]


def test_getitem(node, node_json):
    assert {node[service_["name"]].name for service_ in node_json["services"]} == {
        service_["name"] for service_ in node_json["services"]
    }


def test_getitem_no_such_service(node, node_json):
    """Test that __getitem__ raises an appropriate error if a service is not found"""
    with pytest.raises(marble_client.ServiceNotAvailableError):
        node["".join(service_["name"] for service_ in node_json["services"])]


def test_contains(node, node_json):
    assert all(service_["name"] in node for service_ in node_json["services"])


def test_not_contains(node, node_json):
    assert "".join(service_["name"] for service_ in node_json["services"]) not in node


@pytest.mark.parametrize("input_type", ["stdin", None])
@pytest.mark.parametrize("detail", ["some info here", None])
def test_login_stdin_success(input_type, detail, node, capsys, monkeypatch, responses):
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "test")
    monkeypatch.setattr("getpass.getpass", lambda *a, **kw: "testpass")
    responses.post(
        node.url.rstrip("/") + "/magpie/signin",
        json=({"detail": detail} if detail else {}),
        headers={"Set-Cookie": "cookie=test"},
    )
    if input_type is None:
        with patch("marble_client.node.check_rich_output_shell", Mock(return_value=False)):
            session = node.login(input_type=input_type)
    else:
        session = node.login(input_type=input_type)
    assert capsys.readouterr().out.strip() == (detail or "Success")
    assert session.cookies.get_dict() == {"cookie": "test"}


@pytest.mark.parametrize("input_type", ["stdin", None])
@pytest.mark.parametrize("detail", ["some info here", None])
def test_login_stdin_failure(input_type, detail, node, capsys, monkeypatch, responses):
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "test")
    monkeypatch.setattr("getpass.getpass", lambda *a, **kw: "testpass")
    responses.post(
        node.url.rstrip("/") + "/magpie/signin",
        status=401,
        json=({"detail": detail} if detail else {}),
    )
    with pytest.raises(RuntimeError) as e:
        if input_type is None:
            with patch("marble_client.node.check_rich_output_shell", Mock(return_value=False)):
                node.login(input_type=input_type)
        else:
            node.login(input_type=input_type)
    assert str(e.value) == (detail or "Unable to log in")


@pytest.mark.parametrize("input_type", ["widget", None])
def test_login_widget_display(input_type, node, capsys):
    """
    Only test for display because interaction with widgets requires a jvascript testing
    framework like galata.
    """
    if input_type is None:
        with patch("marble_client.node.check_rich_output_shell", Mock(return_value=True)):
            node.login(input_type=input_type)
    else:
        node.login(input_type=input_type)
    assert capsys.readouterr().out.startswith("VBox")
