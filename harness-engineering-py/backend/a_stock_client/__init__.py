# -*- coding: utf-8 -*-
"""
===================================
A 股 K 线数据客户端（独立模块）
===================================

职责：
1. 封装 A 股历史 K 线数据的获取逻辑
2. 支持指定股票代码、起始/终止日期
3. 返回标准化的 K 线数据（OHLCV + 涨跌幅）
4. 支持 CSV 文件存储

使用方式：
    from a_stock_client import AStockClient

    client = AStockClient()
    df = client.get_kline("600519", "2025-01-01", "2025-12-31")
    client.to_csv("600519", "2025-01-01", "2025-12-31", "kline_600519.csv")

数据源优先级（复用 data_provider 的 DataFetcherManager）：
    EfinanceFetcher(P0) → AkshareFetcher(P1) → PytdxFetcher(P2)
    → BaostockFetcher(P3) → YfinanceFetcher(P4)

返回的 DataFrame 列：
    date, open, high, low, close, volume, amount, pct_chg,
    ma5, ma10, ma20, volume_ratio, code, name, source
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# 将 a_stock_client 自身目录插入 sys.path[0]，使本地 data_provider/ 和 src/
# 包优先于项目根目录的同名包，实现完全独立运行。
_CLIENT_ROOT = Path(__file__).resolve().parent
if str(_CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_CLIENT_ROOT))

logger = logging.getLogger(__name__)


class AStockClient:
    """
    A 股 K 线数据客户端

    封装了项目的 DataFetcherManager，提供简化的接口：
    - 输入：股票代码 + 起始/终止日期
    - 输出：标准化的 K 线 DataFrame 或 CSV 文件

    支持市场：
    - A 股（沪深 / 科创 / 北交所）：6 位数字代码，如 600519、000001、688981、920748
    - 港股：5 位数字代码，如 00700、01810
    - 美股：字母代码，如 AAPL、TSLA（由 YFinanceFetcher 处理）

    示例：
        >>> client = AStockClient()
        >>> df = client.get_kline("600519", "2025-06-01", "2025-06-20")
        >>> print(df.head())
        >>> client.to_csv("600519", "2025-06-01", "2025-06-20", "maotai.csv")
    """

    # 标准输出列
    OUTPUT_COLUMNS = [
        "date", "open", "high", "low", "close",
        "volume", "amount", "pct_chg",
        "ma5", "ma10", "ma20", "volume_ratio",
        "code", "name", "source",
    ]

    def __init__(self):
        """初始化客户端，加载项目配置并创建数据源管理器。"""
        self._setup_env()
        self._manager = None
        self._stock_name_cache: dict = {}

    def _setup_env(self) -> None:
        """加载项目 .env 配置（如果存在）。"""
        # 先尝试父目录（项目根目录的 .env），再尝试自身目录
        for candidate in (_CLIENT_ROOT.parent, _CLIENT_ROOT):
            env_file = candidate / ".env"
            if env_file.exists():
                try:
                    from dotenv import dotenv_values
                    env_values = dotenv_values(str(env_file))
                    for key, value in env_values.items():
                        if key and value and key not in os.environ:
                            os.environ[key] = value
                except Exception:
                    pass
                break

    @property
    def manager(self):
        """懒加载 DataFetcherManager 实例。"""
        if self._manager is None:
            from data_provider.base import DataFetcherManager
            self._manager = DataFetcherManager()
        return self._manager

    def get_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取指定股票在日期范围内的日线 K 线数据。

        Args:
            stock_code: 股票代码，如 "600519"（茅台）、"000001"（平安银行）
            start_date: 起始日期，格式 "YYYY-MM-DD"
            end_date: 终止日期，格式 "YYYY-MM-DD"

        Returns:
            标准化的 K 线 DataFrame，包含以下列：
            - date: 交易日期
            - open: 开盘价（前复权）
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量（股）
            - amount: 成交额（元）
            - pct_chg: 涨跌幅（%）
            - ma5/ma10/ma20: 移动均线
            - volume_ratio: 量比
            - code: 股票代码
            - name: 股票名称
            - source: 数据来源

        Raises:
            ValueError: 日期格式错误或起始日期晚于终止日期
            RuntimeError: 所有数据源均获取失败
        """
        # --- 参数校验 ---
        stock_code = str(stock_code).strip()
        if not stock_code:
            raise ValueError("stock_code 不能为空")

        start_date = self._normalize_date(start_date)
        end_date = self._normalize_date(end_date)

        if start_date > end_date:
            raise ValueError(
                f"起始日期 {start_date} 不能晚于终止日期 {end_date}"
            )

        # 计算需要获取的天数（用于 DataFetcherManager 的 days 参数）
        days = (datetime.strptime(end_date, "%Y-%m-%d")
                - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
        # 多取一些以覆盖非交易日
        days = max(days * 2, 30)

        # --- 获取数据 ---
        logger.info(
            "获取 %s K线数据: %s ~ %s (days=%d)",
            stock_code, start_date, end_date, days,
        )

        df, source = self.manager.get_daily_data(
            stock_code,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

        if df is None or df.empty:
            raise RuntimeError(
                f"获取 {stock_code} K线数据失败：所有数据源均返回空数据"
            )

        # --- 按日期范围过滤 ---
        df = df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]

        if df.empty:
            raise RuntimeError(
                f"日期范围 {start_date} ~ {end_date} 内无 {stock_code} 的交易数据"
            )

        # --- 添加元数据列 ---
        df["code"] = stock_code
        df["source"] = source

        # 获取股票名称
        name = self._stock_name_cache.get(stock_code)
        if name is None:
            try:
                name = self.manager.get_stock_name(stock_code) or ""
            except Exception:
                name = ""
            self._stock_name_cache[stock_code] = name
        df["name"] = name

        # --- 整理输出列 ---
        output_cols = [c for c in self.OUTPUT_COLUMNS if c in df.columns]
        df = df[output_cols]

        # 按日期排序
        df = df.sort_values("date", ascending=True).reset_index(drop=True)

        logger.info(
            "获取 %s (%s) K线成功: %d 条, 来源=%s",
            stock_code, name, len(df), source,
        )
        return df

    def to_csv(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        filepath: str,
    ) -> str:
        """
        获取 K 线数据并保存为 CSV 文件。

        Args:
            stock_code: 股票代码
            start_date: 起始日期 "YYYY-MM-DD"
            end_date: 终止日期 "YYYY-MM-DD"
            filepath: CSV 输出路径（相对或绝对）

        Returns:
            写入的 CSV 文件绝对路径

        Raises:
            ValueError: 参数校验失败
            RuntimeError: 数据获取失败
        """
        df = self.get_kline(stock_code, start_date, end_date)

        # 确保输出目录存在
        output_path = Path(filepath).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 格式化日期列
        df_to_save = df.copy()
        if "date" in df_to_save.columns:
            df_to_save["date"] = df_to_save["date"].dt.strftime("%Y-%m-%d")

        df_to_save.to_csv(str(output_path), index=False, encoding="utf-8-sig")
        logger.info("已保存 %d 条 K线数据到 %s", len(df), output_path)
        return str(output_path)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """校验并标准化日期格式为 YYYY-MM-DD。"""
        date_str = str(date_str).strip()
        # 支持 YYYYMMDD 格式
        if len(date_str) == 8 and date_str.isdigit():
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"日期格式错误: '{date_str}'，期望格式: YYYY-MM-DD 或 YYYYMMDD"
            )


# ------------------------------------------------------------------
# 命令行入口
# ------------------------------------------------------------------

def main():
    """命令行入口：python -m a_stock_client <代码> <起始> <终止> [输出csv]"""
    import argparse

    parser = argparse.ArgumentParser(
        description="A 股 K 线数据客户端 - 获取历史日线数据",
    )
    parser.add_argument("code", help="股票代码，如 600519")
    parser.add_argument("start", help="起始日期 YYYY-MM-DD 或 YYYYMMDD")
    parser.add_argument("end", help="终止日期 YYYY-MM-DD 或 YYYYMMDD")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="CSV 输出路径（可选，不指定则打印到终端）",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细日志",
    )

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    client = AStockClient()

    try:
        if args.output:
            path = client.to_csv(args.code, args.start, args.end, args.output)
            print(f"[OK] Saved to: {path}")
        else:
            df = client.get_kline(args.code, args.start, args.end)
            print(df.to_string(index=False))
            src = df['source'].iloc[0] if not df.empty else 'N/A'
            print(f"\nTotal: {len(df)} rows, Source: {src}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
