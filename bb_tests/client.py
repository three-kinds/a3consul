# -*- coding: utf-8 -*-
import logging
import time

from a3consul.scene_cases.watch_nodes import NodeThread


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="{asctime} {levelname} {process:d} [{threadName}] {name} : {message}", style="{")
    node_thread_list = list()
    for i in range(1):
        node_thread = NodeThread(
            topic="测试",
            conf={
                "init": {
                    "host": "127.0.0.1",
                    "port": 8501,
                    "scheme": "https",
                    "verify": "/data/ssl/ca.pem",
                    "cert": ('/data/ssl/client.pem', '/data/ssl/client-key.pem')
                },
                "node": {
                    "prefix": "tk",
                    "max_length": 64,
                },
                "session": {
                    "ttl": 10,
                },
                "renew": {
                    "per_request_timeout_seconds": 3,
                    "sleep_seconds": 6,
                    "timeout_seconds": 19,
                }
            },
            nodes_path='/nodes/site/aaa:',
            should_force_exit=True
        )
        node_id = node_thread.get_node_id()
        node_thread_list.append(node_thread)

    for t in node_thread_list:
        t.start()

    # # 测试不影响其它 requests
    # import requests
    # for i in range(10):
    #     client = requests.session()
    #     response = client.put('https://www.jd.com')
    #     print(len(response.text))
    #     time.sleep(3)

    for t in node_thread_list:
        t.join()
