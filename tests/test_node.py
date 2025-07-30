import dateutil.parser
import pytest
import requests

import marble_client


def test_is_online(node, requests_mock):
    requests_mock.get(node.url)
    assert node.is_online()


def test_is_online_returns_error_status(node, requests_mock):
    requests_mock.get(node.url, status_code=500)
    assert not node.is_online()


def test_is_online_offline(node, requests_mock):
    requests_mock.get(node.url, exc=requests.exceptions.ConnectionError)
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
