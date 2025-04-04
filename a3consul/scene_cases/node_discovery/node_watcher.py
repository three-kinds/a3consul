# -*- coding: utf-8 -*-
import logging
import abc
from typing import Set

from consul import Consul


class NodeWatcher(abc.ABC):
    logger = logging.getLogger(__name__)

    def __init__(self, conf: dict):
        self._conf = conf
        self._client = Consul(**self._conf["init"])
        self._last_node_id_set: Set[str] | None = None

    @abc.abstractmethod
    def _handle_first_node_id_set(self, node_id_set: Set[str]):
        raise NotImplementedError()

    @abc.abstractmethod
    def _on_change(self, online_node_id_set: Set[str], offline_node_id_set: Set[str]):
        raise NotImplementedError()

    def _check_should_stop(self) -> bool:
        return False

    def start(self):
        self.logger.info("Starting...")

        node_path = self._conf["node_path"].lstrip("/")
        index = None
        while True:
            index, node_list = self._client.kv.get(node_path, recurse=True, index=index)
            if node_list is None:
                node_id_set = set()
            else:
                node_id_set = {node["Key"].rsplit("/", 2)[-1] for node in node_list}

            if self._last_node_id_set is None:
                self.logger.info(f"First node_id_set length: {len(node_id_set)}.")
                self._handle_first_node_id_set(node_id_set)
                self._last_node_id_set = node_id_set
                self.logger.info("Watching...")
            else:
                online_node_id_set = node_id_set - self._last_node_id_set
                offline_node_id_set = self._last_node_id_set - node_id_set
                self._last_node_id_set = node_id_set
                if len(online_node_id_set) > 0 or len(offline_node_id_set) > 0:
                    self._on_change(online_node_id_set, offline_node_id_set)
                else:
                    self.logger.debug("No change.")

            if self._check_should_stop():
                break
