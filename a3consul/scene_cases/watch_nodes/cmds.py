# -*- coding: utf-8 -*-
import logging
from consul import Consul

from .abstract_node_change_service import AbstractNodeChangeService


def run_watch_nodes_server(conf: dict, nodes_path: str, node_change_service: AbstractNodeChangeService, logger: logging.Logger):
    client = Consul(**conf['init'])
    nodes_path = nodes_path.lstrip("/")

    index = None
    logger.info(f"开启观察...")
    while True:
        index, node_list = client.kv.get(nodes_path, recurse=True, index=index)
        if node_list is None:
            node_change_service.on_change(set())
        else:
            node_id_set = {node["Key"].rsplit("/", 2)[-1] for node in node_list}
            node_change_service.on_change(node_id_set)
