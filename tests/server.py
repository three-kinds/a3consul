# -*- coding: utf-8 -*-
import logging
from typing import Set

from a3consul.scene_cases.watch_nodes import AbstractNodeChangeService, run_watch_nodes_server


class NodeChangeService(AbstractNodeChangeService):
    logger = logging.getLogger('server')

    def handle(self, online_node_id_set: Set[str], offline_node_id_set: Set[str]):
        self.logger.info(f'当前共{len(self.current_node_id_set)}, 新在线: {len(online_node_id_set)}，新离线: {len(offline_node_id_set)}')
        # 先处理上线的
        for online_node_id in online_node_id_set:
            self._handle_online(online_node_id)
        # 再处理掉线的
        for offline_node_id in offline_node_id_set:
            self._handle_offline(offline_node_id)

    def _handle_online(self, online_node_id: str):
        self.logger.info(f'on: {online_node_id}')

    def _handle_offline(self, offline_node_id: str):
        self.logger.info(f'off: {offline_node_id}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="{asctime} {levelname} {process:d} [{threadName}] {name} : {message}", style="{")

    logger = logging.getLogger(__name__)
    run_watch_nodes_server(
        conf={
            "init": {
                "host": "127.0.0.1",
                "port": 8501,
                "scheme": "https",
                "verify": "/data/ssl/ca.pem",
                "cert": ('/data/ssl/client.pem', '/data/ssl/client-key.pem')
            },
        },
        nodes_path='/nodes/site/',
        node_change_service=NodeChangeService(),
        logger=logger
    )
