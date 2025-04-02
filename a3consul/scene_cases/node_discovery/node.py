# -*- coding: utf-8 -*-
import logging
import os
import signal
import time
import uuid
from typing import Optional
from threading import Thread

from consul import Consul

from a3consul.patch_utils import patch_http_client_request_with_timeout


class Node:
    logger = logging.getLogger(__name__)

    def __init__(self, conf: dict):
        self._conf = conf
        self._client: Optional[Consul] = None
        self._session_id: Optional[str] = None
        self._renew_thread: Optional[Thread] = None

    def register_node_id(self) -> str:
        self._client = Consul(**self._conf["init"])
        self._session_id = self._client.session.create(**self._conf["session"], behavior="delete")

        node_name = uuid.uuid4().hex
        node_path = f"{self._conf['node_path']}{node_name}"
        node_id = node_path.rsplit("/", 2)[-1]

        self._client.kv.put(key=node_path, value="", acquire=self._session_id)
        self.logger.info(f"[{self._conf['topic']}]Register node id: {node_id}.")
        return node_id

    def _renew_session(self, timeout_seconds: float) -> bool:
        assert self._client is not None
        start_tick = time.monotonic()
        while True:
            try:
                self._client.session.renew(session_id=self._session_id)
                self.logger.debug(f"[{self._conf['topic']}]Renew session success.")
                return True
            except Exception as e:
                self.logger.warning(f"[{self._conf['topic']}]Renew error: {e}.")

            # Retry once per second after an exception occurs.
            time.sleep(1)
            if time.monotonic() - start_tick > timeout_seconds:
                return False

    def _renew_thread_func(self):
        conf = self._conf["renew"]
        per_request_timeout_seconds = conf.get("per_request_timeout_seconds", None) or 2
        patch_http_client_request_with_timeout(self._client, per_request_timeout_seconds)

        while True:
            is_success = self._renew_session(timeout_seconds=conf["timeout_seconds"])
            if is_success:
                sleep_seconds = conf["sleep_seconds"]
                time.sleep(sleep_seconds)
            else:
                break

        self.logger.critical(f"[{self._conf['topic']}]Renew failed.")
        self._on_renew_failed()

    def start_renew_thread(self):
        self._renew_thread = Thread(target=self._renew_thread_func, daemon=True)
        self._renew_thread.start()

    def _on_renew_failed(self):
        self.logger.critical(f"[{self._conf['topic']}]Send SIGTERM to self...")
        os.kill(os.getpid(), signal.SIGTERM)
