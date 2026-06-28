# -*- coding: utf-8 -*-
"""K 线数据加载：CSV → backtrader DataFeed."""

from __future__ import annotations

import sys

import backtrader as bt
import pandas as pd


REQUIRED_COLUMNS = {"date", "open", "high", "low", "close"}


def load_csv_data(csv_path: str) -> tuple[bt.feeds.PandasData, str]:
    """从 CSV 加载数据并返回 DataFeed 和股票名称。"""
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"错误：无法读取 CSV 文件: {e}")
        sys.exit(1)

    if df.empty:
        print("错误：CSV 文件无数据")
        sys.exit(1)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        print(f"错误：CSV 缺少必要列: {missing}")
        sys.exit(1)

    df["date"] = pd.to_datetime(df["date"])

    stock_name = ""
    if "name" in df.columns:
        stock_name = str(df["name"].iloc[0])

    df.set_index("date", inplace=True)

    data = bt.feeds.PandasData(
        dataname=df,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
    )
    return data, stock_name
