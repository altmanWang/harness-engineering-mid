# -*- coding: utf-8 -*-
"""回测执行层：Cerebro 装配、运行、结果输出."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import backtrader as bt

from ..data.loader import load_csv_data
from ..strategies.ema_pullback import EMA20PullbackStrategy
from ..strategies.ema_pullback_config import INITIAL_CAPITAL


def run_backtest(csv_path: str, output_path: str | None = None, plot: bool = False) -> str:
    """回测模式：运行 Cerebro，输出交易记录 CSV 和收益曲线图。

    Args:
        csv_path: 输入 CSV 路径
        output_path: 输出 CSV 路径（None 则自动生成）
        plot: 是否显示图表

    Returns:
        输出的交易记录 CSV 路径
    """
    data, stock_name = load_csv_data(csv_path)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(EMA20PullbackStrategy, stock_name=stock_name)
    cerebro.broker.setcash(INITIAL_CAPITAL)

    starting_value = cerebro.broker.getvalue()
    print(f"初始资金: {starting_value:,.0f}")
    print(f"股票: {stock_name}")
    print("-" * 50)

    results = cerebro.run()
    strategy: EMA20PullbackStrategy = results[0]

    final_value = cerebro.broker.getvalue()
    print(f"最终资金: {final_value:,.0f}")
    print(f"总收益: {final_value - starting_value:+,.0f}")
    print(f"收益率: {(final_value / starting_value - 1) * 100:+.2f}%")
    print(f"交易记录数: {len(strategy.recorder)}")

    # 输出交易记录 CSV
    if output_path is None:
        input_path = Path(csv_path)
        output_path = str(input_path.parent / f"{input_path.stem}_trades.csv")
    strategy.recorder.to_csv(output_path)
    print(f"交易记录已保存至: {output_path}")

    if plot:
        cerebro.plot(style="candlestick")
    return output_path


def run_signal(csv_path: str, config_overrides: dict | None = None) -> dict:
    """信号模式：静默回测后返回最后一根 K 线的操作建议。

    Args:
        csv_path: K 线 CSV 路径
        config_overrides: 策略参数覆盖，如 {"ema_period": 30, "stop_loss_ratio": 0.08}

    Returns:
        {"signal": "买入"|"观望", "date": "...", "open": ..., "close": ..., "stop_loss": ...}
    """
    data, stock_name = load_csv_data(csv_path)

    strategy_kwargs: dict = {"stock_name": stock_name, "signal_only": True}
    if config_overrides:
        strategy_kwargs.update(config_overrides)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(EMA20PullbackStrategy, **strategy_kwargs)
    cerebro.broker.setcash(INITIAL_CAPITAL)

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        results = cerebro.run()
    finally:
        sys.stdout = old_stdout

    strategy: EMA20PullbackStrategy = results[0]
    last = strategy.recorder.last()

    if last is None:
        return {"signal": "观望", "date": "", "open": 0, "close": 0, "stop_loss": 0}

    return {
        "signal": last["signal"],
        "date": last["date"],
        "open": last["open"],
        "close": last["close"],
        "stop_loss": last["stop_loss"],
    }
