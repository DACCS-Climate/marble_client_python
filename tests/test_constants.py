import importlib
import os

import marble_client.constants


def test_node_registry_url_default():
    importlib.reload(marble_client.constants)
    assert (
        marble_client.constants.NODE_REGISTRY_URL
        == "https://raw.githubusercontent.com/DACCS-Climate/DACCS-node-registry/current-registry/node_registry.json"
    )


def test_node_registry_url_settable(monkeypatch):
    other_value = "other_value"
    monkeypatch.setenv("MARBLE_NODE_REGISTRY_URL", other_value)
    importlib.reload(marble_client.constants)
    assert marble_client.constants.NODE_REGISTRY_URL == other_value


def test_cache_fname_default(tmp_cache):
    importlib.reload(marble_client.constants)
    assert os.path.realpath(marble_client.constants.CACHE_FNAME) == os.path.join(tmp_cache, "registry.cached.json")


def test_cache_fname_settable(monkeypatch):
    other_value = "other_value"
    monkeypatch.setenv("MARBLE_CACHE_DIR", other_value)
    importlib.reload(marble_client.constants)
    assert marble_client.constants.CACHE_FNAME == os.path.join(other_value, "registry.cached.json")
