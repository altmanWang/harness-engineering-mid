# -*- coding: utf-8 -*-
"""回测执行层：Cerebro 装配、运行、结果输出."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import backtrader as bt

from ..data.loader import load_csv_data
from ..strategies.ema_pullback import EMA20PullbackStrategy
from ..strategies.ema_pullback_config import INITIAL_CAPITAL


def run_backtest(csv_path: str, output_dir: str | None = None, config_overrides: dict | None = None, plot: bool = False) -> dict:
    """回测模式：运行 Cerebro，输出交易记录 CSV 和汇总 JSON。

    Args:
        csv_path: 输入 CSV 路径
        output_dir: 输出目录（存放 bars CSV 和 summary JSON），None 则自动使用 CSV 所在目录
        config_overrides: 策略参数覆盖
        plot: 是否显示图表

    Returns:
        {"bars_csv": str, "summary_json": str, "summary": dict}
    """
    data, stock_name = load_csv_data(csv_path)

    strategy_kwargs: dict = {"stock_name": stock_name}
    if config_overrides:
        strategy_kwargs.update(config_overrides)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(EMA20PullbackStrategy, **strategy_kwargs)
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

    # 确定输出目录
    input_path = Path(csv_path)
    out_dir = Path(output_dir) if output_dir else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    code = input_path.stem.split("_")[0] if "_" in input_path.stem else input_path.stem

    # 输出 bars CSV
    bars_csv = str(out_dir / f"{code}_bars.csv")
    strategy.recorder.to_csv(bars_csv)
    print(f"交易记录已保存至: {bars_csv}")

    # 计算汇总指标
    records = strategy.recorder._records
    # 从 bars 中提取交易信号
    buy_records: list[dict] = []
    sell_records: list[dict] = []
    for r in records:
        sig = r.get("signal", "")
        if sig == "买入":
            buy_records.append(r)
        elif sig == "卖出":
            sell_records.append(r)

    # 计算胜率：配对买入-卖出，计算每笔盈亏
    win_count = 0
    total_trades = min(len(buy_records), len(sell_records))
    for i in range(total_trades):
        buy_cost = buy_records[i].get("cost", 0) or 0
        sell_profit = sell_records[i].get("profit", 0) or 0
        if sell_profit > 0:
            win_count += 1

    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0

    # 计算最大回撤：从资金序列中找
    capital_series = [r.get("capital", starting_value) or starting_value for r in records]
    peak = capital_series[0]
    max_dd = 0.0
    for cap in capital_series:
        if cap > peak:
            peak = cap
        dd = (peak - cap) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    total_return = (final_value / starting_value - 1) * 100 if starting_value > 0 else 0.0

    summary = {
        "stock_code": code,
        "stock_name": stock_name,
        "initial_capital": round(starting_value, 2),
        "final_capital": round(final_value, 2),
        "total_return": round(total_return, 2),
        "max_drawdown": round(max_dd, 2),
        "win_rate": round(win_rate, 2),
        "trade_count": total_trades,
    }

    # 输出 summary JSON
    summary_json = str(out_dir / f"{code}_summary.json")
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"汇总已保存至: {summary_json}")

    if plot:
        cerebro.plot(style="candlestick")

    return {"bars_csv": bars_csv, "summary_json": summary_json, "summary": summary}


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
