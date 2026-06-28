# -*- coding: utf-8 -*-
"""交易记录器：逐 bar 记录并输出 CSV."""

from __future__ import annotations

import csv
from typing import Any, Dict, List, Optional


class TradeRecorder:
    """按交易日逐行记录交易状态。"""

    COLUMNS = [
        "stock_name", "date", "open", "close",
        "signal", "cost", "profit", "capital", "stop_loss", "target_price",
    ]

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def record(
        self,
        date: str,
        stock_name: str,
        open_price: float,
        close_price: float,
        signal: str,
        cost: float,
        profit: Optional[float],
        capital: float,
        stop_loss: float,
        target_price: float = 0,
    ) -> None:
        self._records.append({
            "stock_name": stock_name,
            "date": date,
            "open": round(open_price, 2),
            "close": round(close_price, 2),
            "signal": signal,
            "cost": round(cost, 2),
            "profit": "" if profit is None else round(profit, 2),
            "capital": round(capital, 2),
            "stop_loss": round(stop_loss, 2) if stop_loss else 0,
            "target_price": round(target_price, 2) if target_price else 0,
        })

    def to_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(self._records)

    def last(self) -> Optional[Dict[str, Any]]:
        return self._records[-1] if self._records else None

    def __len__(self) -> int:
        return len(self._records)
