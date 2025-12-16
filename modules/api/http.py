#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTTP helpers for external API calls."""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional

import requests


DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": "SV/1.0 (local)",
    "Accept": "application/json, text/plain, */*",
}


def request_json(
    url: str,
    *,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10,
    retries: int = 2,
    backoff_seconds: float = 0.8,
    retry_statuses: Iterable[int] = (429, 500, 502, 503, 504),
) -> Any:
    """Perform an HTTP request and parse JSON.

    Raises on final failure.
    """

    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)

    last_exc: Optional[BaseException] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                data=data,
                headers=merged_headers,
                timeout=timeout,
            )

            if resp.status_code in set(retry_statuses) and attempt < retries:
                retry_after = resp.headers.get("Retry-After")
                try:
                    sleep_s = float(retry_after) if retry_after else backoff_seconds * (2**attempt)
                except Exception:
                    sleep_s = backoff_seconds * (2**attempt)
                time.sleep(min(10.0, max(0.0, sleep_s)))
                continue

            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            last_exc = e
            if attempt >= retries:
                raise
            time.sleep(backoff_seconds * (2**attempt))

    # Unreachable, but keeps type-checkers happy
    raise last_exc  # type: ignore[misc]
