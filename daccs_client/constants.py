import os
from platformdirs import user_cache_dir

__all__ = ("NODE_REGISTRY_URL", "CACHE_FNAME", "CACHE_META_FNAME")

# DACCS node registry URL
NODE_REGISTRY_URL: str = os.getenv(
    "DACCS_NODE_REGISTRY_URL",
    "https://raw.githubusercontent.com/DACCS-Climate/DACCS-node-registry/main/doc/node_registry.example.json",
)

_CACHE_DIR: str = os.getenv("DACCS_CACHE_DIR", user_cache_dir("daccs_client_python"))

# location to write registry cache
CACHE_FNAME: str = os.path.join(_CACHE_DIR, "registry.cached.json")

# location to write metadata about the registry cache
CACHE_META_FNAME: str = os.path.join(_CACHE_DIR, "cache_metadata.json")
