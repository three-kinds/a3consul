# -*- coding: utf-8 -*-
import signal
from typing import Set
from unittest import TestCase, mock
from threading import Thread
from consul.api.session import Session
from consul.api.kv import KV

from a3consul.scene_cases.node_discovery.node import Node
from a3consul.scene_cases.node_discovery.node_watcher import NodeWatcher as BaseNodeWatcher


class NodeWatcher(BaseNodeWatcher):
    def __init__(self, conf: dict):
        super().__init__(conf=conf)
        self.first_node_id_set: Set[str] | None = None
        self.online_node_id_set: Set[str] | None = None
        self.offline_node_id_set: Set[str] | None = None

    def _handle_first_node_id_set(self, node_id_set: Set[str]):
        self.first_node_id_set = node_id_set

    def _on_change(self, online_node_id_set: Set[str], offline_node_id_set: Set[str]):
        self.online_node_id_set = online_node_id_set
        self.offline_node_id_set = offline_node_id_set


_count = 0


def _return_true_after_one_call() -> bool:
    global _count
    _count += 1
    if _count == 1:
        return False
    return True


class TestNodeDiscovery(TestCase):
    def test_node_renew_failed(self):
        p1 = mock.patch.object(Session, "create", return_value="123")
        p1.start()
        self.addCleanup(p1.stop)
        p2 = mock.patch.object(Session, "renew", side_effect=Exception("renew failed"))
        p2.start()
        self.addCleanup(p2.stop)
        p3 = mock.patch.object(KV, "put", return_value=None)
        p3.start()
        self.addCleanup(p3.stop)

        received_signal = False

        def signal_handler(signum, frame):
            nonlocal received_signal
            received_signal = True

        signal.signal(signal.SIGTERM, signal_handler)

        node_conf = {
            "topic": "unittest",
            "node_path": "/nodes/",
            "init": {
                "host": "127.0.0.1",
                "port": 8600,
            },
            "session": {
                "ttl": 10,
            },
            "renew": {
                "sleep_seconds": 1,
                "timeout_seconds": 1,
            },
        }
        node = Node(conf=node_conf)
        node.register_node_id()
        renew_thread = node.start_renew_thread()

        renew_thread.join(timeout=2)
        self.assertEqual(received_signal, True)
        self.assertEqual(renew_thread.is_alive(), False)

    def test_the_entire_process(self):
        watcher_conf = {
            "init": {
                "host": "127.0.0.1",
                "port": 8500,
            },
            "node_path": "/nodes/",
        }
        node_conf = {
            "topic": "unittest",
            "node_path": "/nodes/",
            "init": {
                "host": "127.0.0.1",
                "port": 8500,
            },
            "session": {
                "ttl": 10,
            },
            "renew": {
                "sleep_seconds": 5,
                "timeout_seconds": 20,
            },
        }

        node_watcher = NodeWatcher(conf=watcher_conf)
        node_watcher.set_should_stop(True)

        watcher_thread = Thread(target=node_watcher.start, daemon=True)
        watcher_thread.start()
        watcher_thread.join(timeout=2)

        self.assertEqual(len(node_watcher.first_node_id_set), 0)
        self.assertEqual(node_watcher.online_node_id_set, None)
        self.assertEqual(node_watcher.offline_node_id_set, None)
        self.assertEqual(watcher_thread.is_alive(), False)
        # Start the watcher for the second time.
        node1 = Node(conf=node_conf)
        node1_id = node1.register_node_id()
        node1.start_renew_thread()

        node_watcher = NodeWatcher(conf=watcher_conf)
        node_watcher._check_should_stop = _return_true_after_one_call
        watcher_thread = Thread(target=node_watcher.start, daemon=True)
        watcher_thread.start()
        watcher_thread.join(timeout=2)

        node2 = Node(conf=node_conf)
        node2_id = node2.register_node_id()
        renew_thread2 = node2.start_renew_thread()
        renew_thread2.join(timeout=2)

        self.assertEqual(node_watcher.first_node_id_set, {node1_id})
        self.assertEqual(node_watcher.online_node_id_set, {node2_id})
        self.assertEqual(len(node_watcher.offline_node_id_set), 0)
        self.assertEqual(watcher_thread.is_alive(), False)
        node1.close()
        node2.close()
