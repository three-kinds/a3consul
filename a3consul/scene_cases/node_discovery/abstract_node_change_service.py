# -*- coding: utf-8 -*-
import abc
import sys
import logging
from typing import Set


class AbstractNodeChangeService(abc.ABC):
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.current_node_id_set: Set | None = None

    def on_change(self, current_node_id_set: Set[str]):
        if self.current_node_id_set is None:
            self.current_node_id_set = current_node_id_set
            if len(current_node_id_set) > 0:
                self.logger.critical(f"服务端启动时，节点列表却不为空，无法继续")
                sys.exit(-1)
            return

        last_node_id_set = self.current_node_id_set

        online_node_id_set = current_node_id_set - last_node_id_set
        offline_node_id_set = last_node_id_set - current_node_id_set
        self.current_node_id_set = current_node_id_set
        if len(online_node_id_set) > 0 or len(offline_node_id_set) > 0:
            self.handle(online_node_id_set, offline_node_id_set)
        else:
            self.logger.debug(f'调过空转')

    @abc.abstractmethod
    def handle(self, online_node_id_set: Set[str], offline_node_id_set: Set[str]):
        raise NotImplementedError()
