# -*- coding: utf-8 -*-
from consul import Consul
from consul.std import HTTPClient  # noqa


def patch_http_client_request_with_timeout(consul: Consul, per_request_timeout_seconds: int):
    http_client: HTTPClient = consul.http
    raw_request = http_client.session.request

    def _patched_request(*args, **kwargs):
        kwargs["timeout"] = per_request_timeout_seconds
        return raw_request(*args, **kwargs)

    http_client.session.request = _patched_request
