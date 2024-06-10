import importlib
import json
import os
import random
import tempfile
import warnings

import pytest
import requests

import marble_client


@pytest.fixture
def client():
    yield marble_client.MarbleClient()


@pytest.fixture(scope="session")
def registry_content():
    registry_url = marble_client.constants.NODE_REGISTRY_URL
    cache_file = marble_client.constants.CACHE_FNAME
    try:
        registry_resp = requests.get(registry_url)
        registry_resp.raise_for_status()
        content = registry_resp.json()
    except Exception as requests_err:
        warnings.warn(f"Cannot access remote registry at {registry_url}. "
                      f"Trying to load from cache file at {cache_file}.")
        try:
            with open(cache_file) as f:
                content = json.load(f)
            cache_content = content.get(marble_client.MarbleClient._registry_cache_key)
            if cache_content:
                content = cache_content
        except Exception as cache_err:
            pytest.fail(
                f"Cannot access remote registry at {registry_url} or a cached version at {cache_file}. "
                f"This test will fail.\nOriginal error messages: '{requests_err}' and '{cache_err}'"
            )
    yield content


@pytest.fixture(autouse=True)
def registry_request(request, requests_mock, registry_content, tmp_cache):
    if "load_from_cache" in request.keywords:
        requests_mock.get(marble_client.constants.NODE_REGISTRY_URL, status_code=500)
        with open(marble_client.constants.CACHE_FNAME, "w") as f:
            json.dump({
                marble_client.MarbleClient._registry_cache_key: registry_content,
                marble_client.MarbleClient._registry_cache_last_updated_key: '1900'
            }, f)
    else:
        requests_mock.get(marble_client.constants.NODE_REGISTRY_URL, json=registry_content)
    yield


@pytest.fixture(autouse=True)
def tmp_cache(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_dir:
        monkeypatch.setenv("MARBLE_CACHE_DIR", tmp_dir)
        importlib.reload(marble_client.constants)
        importlib.reload(marble_client.client)
        yield os.path.realpath(tmp_dir)


@pytest.fixture
def node(client):
    yield random.choice(list(client.nodes.values()))


@pytest.fixture
def node_json(node, registry_content):
    yield registry_content[node.id]


@pytest.fixture
def service(client):
    nodes = list(client.nodes.values())
    yield next(node_[random.choice(node_.services)] for node_ in random.sample(nodes, len(nodes)) if node_.services)


@pytest.fixture
def service_json(service, registry_content):
    yield next(service_data
               for service_data in registry_content[service._node.id]["services"]
               if service_data == service._servicedata)


@pytest.fixture
def first_url(registry_content):
    yield next(link["href"] for link in next(iter(registry_content.values()))["links"] if link["rel"] == "service")


@pytest.fixture(autouse=True)
def jupyterlab_environment(request, monkeypatch, first_url, requests_mock):
    if "jupyterlab_environment" in request.keywords:
        kwargs = request.keywords["jupyterlab_environment"].kwargs
        monkeypatch.setenv("BIRDHOUSE_HOST_URL", kwargs.get("url", first_url))

        jupyterhub_api_url = kwargs.get("jupyterhub_api_url", "http://jupyterhub.example.com")
        jupyterhub_user = kwargs.get("jupyterhub_user", "example_user")
        jupyterhub_api_token = kwargs.get("jupyterhub_api_token", "example_token")
        monkeypatch.setenv("JUPYTERHUB_API_URL", jupyterhub_api_url)
        monkeypatch.setenv("JUPYTERHUB_USER", jupyterhub_user)
        monkeypatch.setenv("JUPYTERHUB_API_TOKEN", jupyterhub_api_token)
        cookies = kwargs.get("cookies", {})
        requests_mock.get(f"{jupyterhub_api_url}/users/{jupyterhub_user}",
                          json={"auth_state": {"magpie_cookies": cookies}},
                          status_code=kwargs.get("jupyterhub_api_response_status_code", 200))
    yield
