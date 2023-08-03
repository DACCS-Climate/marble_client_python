import contextlib
import datetime
import json
import os
import shutil
import warnings
from typing import Optional

import dateutil.parser
import requests

from daccs_client.constants import CACHE_FNAME, CACHE_META_FNAME, NODE_REGISTRY_URL
from daccs_client.exceptions import UnknownNodeError
from daccs_client.node import DACCSNode

__all__ = ["DACCSClient"]


class DACCSClient:
    def __init__(self, fallback: Optional[bool] = True) -> None:
        """Constructor method

        :param fallback: If True, then fall back to a cached version of the registry
            if the cloud registry cannot be accessed, defaults to True
        :type fallback: Optional[bool], optional
        :raises requests.exceptions.RequestException: Raised when there is an issue
            connecting to the cloud registry and `fallback` is False
        :raises UserWarning: Raised when there is an issue connecting to the cloud registry
            and `fallback` is True
        :raise RuntimeError: If cached registry needs to be read but there is no cache
        """
        self._fallback = fallback
        self._nodes: dict[str, DACCSNode] = {}
        self._registry: dict = {}
        try:
            registry = requests.get(NODE_REGISTRY_URL)
            registry.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            if self._fallback:
                warnings.warn("Cannot retrieve cloud registry. Falling back to cached version")
                self._load_registry_from_cache()
            else:
                raise
        else:
            self._load_registry_from_cloud(registry)

        for node, node_details in self._registry.items():
            self._nodes[node] = DACCSNode(node, node_details)

    @property
    def nodes(self) -> dict[str, DACCSNode]:
        return self._nodes

    def __getitem__(self, node: str) -> DACCSNode:
        try:
            return self.nodes[node]
        except KeyError:
            raise UnknownNodeError(f"No node named '{node}' in the DACCS network.") from None

    def _load_registry_from_cloud(self, registry_response: requests.Response) -> None:
        try:
            self._registry = registry_response.json()
        except json.JSONDecodeError:
            raise RuntimeError(
                "Could not parse JSON returned from the cloud registry. "
                f"Consider re-trying with 'fallback' set to True when instantiating the {self.__class__.__name__} "
                "object."
            )
        self._save_registry_as_cache()

    def _load_registry_from_cache(self):
        try:
            with open(CACHE_FNAME, "r") as f:
                self._registry = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Local registry cache not found. No file named {CACHE_FNAME}.") from None

        try:
            with open(CACHE_META_FNAME, "r") as f:
                data = json.load(f)
                date = dateutil.parser.isoparse(data["last_cache_date"])
        except (FileNotFoundError, ValueError):
            date = "Unknown"

        print(f"Registry loaded from cache dating: {date}")

    def _save_registry_as_cache(self):
        cache_backup = CACHE_FNAME + ".backup"
        cache_meta_backup = CACHE_META_FNAME + ".backup"

        # Create cache parent directories if they don't exist
        for cache_dir in {os.path.dirname(CACHE_FNAME), os.path.dirname(CACHE_META_FNAME)}:
            os.makedirs(cache_dir, exist_ok=True)

        # Suppressing a FileNotFoundError error for the first use case where a cached registry file
        # does not exist
        with contextlib.suppress(FileNotFoundError):
            shutil.copy(CACHE_FNAME, cache_backup)
            shutil.copy(CACHE_META_FNAME, cache_meta_backup)

        try:
            metadata = {"last_cache_date": datetime.datetime.now(tz=datetime.timezone.utc).isoformat()}

            # Write the metadata
            with open(CACHE_META_FNAME, "w") as f:
                json.dump(metadata, f)

            # write the registry
            with open(CACHE_FNAME, "w") as f:
                json.dump(self._registry, f)

        except OSError as e:
            # If either the cache file or the metadata file could not be written, then restore from backup files
            shutil.copy(cache_backup, CACHE_FNAME)
            shutil.copy(cache_meta_backup, CACHE_META_FNAME)

        finally:
            # Similarly, suppressing an error that I don't need to catch
            with contextlib.suppress(FileNotFoundError):
                os.remove(cache_backup)
                os.remove(cache_meta_backup)


if __name__ == "__main__":
    d = DACCSClient()
    print(d.nodes)
