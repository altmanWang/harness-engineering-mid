# 智能诊股 — 策略信号模式改造

> 创建时间: 2026-06-28 | 状态: 已确认

---

## 1. 概述

将智能诊股的判断逻辑从 **LLM 调用** 改为 **backtest_albrooks 策略信号模式**。用户选择一种策略，后端用该策略的 `signal_only` 模式分析每只股票，输出"买入"或"观望"信号，替代原先 LLM 输出的 看多/看空/观望。

目前只有 `ema_pullback` 一种策略，设计上预留策略扩展机制。

## 2. 与现有设计的区别

本文档仅覆盖**诊股判断逻辑的改造**。回测功能（BacktestPanel 等）已在 `2026-06-28-stock-backtest-design.md` 中设计，不在此范围。

核心变更：
- **去掉** LLM 诊股（engine.execute + prompt 构建 + conclusion 解析）
- **改为** backtest_albrooks `run_signal()` 策略信号调用
- **去掉** Skills 多选下拉，改为策略单选下拉 + 配置折叠面板
- **结论** 从三态（看多/看空/观望）改为两态（买入/观望）

## 3. 决策记录

| 决策点 | 选择 | 说明 |
|--------|------|------|
| 结论状态 | 买入 / 观望 | 去掉看空，策略信号模式只输出这两种 |
| 策略选择 | 单选 | 一次诊股用一种策略 |
| 配置 UI | 内联折叠 | 默认折叠显示关键参数摘要，展开可编辑全部参数 |
| K 线数据 | 保留现有流程 | AStockClient 拉取，保存 CSV（供 K 线图 + 策略信号） |
| 配置传递 | API 参数覆盖 | 前端传 config_overrides，后端动态覆盖，不改配置文件 |
| 策略列表 | 硬编码注册表 | 后端维护策略注册表，新策略手动注册 |

## 4. 策略注册表

新增 `backtest_albrooks/strategies/registry.py`：

```python
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
```

扩展新策略时：在 `STRATEGY_REGISTRY` 中添加新条目，创建对应的 `strategies/<name>.py` 和 `strategies/<name>_config.py` 即可。

## 5. 后端改动

### 5.1 新增 API

**`GET /api/stock/strategies`**

返回策略注册表（去掉 `module` 和 `config_class` 等内部字段）：

```json
{
  "strategies": [
    {
      "id": "ema_pullback",
      "name": "EMA20 趋势回调",
      "description": "EMA20 趋势判断 + 回调到均线附近出现阳线信号K线后入场（Al Brooks 风格）",
      "configSchema": [...]
    }
  ]
}
```

### 5.2 修改 `run_signal` (`engine/runner.py`)

增加 `config_overrides: dict | None = None` 参数。将策略参数通过 `addstrategy` 的 kwargs 传入，覆盖默认值。返回值从 `None`（直接 print）改为返回 `dict`，包含 signal、date、open、close、stop_loss。

```python
def run_signal(csv_path: str, config_overrides: dict | None = None) -> dict:
    """信号模式：静默回测后返回最后一根 K 线的操作建议。

    Args:
        csv_path: K 线 CSV 路径
        config_overrides: 策略参数覆盖

    Returns:
        {"signal": "买入"|"观望", "date": "...", "open": ..., "close": ..., "stop_loss": ...}
    """
    data, stock_name = load_csv_data(csv_path)

    strategy_kwargs = {"stock_name": stock_name, "signal_only": True}
    if config_overrides:
        # 将用户配置的 key 映射为 backtrader params 名称
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
```

### 5.3 修改 `_run_analysis` (`routers/stock.py`)

核心变更：去掉 LLM 调用链，改为策略信号调用。

**之前**：
1. 加载 skills 到 worktree
2. 创建 OpenCode engine
3. 构建 prompt → `engine.execute()` → 解析结论/理由

**之后**：
1. ~~加载 skills 到 worktree~~ （不再需要）
2. ~~创建 OpenCode engine~~ （不再需要）
3. `AStockClient.get_kline()` → 存 CSV → `run_signal(csv_path, config_overrides)` → 获取信号

关键代码路径：

```python
async def _run_analysis(
    analysis_id: str,
    codes: list[str],
    days: int,
    strategy: str,          # 新：策略 ID
    strategy_config: dict,  # 新：策略配置覆盖
    session_id: str,
    sector: str = "",
) -> None:
    import pandas as pd
    from a_stock_client import AStockClient
    from app.backtest_albrooks.engine.runner import run_signal

    client = AStockClient()
    session = await get_session(session_id)
    if session is None:
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    await _stream_event(analysis_id, "start", {
        "total": len(codes),
        "codes": codes,
    })

    results: list = []
    success_count = 0
    failed_count = 0

    for code in codes:
        try:
            df = client.get_kline(code, start_date, end_date)
            last_row = df.iloc[-1]
            name = str(last_row.get("name", code))
            source = str(last_row.get("source", ""))
            close_val = float(last_row["close"]) if pd.notna(last_row.get("close")) else None
            open_val = float(last_row["open"]) if pd.notna(last_row.get("open")) else None
            pct_chg_val = float(last_row["pct_chg"]) if pd.notna(last_row.get("pct_chg")) else None
            ema20_val = float(last_row["ma20"]) if pd.notna(last_row.get("ma20")) else None

            # 保存 K 线 CSV（保留，供 K 线图使用）
            kline_dir = WORKTREES_DIR / session_id / "kline"
            kline_dir.mkdir(parents=True, exist_ok=True)
            kline_filename = f"{code}_{start_date}_{end_date}.csv"
            kline_path = kline_dir / kline_filename
            df_to_save = df.copy()
            if "date" in df_to_save.columns:
                df_to_save["date"] = pd.to_datetime(df_to_save["date"]).dt.strftime("%Y-%m-%d")
            df_to_save.to_csv(str(kline_path), index=False, encoding="utf-8-sig")
            kline_rel_path = f"worktrees/{session_id}/kline/{kline_filename}"

            # 调用策略信号（替代 LLM）
            signal_result = run_signal(str(kline_path), config_overrides=strategy_config)
            conclusion = signal_result["signal"]  # "买入" 或 "观望"

            kline_date = str(last_row.get("date", ""))
            if hasattr(kline_date, "strftime"):
                kline_date = kline_date.strftime("%Y-%m-%d")

            diagnosis_result = DiagnosisResult(
                code=code,
                name=name,
                conclusion=conclusion,   # 两态：买入/观望
                reason="",               # 策略模式无文本理由
                close=close_val,
                open=open_val,
                pct_chg=pct_chg_val,
                ema20=ema20_val,
                source=source,
                klinePath=kline_rel_path,
                klineDate=kline_date,
            )
            results.append(diagnosis_result)
            success_count += 1

            await _stream_event(analysis_id, "stock_result", diagnosis_result.model_dump())

        except Exception as e:
            error_msg = str(e)[:200]
            diagnosis_result = DiagnosisResult(
                code=code,
                name=code,
                conclusion=None,
                reason="",
                error=error_msg,
            )
            results.append(diagnosis_result)
            failed_count += 1
            await _stream_event(analysis_id, "stock_error", {
                "code": code,
                "error": error_msg,
            })

    session.diagnosis = StockDiagnosis(
        codes=codes,
        sector=sector or None,
        days=days,
        strategy=strategy,              # 新字段
        strategyConfig=strategy_config, # 新字段
        skills=[],                      # 不再使用
        skillNames=[],
        initialPrompt="",
        results=results,
        successCount=success_count,
        failedCount=failed_count,
    )
    await save_session(session)

    await _stream_event(analysis_id, "done", {
        "analysisId": analysis_id,
        "total": len(codes),
        "success": success_count,
        "failed": failed_count,
    })
```

### 5.4 修改 `POST /api/stock/analyze` 请求处理

接收新增的 `strategy` 和 `strategyConfig` 字段，传递给 `_run_analysis`。

### 5.5 数据模型变更 (`models/schemas.py`)

```python
class StockDiagnosis(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None
    days: int = 90
    strategy: str = ""               # 新增：策略 ID
    strategyConfig: dict = {}        # 新增：用户覆盖的配置
    skills: List[str] = []           # 保留兼容，不再使用
    skillNames: List[str] = []       # 保留兼容，不再使用
    initialPrompt: str = ""
    results: List[DiagnosisResult] = []
    successCount: int = 0
    failedCount: int = 0


class StockAnalyzeRequest(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None
    days: int = 90
    strategy: Optional[str] = None       # 新增：策略 ID
    strategyConfig: Optional[dict] = None # 新增：策略配置覆盖
    skills: List[str] = []               # 保留兼容
    sessionId: Optional[str] = None
    model: Optional[str] = None          # 保留兼容
```

### 5.6 文件变更清单（后端）

| 文件 | 变更 |
|------|------|
| `backtest_albrooks/strategies/registry.py` | **新文件**：策略注册表 |
| `backtest_albrooks/engine/runner.py` | `run_signal()` 增加 `config_overrides` 参数，返回 dict |
| `app/routers/stock.py` | `_run_analysis()` 去掉 LLM 调用链，改为 `run_signal()`；新增 `GET /api/stock/strategies` |
| `app/models/schemas.py` | `StockDiagnosis`、`StockAnalyzeRequest` 增加 strategy/strategyConfig 字段 |

## 6. 前端改动

### 6.1 StockInput.vue — 策略选择 + 配置面板

**Skills 下拉 → 策略单选下拉**：

```vue
<div class="option-item">
  <label class="option-label">策略</label>
  <el-select
    :model-value="selectedStrategy"
    placeholder="选择策略"
    style="width: 220px"
    @update:model-value="onStrategyChange"
  >
    <el-option
      v-for="s in strategyList"
      :key="s.id"
      :label="s.name"
      :value="s.id"
    />
  </el-select>
</div>
```

**配置折叠面板**（策略选中后出现）：

```
+-------------------------------------------------+
| EMA20 趋势回调                    [展开/收起]    |
| EMA20 . 止损5% . 每手100股        [重置默认]    |
+-------------------------------------------------+
| (展开后)                                        |
| EMA 周期          [20    ]  EMA 均线计算周期     |
| 趋势确认K线数      [5     ]  趋势确认回溯 K 线数  |
| 趋势确认占比       [0.6   ]  收盘在 EMA 上方比例  |
| 回调缓冲区         [0.02  ]  回调到 EMA 上方范围  |
| ...                                             |
+-------------------------------------------------+
```

- 折叠状态：显示一行摘要（2-3 个关键参数 + 策略名）
- 展开状态：动态渲染所有 configSchema 字段（根据 type 渲染不同的 input 组件）
- "重置默认"按钮：恢复所有字段为 schema default 值

### 6.2 StockResultTable.vue — 结论标签变更

- 图标：去掉 Top/Bottom/Minus，改为 `CircleCheck`(买入) / `Clock`(观望)
- 颜色：买入 → `success`(绿)，观望 → `warning`(黄)
- 理由列：策略模式下为空，可隐藏或显示简短策略信号说明

### 6.3 StockView.vue — 策略参数传递

```typescript
const selectedStrategy = ref('ema_pullback')
const strategyConfig = ref<Record<string, any>>({})

async function handleStart() {
  await startAnalysis(
    codes.value,
    days.value,
    selectedStrategy.value,    // 新：策略 ID
    strategyConfig.value,       // 新：配置覆盖
  )
}
```

### 6.4 useStockAnalysis.ts — 接口变更

`startAnalysis` 参数从 `(codes, days, skills, sessionId?, model?)` 改为 `(codes, days, strategy, strategyConfig, sessionId?)`。POST body 增加 `strategy` 和 `strategyConfig` 字段，去掉 `skills` 和 `model`。

### 6.5 类型定义 (`types/stock.ts`)

```typescript
export interface StrategyConfigItem {
  key: string
  label: string
  type: 'int' | 'float'
  default: number
  min?: number
  max?: number
  step?: number
  description: string
}

export interface StrategyInfo {
  id: string
  name: string
  description: string
  configSchema: StrategyConfigItem[]
}

// StockDiagnosis 增加字段
export interface StockDiagnosis {
  // ... existing fields ...
  strategy: string
  strategyConfig: Record<string, any>
}
```

### 6.6 文件变更清单（前端）

| 文件 | 变更 |
|------|------|
| `components/stock/StockInput.vue` | Skills 下拉 → 策略下拉 + 配置折叠面板 |
| `components/stock/StockResultTable.vue` | 结论图标/颜色映射从三态改为两态 |
| `views/StockView.vue` | selectedStrategy + strategyConfig 状态管理 |
| `composables/useStockAnalysis.ts` | startAnalysis 参数变更 |
| `types/stock.ts` | 新增 StrategyInfo、StrategyConfigItem；StockDiagnosis 增加字段 |

## 7. 数据流

```
用户选择策略 → 展开配置(可选修改) → 点击开始诊股
  |
  +-- GET /api/stock/strategies  → 加载策略列表
  |
  +-- POST /api/stock/analyze {codes, strategy: "ema_pullback", strategyConfig: {ema_period: 30}}
       |
       +-- 后端逐只:
       |   1. AStockClient.get_kline(code)
       |   2. 保存 CSV 到 worktree/kline/
       |   3. run_signal(csv_path, config_overrides={ema_period: 30})
       |   4. SSE → stock_result {conclusion: "买入"|"观望"}
       |
       +-- 前端: StockResultTable 逐行更新
```

## 8. 边界与异常处理

- **策略 ID 无效**：后端返回 400 "Unknown strategy: xxx"
- **K 线数据不足**（EMA 周期需要最少数据）：`run_signal` 内部 EMA 未就绪时跳过，最终可能返回 "观望"
- **CSV 格式不兼容**：`load_csv_data` 会检查必要列，缺失时抛出异常 → SSE 推送 `stock_error`
- **config_overrides 类型错误**：后端在传给 backtrader 前做基本校验（int/float 类型转换）
- **旧会话兼容**：`StockDiagnosis` 的 `skills` 和 `skillNames` 字段保留，旧会话加载时不受影响；`strategy` 为空表示旧版 LLM 诊股

## 9. 未涉及的部分

以下功能不在本次改造范围内：
- 回测功能（BacktestPanel、BacktestResultView 等）— 见 `2026-06-28-stock-backtest-design.md`
- 板块诊股（sector 模式）— 保留现有流程，仅判断逻辑切换到策略信号
- StockCompare 对比模式 — 保留现有流程
- KLineChart — 保留不变
