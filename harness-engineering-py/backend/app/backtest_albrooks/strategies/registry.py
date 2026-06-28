# -*- coding: utf-8 -*-
"""策略注册表：每个策略的元数据和配置项 schema。"""

STRATEGY_REGISTRY: dict[str, dict] = {
    "ema_pullback": {
        "id": "ema_pullback",
        "name": "EMA20 趋势回调",
        "description": "EMA20 趋势判断 + 回调到均线附近出现阳线信号K线后入场（Al Brooks 风格）",
        "module": "ema_pullback",
        "config_class": "EMA20PullbackStrategy",
        "configSchema": [
            {"key": "ema_period",           "label": "EMA 周期",           "type": "int",   "default": 20,    "min": 5,   "max": 200,  "description": "EMA 均线计算周期"},
            {"key": "trend_confirm_bars",   "label": "趋势确认K线数",       "type": "int",   "default": 5,     "min": 2,   "max": 50,   "description": "趋势确认回溯 K 线根数"},
            {"key": "trend_confirm_ratio",  "label": "趋势确认占比",        "type": "float", "default": 0.6,   "min": 0.3, "max": 1.0, "step": 0.05, "description": "收盘在 EMA 上方的比例阈值"},
            {"key": "pullback_ema_buffer",  "label": "回调缓冲区",          "type": "float", "default": 0.02,  "min": 0.0, "max": 0.1, "step": 0.005, "description": "回调到 EMA 上方的缓冲范围"},
            {"key": "signal_bar_expire",   "label": "信号K线有效期(天)",    "type": "int",   "default": 1,     "min": 1,   "max": 10,   "description": "信号K线未触发即失效的天数"},
            {"key": "swing_high_window",   "label": "波段高低确认窗口",     "type": "int",   "default": 2,     "min": 1,   "max": 10,   "description": "波段高点/低点前后确认 K 线数"},
            {"key": "breakout_ema_slope",  "label": "EMA斜率确认回溯",     "type": "int",   "default": 5,     "min": 2,   "max": 30,   "description": "突破追入时 EMA 斜率确认回溯 bar 数"},
            {"key": "breakout_ema_buffer", "label": "突破追入EMA缓冲",      "type": "float", "default": 0.05,  "min": 0.01,"max": 0.2, "step": 0.01, "description": "突破追入时价格距 EMA 的上限"},
            {"key": "stop_loss_ratio",     "label": "止损/止盈比例",        "type": "float", "default": 0.05,  "min": 0.01,"max": 0.2, "step": 0.01, "description": "止损和移动止盈的回撤比例"},
            {"key": "lot_size",            "label": "每手股数",            "type": "int",   "default": 100,   "min": 100, "max": 10000,"step": 100, "description": "每手买入股数"},
        ],
    },
}
