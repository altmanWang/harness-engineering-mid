# -*- coding: utf-8 -*-
"""EMA20 趋势+回调入场策略（Al Brooks 风格）."""

from __future__ import annotations

import backtrader as bt

from .ema_pullback_config import (
    BREAKOUT_EMA_BUFFER,
    BREAKOUT_EMA_SLOPE,
    EMA_PERIOD,
    LOT_SIZE,
    PULLBACK_EMA_BUFFER,
    SIGNAL_BAR_EXPIRE,
    STOP_LOSS_RATIO,
    SWING_HIGH_WINDOW,
    TREND_CONFIRM_BARS,
    TREND_CONFIRM_RATIO,
)
from ..data.recorder import TradeRecorder


class EMA20PullbackStrategy(bt.Strategy):
    """EMA20 趋势判断 + 回调到均线附近出现阳线信号K线后入场。

    仅做多，单笔持仓。卖出后才能再次买入。
    """

    params = (
        ("ema_period", EMA_PERIOD),
        ("trend_confirm_bars", TREND_CONFIRM_BARS),
        ("trend_confirm_ratio", TREND_CONFIRM_RATIO),
        ("pullback_ema_buffer", PULLBACK_EMA_BUFFER),
        ("signal_bar_expire", SIGNAL_BAR_EXPIRE),
        ("stop_loss_ratio", STOP_LOSS_RATIO),
        ("lot_size", LOT_SIZE),
        ("swing_high_window", SWING_HIGH_WINDOW),
        ("breakout_ema_slope", BREAKOUT_EMA_SLOPE),
        ("breakout_ema_buffer", BREAKOUT_EMA_BUFFER),
        ("signal_only", False),
        ("stock_name", ""),
    )

    def __init__(self) -> None:
        self.ema = bt.indicators.ExponentialMovingAverage(
            self.data.close, period=self.p.ema_period
        )
        self.recorder = TradeRecorder()
        self._signal_bar_high: float | None = None
        self._signal_bar_low: float | None = None
        self._signal_bar_age: int = 0
        self._entry_price: float = 0.0
        self._stop_loss_price: float = 0.0
        self._pending_ema_exit: bool = False
        self._highest_close: float = 0.0
        self._target_price: float = 0.0
        self._bar_signal: str = "观望"
        self._bar_cost: float = 0.0
        self._bar_profit: float | None = None
        self._traded_this_bar: bool = False
        self.order = None

    def _is_uptrend(self) -> bool:
        if len(self.data) < self.p.trend_confirm_bars:
            return False
        required = int(self.p.trend_confirm_bars * self.p.trend_confirm_ratio)
        above_count = 0
        for i in range(self.p.trend_confirm_bars):
            if self.data.close[-i] > self.ema[-i]:
                above_count += 1
        return above_count >= required and self.data.close[0] > self.ema[0]

    def _is_bullish_bar(self) -> bool:
        return self.data.close[0] > self.data.open[0]

    def _is_pullback_to_ema(self) -> bool:
        threshold = self.ema[0] * (1 + self.p.pullback_ema_buffer)
        return self.data.low[0] <= threshold

    def _lower_low_than_prev(self) -> bool:
        if len(self.data) < 2:
            return False
        return self.data.low[0] < self.data.low[-1]

    def _is_signal_bar(self) -> bool:
        return (
            self._is_uptrend()
            and self._is_pullback_to_ema()
            and self._is_bullish_bar()
            and self._lower_low_than_prev()
        )

    def _check_entry(self) -> None:
        if self._signal_bar_high is None:
            return
        if self._signal_bar_age >= self.p.signal_bar_expire:
            self._clear_signal_bar()
            return
        if self.data.high[0] > self._signal_bar_high:
            entry_price = self.data.close[0]
            size = self.p.lot_size
            self._entry_price = entry_price
            self._highest_close = entry_price
            self._target_price = self._calc_leg_target(entry_price)
            self._stop_loss_price = max(
                entry_price * (1 - self.p.stop_loss_ratio),
                self._signal_bar_low or entry_price * 0.97,
            )
            self._bar_signal = "买入"
            self._bar_cost = entry_price * size
            self._bar_profit = None
            self._traded_this_bar = True
            self._clear_signal_bar()
            self.buy(size=size)
        else:
            self._signal_bar_age += 1

    def _clear_signal_bar(self) -> None:
        self._signal_bar_high = None
        self._signal_bar_low = None
        self._signal_bar_age = 0

    def _find_swing_high(self) -> float | None:
        w = self.p.swing_high_window
        min_bars = 2 * w + 1
        if len(self.data) < min_bars:
            return None
        for idx in range(-w, -(len(self.data) - w - 2), -1):
            bar_high = self.data.high[idx]
            is_swing = True
            for j in range(1, w + 1):
                if self.data.high[idx - j] >= bar_high or self.data.high[idx + j] >= bar_high:
                    is_swing = False
                    break
            if is_swing:
                return bar_high
        return None

    def _find_swing_low(self) -> float | None:
        w = self.p.swing_high_window
        min_bars = 2 * w + 1
        if len(self.data) < min_bars:
            return None
        for idx in range(-w, -(len(self.data) - w - 2), -1):
            bar_low = self.data.low[idx]
            is_swing = True
            for j in range(1, w + 1):
                if self.data.low[idx - j] <= bar_low or self.data.low[idx + j] <= bar_low:
                    is_swing = False
                    break
            if is_swing:
                return bar_low
        return None

    def _calc_leg_target(self, entry_price: float) -> float:
        sw_high = self._find_swing_high()
        sw_low = self._find_swing_low()
        if sw_high is None or sw_low is None or sw_high <= sw_low:
            return 0
        leg_height = sw_high - sw_low
        return entry_price + leg_height

    def _is_ema_rising(self) -> bool:
        if len(self.data) < self.p.breakout_ema_slope + self.p.ema_period:
            return False
        return self.ema[0] > self.ema[-self.p.breakout_ema_slope]

    def _is_price_near_ema(self) -> bool:
        upper = self.ema[0] * (1 + self.p.breakout_ema_buffer)
        return self.data.close[0] <= upper

    def _chase_recommendation(self) -> str:
        if self._is_ema_rising() and self.data.close[0] > self.ema[0] and self._is_bullish_bar():
            return "买入"
        return "观望"

    def _check_breakout_entry(self) -> None:
        sw_high = self._find_swing_high()
        if sw_high is None:
            return
        if not self._is_ema_rising():
            return
        if self.data.high[0] <= sw_high:
            return
        if not self._is_bullish_bar():
            return
        entry_price = self.data.close[0]
        size = self.p.lot_size
        self._entry_price = entry_price
        self._highest_close = entry_price
        self._target_price = self._calc_leg_target(entry_price)
        self._stop_loss_price = entry_price * (1 - self.p.stop_loss_ratio)
        self._bar_signal = "买入"
        self._bar_cost = entry_price * size
        self._bar_profit = None
        self._traded_this_bar = True
        self._clear_signal_bar()
        self.buy(size=size)

    def _check_exit(self) -> None:
        if not self.position:
            return
        if self._highest_close > 0 and self.data.close[0] <= self._highest_close * (1 - self.p.stop_loss_ratio):
            self._execute_sell(self.data.close[0], "止盈离场")
            return
        if self.data.low[0] <= self._stop_loss_price:
            self._execute_sell(self._stop_loss_price, "止损离场")
            return
        if self.data.close[0] < self.ema[0]:
            if self._pending_ema_exit:
                self._execute_sell(self.data.close[0], "EMA破位离场")
                self._pending_ema_exit = False
                return
            else:
                self._pending_ema_exit = True
        else:
            self._pending_ema_exit = False

    def _execute_sell(self, price: float, reason: str) -> None:
        size = self.p.lot_size
        if self.p.signal_only:
            self._bar_signal = "观望"
        else:
            self._bar_signal = "卖出"
        self._bar_cost = price * size
        self._bar_profit = (price - self._entry_price) * size
        self._stop_loss_price = 0.0
        self._entry_price = 0.0
        self._highest_close = 0.0
        self._target_price = 0.0
        self._pending_ema_exit = False
        self._traded_this_bar = True
        self.sell(size=size)

    def next(self) -> None:
        self._bar_signal = "观望"
        self._bar_cost = 0.0
        self._bar_profit = None
        self._traded_this_bar = False
        if not self.position:
            self._target_price = 0.0
        if len(self.data) < self.p.ema_period:
            self._record()
            return
        if self.position:
            self._check_exit()
            if self.position and not self._traded_this_bar:
                self._update_trailing_stop()
                if self.p.signal_only:
                    self._bar_signal = self._chase_recommendation()
                else:
                    self._bar_signal = "持有"
                if self.data.close[0] > self._highest_close:
                    self._highest_close = self.data.close[0]
        else:
            self._check_breakout_entry()
            if not self._traded_this_bar:
                self._check_entry()
            if not self.position and not self._traded_this_bar and self._is_signal_bar():
                self._signal_bar_high = self.data.high[0]
                self._signal_bar_low = self.data.low[0]
                self._signal_bar_age = 0
        self._record()

    def _update_trailing_stop(self) -> None:
        trail = self.data.close[0] * (1 - self.p.stop_loss_ratio)
        self._stop_loss_price = max(self._stop_loss_price, trail)

    def _record(self) -> None:
        date_str = self.data.datetime.date(0).isoformat()
        self.recorder.record(
            date=date_str,
            stock_name=self.p.stock_name,
            open_price=self.data.open[0],
            close_price=self.data.close[0],
            signal=self._bar_signal,
            cost=self._bar_cost,
            profit=self._bar_profit,
            capital=self.broker.getvalue(),
            stop_loss=self._stop_loss_price,
            target_price=self._target_price,
        )

    def notify_order(self, order: bt.Order) -> None:
        if order.status in (order.Completed, order.Canceled, order.Margin, order.Rejected):
            self.order = None

    def stop(self) -> None:
        if self.position:
            price = self.data.close[0]
            if self.p.signal_only:
                self._bar_signal = "观望"
            else:
                self._bar_signal = "卖出"
            self._bar_cost = price * self.p.lot_size
            self._bar_profit = (price - self._entry_price) * self.p.lot_size
            self._stop_loss_price = 0.0
            self._target_price = 0.0
            self._traded_this_bar = True
            self._record()
