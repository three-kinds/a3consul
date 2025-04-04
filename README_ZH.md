# a3consul

[English](README.md) | 简体中文

`a3consul` 对 `py-consul` 做了简单的封装，目的是用起来更简单。

## 1. 简介

* 提供`节点发现`场景的封装

## 2. 使用

### 安装

```shell
pip install a3consul

```

### 样例：节点发现

* Node

```python
from a3consul.scene_cases.node_discovery.node import Node

if __name__ == '__main__':
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
    node = Node(conf=node_conf)
    node_id = node.register_node_id()
    node.start_renew_thread()
    node.close()

```

* NodeWatcher

```python
from typing import Set
from a3consul.scene_cases.node_discovery.node_watcher import NodeWatcher


class MyNodeWatcher(NodeWatcher):
    def _on_change(self, online_node_id_set: Set[str], offline_node_id_set: Set[str]):
        # do something
        pass

    def _handle_first_node_id_set(self, node_id_set: Set[str]):
        # kick or keep them or do something else
        pass


if __name__ == '__main__':
    watcher_conf = {
        "init": {
            "host": "127.0.0.1",
            "port": 8500,
        },
        "node_path": "/nodes/",
    }
    watcher = MyNodeWatcher(conf=watcher_conf)
    watcher.start()

```
