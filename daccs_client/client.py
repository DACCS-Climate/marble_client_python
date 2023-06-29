import contextlib
import datetime
import json
import os
import os.path as osp
import shutil
import warnings
from typing import Optional

import dateutil.parser
import requests
from dotenv import load_dotenv

from daccs_client.exceptions import UnknownNodeError
from daccs_client.node import DACCSNode

load_dotenv()

CACHE = osp.join(osp.dirname(__file__), os.environ["CACHE_FNAME"])
CACHE_META = osp.join(osp.dirname(__file__), os.environ["CACHE_META_FNAME"])
REG_URL = os.environ["NODE_REGISTRY_URL"]

__all__ = ["DACCSClient"]


class DACCSClient:
    def __init__(self, fallback: Optional[bool] = True) -> None:
        """Constructor method

        :param fallback: If True, then fall back to a cached version of the registry
            if the cloud registry cannot be accessed, defaults to True
        :type fallback: Optional[bool], optional
        :raises requests.exceptions.RequestException: Raised when there is an issue
            conencting to the cloud registry and `fallback` is False
        :raises UserWarning: Raised when there is an issue conencting to the cloud registry
            and `fallback` is True
        :raise RuntimeError: If cached registry needs to be read but there is no cache
        """
        self._fallback = fallback
        self._using_fallback = False
        self._nodes: dict[str, DACCSNode] = {}

        try:
            self._registry = requests.get(REG_URL)
            self._registry.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
            if not self._fallback:
                raise
            else:
                self._using_fallback = True
                warnings.warn("Cannot retrieve cloud registry. Falling back to cached version")

        if not self._using_fallback:
            self._load_registry_from_cloud()
        else:
            self._load_registry_from_cache()

        for node, node_details in self._registry.items():
            self._nodes[node] = DACCSNode(node, node_details)

    @property
    def nodes(self):
        return self._nodes

    def __getitem__(self, node):
        try:
            return self.nodes[node]
        except KeyError:
            raise UnknownNodeError(f"No node named '{node}' in the DACCS network.") from None

    def _load_registry_from_cloud(self):
        try:
            self._registry = self._registry.json()
        except json.json.JSONDecodeError as e:
            raise RuntimeError(
                "Could not parse JSON returned from the cloud registry. "
                "Consider re-trying with 'fallback' set to True when instantiating the DACCS object."
            )
        self._save_registry_as_cache()

    def _load_registry_from_cache(self):
        try:
            with open(CACHE, "r") as f:
                self._registry = json.load(f)
        except FileNotFoundError as e:
            raise RuntimeError(f"Local registry cache not found. No file named {CACHE}.") from None

        try:
            with open(CACHE_META, "r") as f:
                data = json.load(f)
                date = dateutil.parser.isoparse(data["last_cache_date"])
        except (FileNotFoundError, ValueError) as e:
            date = "Unknown"

        print(f"Registry loaded from cache dating: {date}")

    def _save_registry_as_cache(self):
        cache_backup = CACHE + ".backup"
        cache_meta_backup = CACHE_META + ".backup"

        # Suppressing a FileNotFoundError error for the first use case where a cached registry file
        # does not exist
        with contextlib.suppress(FileNotFoundError):
            shutil.copy(CACHE, cache_backup)
            shutil.copy(CACHE_META, cache_meta_backup)

        try:
            metadata = {"last_cache_date": datetime.datetime.now(tz=datetime.timezone.utc).isoformat()}

            # Write the metadata
            with open(CACHE_META, "w") as f:
                json.dump(metadata, f)

            # write the registry
            with open(CACHE, "w") as f:
                json.dump(self._registry, f)

        except OSError as e:
            # If either the cahce file or the metadata file could not be written, then restore from backup files
            shutil.copy(cache_backup, CACHE)
            shutil.copy(cache_meta_backup, CACHE_META)

        finally:
            # Similarly, suppressing an error that I don't need to catch
            with contextlib.suppress(FileNotFoundError):
                os.remove(cache_backup)
                os.remove(cache_meta_backup)


if __name__ == "__main__":
    d = DACCSClient()
    print(d.nodes)
