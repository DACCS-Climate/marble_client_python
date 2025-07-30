import datetime
import json
import os
import warnings

import dateutil.parser
import pytest
import requests

import marble_client


def test_load_from_remote_registry():
    """
    Test that marble_client can be initialized using a remote repository (accessed through a URL)

    Note: this test also functions as a test for the `MarbleClient.registry_uri` property
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        client = marble_client.MarbleClient()
    assert client.registry_uri == marble_client.constants.NODE_REGISTRY_URL


def test_load_from_remote_registry_update_cache(client, tmp_cache, registry_content):
    """Test that marble_client initialized using a remote repository saves the repository content to a local cache"""
    cache_file = os.path.join(tmp_cache, "registry.cached.json")
    assert os.path.isfile(cache_file)
    with open(cache_file) as f:
        content = json.load(f)
    assert content.get(client._registry_cache_key) == registry_content
    last_updated = content.get(client._registry_cache_last_updated_key)
    assert datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.isoparse(last_updated) < datetime.timedelta(
        seconds=1
    )


@pytest.mark.load_from_cache
def test_load_from_cache(tmp_cache):
    """
    Test that marble_client can be initialized using a local cache if the remote repository is not available

    Note: this test also functions as a test for the `MarbleClient.registry_uri` property
    """
    with pytest.warns(UserWarning):
        client = marble_client.MarbleClient()
    assert client.registry_uri == f"file://{os.path.join(tmp_cache, 'registry.cached.json')}"


@pytest.mark.load_from_cache
def test_load_from_cache_no_fallback():
    """
    Test that marble_client does not try to use a local cache if the remote repository is not available and
    fallback=False
    """
    with pytest.raises(RuntimeError):
        marble_client.MarbleClient(fallback=False)


def test_nodes(client, registry_content):
    """Test that `MarbleClient.nodes` returns all nodes from the repository"""
    assert client.nodes
    assert all(isinstance(n, marble_client.MarbleNode) for n in client.nodes.values())
    assert len(client.nodes) == len(registry_content)


@pytest.mark.jupyterlab_environment
def test_this_node_in_jupyter_env(client, first_url):
    """Test that `MarbleClient.this_node` returns the current node when in a jupyterlab environment"""
    node = client.this_node
    assert node.url == first_url


def test_this_node_not_in_jupyter_env(client):
    """Test that `MarbleClient.this_node` raises an error when not in a jupyterlab environment"""
    with pytest.raises(marble_client.JupyterEnvironmentError):
        client.this_node


@pytest.mark.jupyterlab_environment(jupyterhub_api_token="")
def test_this_node_in_invalid_jupyter_env(client):
    """
    Test that `MarbleClient.this_node` raises an error when in a jupyterlab environment where some environment variables
    are not defined
    """
    with pytest.raises(marble_client.JupyterEnvironmentError):
        client.this_node


@pytest.mark.jupyterlab_environment(url="http://example.com")
def test_this_node_in_unknown_node(client):
    """
    Test that `MarbleClient.this_node` raises an error when the reported jupyterlab environment URL is not found in the
    registry.
    """
    with pytest.raises(marble_client.UnknownNodeError):
        client.this_node


@pytest.mark.jupyterlab_environment(cookies={"auth_example": "cookie_example"})
def test_this_session_in_jupyter_env(client):
    """
    Test that `MarbleClient.this_session` sets the login cookies of the current user into a session object when in a
    jupyterlab environment.
    """
    session = client.this_session()
    assert session.cookies.items() == [("auth_example", "cookie_example")]


@pytest.mark.jupyterlab_environment(cookies={"auth_example": "cookie_example"})
def test_this_session_in_jupyter_env_session_exists(client):
    """
    Test that `MarbleClient.this_session` sets the login cookies of the current user into a pre-existing session object
    when in a jupyterlab environment.
    """
    session = requests.Session()
    client.this_session(session=session)
    assert session.cookies.items() == [("auth_example", "cookie_example")]


def test_this_session_not_in_jupyter_env(client):
    """Test that `MarbleClient.this_session` raises an error when not in a jupyterlab environment"""
    with pytest.raises(marble_client.JupyterEnvironmentError):
        client.this_session()


@pytest.mark.jupyterlab_environment(jupyterhub_api_token="")
def test_this_session_in_invalid_jupyter_env(client):
    """
    Test that `MarbleClient.this_session` raises an error when in a jupyterlab environment where some environment
    variables are not defined
    """
    with pytest.raises(marble_client.JupyterEnvironmentError):
        client.this_session()


@pytest.mark.jupyterlab_environment(jupyterhub_api_response_status_code=500)
def test_this_session_handles_api_error(client):
    """Test that `MarbleClient.this_session` raises an appropriate error when the JupyterHub API call fails"""
    with pytest.raises(marble_client.JupyterEnvironmentError):
        client.this_session()


def test_getitem(client, registry_content):
    """Test that __getitem__ can be used to access the nodes in the nodes list"""
    assert {client.nodes[node_id].id for node_id in registry_content} == {
        client[node_id].id for node_id in registry_content
    }


def test_getitem_no_such_node(client, registry_content):
    """Test that __getitem__ raises an appropriate error if a node is not found"""
    with pytest.raises(marble_client.UnknownNodeError):
        client["".join(registry_content)]


def test_contains(client, registry_content):
    """Test that __contains__ returns True when a node is available for the current client"""
    assert all(node_id in client for node_id in registry_content)


def test_not_contains(client, registry_content):
    """Test that __contains__ returns False when a node is not available for the current client"""
    assert "".join(registry_content) not in client
