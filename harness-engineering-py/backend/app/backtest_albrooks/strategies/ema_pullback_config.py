# -*- coding: utf-8 -*-
"""回测系统可调参数."""

# --- 资金与仓位 ---
INITIAL_CAPITAL = 20_000
LOT_SIZE = 100

# --- EMA 趋势 ---
EMA_PERIOD = 20
TREND_CONFIRM_BARS = 5
TREND_CONFIRM_RATIO = 0.6

# --- 回调入场 ---
PULLBACK_EMA_BUFFER = 0.02
SIGNAL_BAR_EXPIRE = 1

# --- 突破追入（波段高点） ---
SWING_HIGH_WINDOW = 2
BREAKOUT_EMA_SLOPE = 5
BREAKOUT_EMA_BUFFER = 0.05

# --- 止损 ---
STOP_LOSS_RATIO = 0.05
