#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Broker client interfaces.

Keep these interfaces small and stable; implementations can vary per broker.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class BrokerClient(Protocol):
    name: str

    def is_configured(self) -> bool:
        ...

    def get_account_summary(self) -> Dict[str, Any]:
        ...

    def get_positions(self) -> List[Dict[str, Any]]:
        ...

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        reduce_only: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ...
