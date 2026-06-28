# -*- coding: utf-8 -*-
"""回测工具入口：backtest 模式和 signal 模式.

用法:
    python -m backtest_albrooks.main --mode backtest --file data/xxx.csv
    python -m backtest_albrooks.main --mode backtest --file data/xxx.csv --output result.csv
    python -m backtest_albrooks.main --mode signal --file data/xxx.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine.runner import run_backtest, run_signal


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EMA20 趋势+回调策略回测工具"
    )
    parser.add_argument(
        "--mode",
        choices=["backtest", "signal"],
        required=True,
        help="回测模式: backtest=完整回测+CSV+图表, signal=最新信号建议",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="输入的 CSV 数据文件路径",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="回测结果 CSV 输出路径（默认与输入同目录，_trades 后缀）",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="回测模式下显示收益曲线图（默认关闭）",
    )
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.exists():
        print(f"错误: 文件不存在: {csv_path}")
        sys.exit(1)

    if args.mode == "backtest":
        run_backtest(str(csv_path), output_path=args.output, plot=args.plot)
    else:
        run_signal(str(csv_path))


if __name__ == "__main__":
    main()
