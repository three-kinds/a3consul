# -*- coding: utf-8 -*-
import logging
import time
import uuid
from typing import Optional
from a3py.simplified.concurrence import force_exit_from_threads
from threading import Thread
from consul import Consul


class NodeThread(Thread):
    logger = logging.getLogger(__name__)

    def __init__(self, topic: str, conf: dict, nodes_path: str, should_force_exit: bool, *args, **kwargs):
        self._topic = topic
        self._conf = conf
        self._nodes_path = nodes_path.lstrip("/")
        self._should_force_exit = should_force_exit
        self._client: Optional[Consul] = None
        self._session_id: Optional[str] = None
        # 配置为守护线程
        super().__init__(daemon=True, *args, **kwargs)

    def get_node_id(self) -> str:
        self._client = Consul(**self._conf['init'])
        self._session_id = self._client.session.create(**self._conf['session'], behavior='delete')

        nodes_path = f'{self._nodes_path}{uuid.uuid4().hex}'
        node_id = nodes_path.rsplit('/', 2)[-1]

        self._client.kv.put(key=nodes_path, value='', acquire=self._session_id)
        self.logger.info(f'[{self._topic}]获得节点id: {node_id}')
        return node_id

    def _renew_session(self, timeout_seconds: float) -> bool:
        start_tick = time.time()
        while True:
            try:
                self._client.session.renew(session_id=self._session_id)
                self.logger.debug(f'[{self._topic}]renew成功')
                return True
            except Exception as e:
                self.logger.debug(f'[{self._topic}]renew出现异常: {e}')

            # 出现异常后，每秒重试一次
            time.sleep(1)
            if time.time() - start_tick > timeout_seconds:
                return False

    def force_exit(self):
        force_exit_from_threads(f'[{self._topic}]因与服务端断开连接，所以整个进程退出')

    def run(self):
        conf = self._conf['renew']
        while True:
            is_success = self._renew_session(timeout_seconds=conf['timeout_seconds'])
            if is_success:
                sleep_seconds = conf['sleep_seconds']
                time.sleep(sleep_seconds)
            else:
                break

        if self._should_force_exit:
            self.force_exit()