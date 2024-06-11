import os

from platformdirs import user_cache_dir

__all__ = ("NODE_REGISTRY_URL", "CACHE_FNAME")

# Marble node registry URL
NODE_REGISTRY_URL: str = os.getenv(
    "MARBLE_NODE_REGISTRY_URL",
    "https://raw.githubusercontent.com/DACCS-Climate/DACCS-node-registry/current-registry/node_registry.json",
)

_CACHE_DIR: str = os.getenv("MARBLE_CACHE_DIR", user_cache_dir("marble_client_python"))

# location to write registry cache
CACHE_FNAME: str = os.path.join(_CACHE_DIR, "registry.cached.json")
