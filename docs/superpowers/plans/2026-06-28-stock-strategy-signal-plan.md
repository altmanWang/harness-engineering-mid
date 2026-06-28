# 智能诊股策略信号模式改造 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将智能诊股从 LLM 调用改为 backtest_albrooks 策略信号模式，用策略下拉+配置面板替换 Skills 下拉

**Architecture:** 后端新增策略注册表 + `run_signal()` 增强为可接收配置覆盖并返回 dict；`_run_analysis()` 去掉 LLM 链改为直接调用策略信号；前端 Skills 下拉替换为策略单选+折叠配置面板，结论从三态改为两态

**Tech Stack:** Python FastAPI + backtrader + Vue 3 + TypeScript + Element Plus

---

### Task 1: 创建策略注册表

**Files:**
- Create: `harness-engineering-py/backend/app/backtest_albrooks/strategies/registry.py`

- [ ] **Step 1: 创建 registry.py**

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

- [ ] **Step 2: 验证文件语法正确**

Run: `cd harness-engineering-py/backend && python -c "from app.backtest_albrooks.strategies.registry import STRATEGY_REGISTRY; print(list(STRATEGY_REGISTRY.keys()))"`
Expected: `['ema_pullback']`

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/backend/app/backtest_albrooks/strategies/registry.py
git commit -m "feat: add strategy registry with config schema

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: 增强 run_signal 支持配置覆盖并返回 dict

**Files:**
- Modify: `harness-engineering-py/backend/app/backtest_albrooks/engine/runner.py`

- [ ] **Step 1: 修改 run_signal 函数签名和实现**

将 `runner.py` 中整个 `run_signal` 函数（第61-98行）替换为：

```python
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

- [ ] **Step 2: 验证 run_signal 语法正确**

Run: `cd harness-engineering-py/backend && python -c "from app.backtest_albrooks.engine.runner import run_signal; print('OK')"`
Expected: `OK`

- [ ] **Step 3: 用实际 CSV 测试 run_signal 返回 dict**

Run:
```bash
cd harness-engineering-py/backend && python -c "
from app.backtest_albrooks.engine.runner import run_signal
import os
csv_file = 'D:/codes/harness-engineering-mid/harness-engineering-mid/sh603650_2026-03-30_2026-06-28.csv'
if os.path.exists(csv_file):
    result = run_signal(csv_file)
    print(f'signal={result[\"signal\"]}, date={result[\"date\"]}, close={result[\"close\"]}')
else:
    print('CSV not found, skipping integration test')
"
```
Expected: `signal=买入` or `signal=观望` with valid date and close price (or "CSV not found" if CSV missing)

- [ ] **Step 4: 测试 config_overrides 参数传递**

Run:
```bash
cd harness-engineering-py/backend && python -c "
from app.backtest_albrooks.engine.runner import run_signal
import os
csv_file = 'D:/codes/harness-engineering-mid/harness-engineering-mid/sh603650_2026-03-30_2026-06-28.csv'
if os.path.exists(csv_file):
    result = run_signal(csv_file, config_overrides={'ema_period': 50})
    print(f'With ema_period=50: signal={result[\"signal\"]}')
else:
    print('CSV not found')
"
```
Expected: prints signal result (may differ from default params)

- [ ] **Step 5: Commit**

```bash
git add harness-engineering-py/backend/app/backtest_albrooks/engine/runner.py
git commit -m "feat: enhance run_signal with config_overrides and dict return

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: 更新后端数据模型 (schemas.py)

**Files:**
- Modify: `harness-engineering-py/backend/app/models/schemas.py`

- [ ] **Step 1: 修改 StockDiagnosis 和 StockAnalyzeRequest**

将 `schemas.py` 中 `StockDiagnosis` 类（第53-62行）替换为：

```python
class StockDiagnosis(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None  # 板块代码（如果是按板块分析）
    days: int = 90
    strategy: str = ""  # 策略 ID，如 "ema_pullback"
    strategyConfig: dict = {}  # 用户覆盖的策略配置
    skills: List[str] = []  # 保留兼容，不再使用
    skillNames: List[str] = []  # 保留兼容，不再使用
    initialPrompt: str = ""  # 保留兼容，不再使用
    results: List[DiagnosisResult] = []
    successCount: int = 0
    failedCount: int = 0
```

将 `StockAnalyzeRequest` 类（第114-120行）替换为：

```python
class StockAnalyzeRequest(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None  # 板块代码，如 BK1036（与 codes 互斥，优先 sector）
    days: int = 90
    strategy: Optional[str] = None  # 策略 ID
    strategyConfig: Optional[dict] = None  # 策略配置覆盖
    skills: List[str] = []  # 保留兼容，不再使用
    sessionId: Optional[str] = None
    model: Optional[str] = None  # 保留兼容，不再使用
```

同时更新 `DiagnosisResult.conclusion` 的注释（第41行）：
```python
    conclusion: Optional[str] = None  # "买入" | "观望" | None(失败)
```

- [ ] **Step 2: 验证模型语法正确**

Run: `cd harness-engineering-py/backend && python -c "from app.models.schemas import StockDiagnosis, StockAnalyzeRequest; d = StockDiagnosis(strategy='ema_pullback', strategyConfig={'ema_period': 30}); print(f'strategy={d.strategy}, config={d.strategyConfig}')"`
Expected: `strategy=ema_pullback, config={'ema_period': 30}`

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/backend/app/models/schemas.py
git commit -m "feat: add strategy/strategyConfig fields to stock diagnosis models

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: 改造后端 _run_analysis 和新增 /api/stock/strategies

**Files:**
- Modify: `harness-engineering-py/backend/app/routers/stock.py`

- [ ] **Step 1: 添加策略注册表导入和辅助函数**

在 `stock.py` 顶部 import 区域，在现有 import 之后添加：

```python
from app.backtest_albrooks.strategies.registry import STRATEGY_REGISTRY
from app.backtest_albrooks.engine.runner import run_signal
```

在 `_parse_conclusion` 函数之后、`_build_prompt` 函数之前，添加 `_validate_config` 辅助函数：

```python
def _validate_config(strategy_id: str, config: dict) -> dict:
    """校验并转换用户配置：确保类型正确、值在合法范围内。"""
    entry = STRATEGY_REGISTRY.get(strategy_id)
    if entry is None:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy_id}")

    schema = entry["configSchema"]
    validated: dict = {}
    for item in schema:
        key = item["key"]
        if key in config:
            raw = config[key]
            try:
                if item["type"] == "int":
                    val = int(raw)
                elif item["type"] == "float":
                    val = float(raw)
                else:
                    val = raw
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for {key}: {raw}"
                )
            # 范围检查
            if "min" in item and val < item["min"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"{key} must be >= {item['min']}, got {val}"
                )
            if "max" in item and val > item["max"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"{key} must be <= {item['max']}, got {val}"
                )
            validated[key] = val
    return validated
```

- [ ] **Step 2: 添加 GET /api/stock/strategies 端点**

在 `@router.get("/stock/sectors")` 之前添加：

```python
@router.get("/stock/strategies")
async def list_strategies():
    """返回所有可用策略列表，供前端下拉选择。"""
    strategies = []
    for entry in STRATEGY_REGISTRY.values():
        strategies.append({
            "id": entry["id"],
            "name": entry["name"],
            "description": entry["description"],
            "configSchema": entry["configSchema"],
        })
    return {"strategies": strategies}
```

- [ ] **Step 3: 修改 _run_analysis 函数签名和实现**

将 `_run_analysis` 函数签名从：
```python
async def _run_analysis(
    analysis_id: str,
    codes: list[str],
    days: int,
    skills: list[str],
    session_id: str,
    model: str = "",
    sector: str = "",
) -> None:
```

改为：
```python
async def _run_analysis(
    analysis_id: str,
    codes: list[str],
    days: int,
    strategy: str,
    strategy_config: dict,
    session_id: str,
    sector: str = "",
) -> None:
```

然后替换函数体（第226-383行）为：

```python
    import pandas as pd
    from a_stock_client import AStockClient

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

            # 保存 K 线数据到 data/worktrees/session-{sessionId}/kline/{code}_{start}_{end}.csv
            kline_dir = WORKTREES_DIR / session_id / "kline"
            kline_dir.mkdir(parents=True, exist_ok=True)
            kline_filename = f"{code}_{start_date}_{end_date}.csv"
            kline_path = kline_dir / kline_filename
            df_to_save = df.copy()
            if "date" in df_to_save.columns:
                df_to_save["date"] = pd.to_datetime(df_to_save["date"]).dt.strftime("%Y-%m-%d")
            df_to_save.to_csv(str(kline_path), index=False, encoding="utf-8-sig")
            # 相对路径：worktrees/session-{sessionId}/kline/{filename}
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
                conclusion=conclusion,
                reason="",  # 策略模式无文本理由
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
        strategy=strategy,
        strategyConfig=strategy_config,
        skills=[],
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

- [ ] **Step 4: 修改 POST /api/stock/analyze 请求处理**

在 `start_analysis` 函数中（第393行起），在函数体开头添加策略校验，并修改 `_run_analysis` 调用。

在 `body.sessionId` 校验逻辑之前添加：

```python
    # 校验策略
    strategy = body.strategy or "ema_pullback"
    if strategy not in STRATEGY_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")
    strategy_config = _validate_config(strategy, body.strategyConfig or {})
```

将 `_run_analysis` 调用从：
```python
    task = asyncio.ensure_future(
        _run_analysis(
            analysis_id=analysis_id,
            codes=codes,
            days=body.days,
            skills=body.skills,
            session_id=session.id,
            model=body.model or "",
            sector=body.sector or "",
        )
    )
```

改为：
```python
    task = asyncio.ensure_future(
        _run_analysis(
            analysis_id=analysis_id,
            codes=codes,
            days=body.days,
            strategy=strategy,
            strategy_config=strategy_config,
            session_id=session.id,
            sector=body.sector or "",
        )
    )
```

- [ ] **Step 5: 验证端点语法正确**

Run: `cd harness-engineering-py/backend && python -c "from app.routers.stock import router; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add harness-engineering-py/backend/app/routers/stock.py
git commit -m "feat: replace LLM analysis with strategy signal in stock diagnosis

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: 更新前端类型定义

**Files:**
- Modify: `harness-engineering-py/frontend/src/types/stock.ts`

- [ ] **Step 1: 添加策略类型，更新 StockDiagnosis**

将 `stock.ts` 完整替换为：

```typescript
export interface DiagnosisResult {
  code: string
  name: string
  conclusion: "买入" | "观望" | null
  reason: string
  close: number | null
  open: number | null
  pct_chg: number | null
  ema20: number | null
  error?: string
  source?: string
  klinePath?: string
  klineDate?: string
}

export interface StrategyConfigItem {
  key: string
  label: string
  type: "int" | "float"
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

export interface StockDiagnosis {
  codes: string[]
  sector?: string
  days: number
  strategy: string
  strategyConfig: Record<string, any>
  skills: string[]
  skillNames: string[]
  initialPrompt: string
  results: DiagnosisResult[]
  successCount: number
  failedCount: number
}

export interface SectorInfo {
  code: string
  name: string
  type?: string  // "行业" | "概念"
}

export interface StockSearchResult {
  code: string
  name: string
  type: string
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit src/types/stock.ts 2>&1 | head -10`
Expected: No errors related to stock.ts

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/frontend/src/types/stock.ts
git commit -m "feat: add strategy types and update diagnosis conclusion to buy/hold

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: 更新 useStockAnalysis composable

**Files:**
- Modify: `harness-engineering-py/frontend/src/composables/useStockAnalysis.ts`

- [ ] **Step 1: 修改 startAnalysis 参数和 POST body**

将 `startAnalysis` 函数签名（第54行）从：
```typescript
  async function startAnalysis(codes: string[], days: number, skills: string[], existingSessionId?: string, model?: string) {
```

改为：
```typescript
  async function startAnalysis(codes: string[], days: number, strategy: string, strategyConfig: Record<string, any>, existingSessionId?: string) {
```

将 POST body（第68-74行）从：
```typescript
        body: JSON.stringify({
          codes,
          days,
          skills,
          sessionId: existingSessionId || undefined,
          model: model || undefined,
        }),
```

改为：
```typescript
        body: JSON.stringify({
          codes,
          days,
          strategy,
          strategyConfig,
          sessionId: existingSessionId || undefined,
        }),
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit 2>&1 | grep -i "useStockAnalysis" | head -5`
Expected: No errors for useStockAnalysis.ts

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/frontend/src/composables/useStockAnalysis.ts
git commit -m "feat: update useStockAnalysis with strategy and config params

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: 改造 StockInput.vue — 策略下拉 + 配置折叠面板

**Files:**
- Modify: `harness-engineering-py/frontend/src/components/stock/StockInput.vue`

- [ ] **Step 1: 修改 props 和 emits**

将 `<script setup>` 中的 props（第177-183行）替换为：

```typescript
import type { StrategyInfo, StrategyConfigItem, StockSearchResult } from '@/types/stock'

const props = defineProps<{
  modelValue: string[]
  days: number
  strategyList: StrategyInfo[]
  selectedStrategy: string
  strategyConfig: Record<string, any>
  isAnalyzing: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [codes: string[]]
  'update:days': [days: number]
  'update:selectedStrategy': [strategy: string]
  'update:strategyConfig': [config: Record<string, any>]
  start: []
  clear: []
}>()
```

- [ ] **Step 2: 添加策略配置面板状态**

在 script 区域，`showDropdown` 之后添加：

```typescript
// 策略配置面板
const configExpanded = ref(false)
const currentConfigValues = ref<Record<string, any>>({})

function getCurrentStrategy(): StrategyInfo | undefined {
  return props.strategyList.find(s => s.id === props.selectedStrategy)
}

function onStrategyChange(strategyId: string) {
  emit('update:selectedStrategy', strategyId)
  // 切换策略时重置配置为默认值
  const strategy = props.strategyList.find(s => s.id === strategyId)
  if (strategy) {
    const defaults: Record<string, any> = {}
    strategy.configSchema.forEach(item => {
      defaults[item.key] = item.default
    })
    currentConfigValues.value = defaults
    emit('update:strategyConfig', { ...defaults })
  }
}

function resetConfig() {
  const strategy = getCurrentStrategy()
  if (strategy) {
    const defaults: Record<string, any> = {}
    strategy.configSchema.forEach(item => {
      defaults[item.key] = item.default
    })
    currentConfigValues.value = { ...defaults }
    emit('update:strategyConfig', { ...defaults })
  }
}

function onConfigChange(key: string, value: any) {
  currentConfigValues.value[key] = value
  emit('update:strategyConfig', { ...currentConfigValues.value })
}

function getSummary(config: Record<string, any>): string {
  const strategy = getCurrentStrategy()
  if (!strategy || !strategy.configSchema || strategy.configSchema.length === 0) return ''
  // 取前3个参数作为摘要
  return strategy.configSchema.slice(0, 3)
    .map(item => {
      const val = config[item.key] ?? item.default
      return `${item.label.split(/[（(]/)[0]}${val}`
    })
    .join(' · ')
}
```

- [ ] **Step 3: 替换模板中的 Skills 下拉为策略下拉 + 配置面板**

将模板中 options-row 区域（第117-166行）替换为：

```vue
    <div class="input-row options-row">
      <div class="option-item">
        <label class="option-label">日期范围</label>
        <el-select
          :model-value="days"
          placeholder="选择天数"
          style="width: 140px"
          @update:model-value="$emit('update:days', $event)"
        >
          <el-option label="近30天" :value="30" />
          <el-option label="近60天" :value="60" />
          <el-option label="近90天" :value="90" />
          <el-option label="近180天" :value="180" />
        </el-select>
      </div>

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

      <el-button
        type="primary"
        :loading="isAnalyzing"
        :disabled="modelValue.length === 0 || !selectedStrategy"
        @click="$emit('start')"
      >
        {{ isAnalyzing ? '分析中...' : '开始诊股' }}
      </el-button>

      <el-button
        v-if="modelValue.length > 0 && !isAnalyzing"
        @click="$emit('clear')"
      >
        清空
      </el-button>
    </div>

    <!-- 策略配置折叠面板 -->
    <div v-if="selectedStrategy && getCurrentStrategy()" class="strategy-config-panel">
      <div class="config-header" @click="configExpanded = !configExpanded">
        <div class="config-summary">
          <span class="config-strategy-name">{{ getCurrentStrategy()?.name }}</span>
          <span class="config-summary-text">{{ getSummary(currentConfigValues) }}</span>
        </div>
        <div class="config-actions">
          <el-button size="small" text @click.stop="resetConfig">重置默认</el-button>
          <el-icon :class="{ 'is-expanded': configExpanded }" class="config-arrow">
            <ArrowDown />
          </el-icon>
        </div>
      </div>
      <div v-show="configExpanded" class="config-body">
        <div
          v-for="item in getCurrentStrategy()?.configSchema || []"
          :key="item.key"
          class="config-item"
        >
          <label class="config-label">{{ item.label }}</label>
          <el-input-number
            v-if="item.type === 'int'"
            :model-value="currentConfigValues[item.key] ?? item.default"
            :min="item.min"
            :max="item.max"
            :step="item.step || 1"
            size="small"
            controls-position="right"
            style="width: 160px"
            @update:model-value="onConfigChange(item.key, $event)"
          />
          <el-input-number
            v-else-if="item.type === 'float'"
            :model-value="currentConfigValues[item.key] ?? item.default"
            :min="item.min"
            :max="item.max"
            :step="item.step || 0.01"
            :precision="3"
            size="small"
            controls-position="right"
            style="width: 160px"
            @update:model-value="onConfigChange(item.key, $event)"
          />
          <span class="config-desc">{{ item.description }}</span>
        </div>
      </div>
    </div>
```

- [ ] **Step 4: 添加 ArrowDown 图标导入**

在 `<script setup>` 顶部的 import 中，将：
```typescript
import { Search, Loading } from '@element-plus/icons-vue'
```
改为：
```typescript
import { Search, Loading, ArrowDown } from '@element-plus/icons-vue'
```

- [ ] **Step 5: 添加配置面板样式**

在 `<style scoped>` 末尾添加：

```css
/* 策略配置折叠面板 */
.strategy-config-panel {
  margin-top: 4px;
  margin-bottom: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  overflow: hidden;
}
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.config-header:hover {
  background: var(--el-fill-color-light);
}
.config-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.config-strategy-name {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}
.config-summary-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.config-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.config-arrow {
  transition: transform 0.2s;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
.config-arrow.is-expanded {
  transform: rotate(180deg);
}
.config-body {
  padding: 8px 14px 14px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
}
.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.config-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  min-width: 110px;
}
.config-desc {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

- [ ] **Step 6: 验证 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit 2>&1 | grep -i "StockInput" | head -5`
Expected: No errors for StockInput.vue

- [ ] **Step 7: Commit**

```bash
git add harness-engineering-py/frontend/src/components/stock/StockInput.vue
git commit -m "feat: replace skills dropdown with strategy selector and collapsible config panel

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: 更新 StockResultTable.vue — 两态结论

**Files:**
- Modify: `harness-engineering-py/frontend/src/components/stock/StockResultTable.vue`

- [ ] **Step 1: 替换结论列的图标和标签逻辑**

将结论列模板（第27-52行）替换为：

```vue
      <el-table-column label="结论" width="90">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result">
            <el-tag
              :type="conclusionTagType(row.result.conclusion)"
              size="small"
            >
              <el-icon style="margin-right: 2px; vertical-align: middle;">
                <CircleCheck v-if="row.result.conclusion === '买入'" />
                <Clock v-else />
              </el-icon>
              {{ row.result.conclusion || '—' }}
            </el-tag>
          </template>
          <template v-else-if="row.status === 'analyzing'">
            <el-tag type="info" size="small">分析中</el-tag>
          </template>
          <template v-else-if="row.status === 'pending'">
            <el-tag type="info" size="small">等待</el-tag>
          </template>
          <template v-else>
            <el-tag type="danger" size="small">失败</el-tag>
          </template>
        </template>
      </el-table-column>
```

- [ ] **Step 2: 替换图标导入**

将 `<script setup>` 中的图标导入从：
```typescript
import { Top, Bottom, Minus } from '@element-plus/icons-vue'
```
改为：
```typescript
import { CircleCheck, Clock } from '@element-plus/icons-vue'
```

- [ ] **Step 3: 更新 conclusionTagType 函数**

将 `conclusionTagType` 函数（第170-175行）替换为：

```typescript
function conclusionTagType(conclusion: string | null): 'success' | 'danger' | 'warning' | 'info' {
  if (conclusion === '买入') return 'success'
  if (conclusion === '观望') return 'warning'
  return 'info'
}
```

- [ ] **Step 4: 验证 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit 2>&1 | grep -i "StockResultTable" | head -5`
Expected: No errors for StockResultTable.vue

- [ ] **Step 5: Commit**

```bash
git add harness-engineering-py/frontend/src/components/stock/StockResultTable.vue
git commit -m "feat: update conclusion display to two-state buy/hold with new icons

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 9: 更新 StockView.vue — 策略状态管理和传递

**Files:**
- Modify: `harness-engineering-py/frontend/src/views/StockView.vue`

- [ ] **Step 1: 替换状态变量和导入**

将 `<script setup>` 中的状态变量和导入修改。

将 import 从：
```typescript
import type { Skill } from '@/types'
```
改为：
```typescript
import type { StrategyInfo } from '@/types/stock'
```

将状态变量从：
```typescript
const skillList = ref<Skill[]>([])
const selectedSkills = ref<string[]>([])
```
改为：
```typescript
const strategyList = ref<StrategyInfo[]>([])
const selectedStrategy = ref('ema_pullback')
const strategyConfig = ref<Record<string, any>>({})
```

- [ ] **Step 2: 替换 onMounted 中的 skills 加载**

将 onMounted（第96-103行）从：
```typescript
onMounted(async () => {
  try {
    const res = await fetch('/api/skills')
    if (res.ok) {
      const data = await res.json()
      skillList.value = data.skills || []
    }
  } catch {}

  await chatStore.loadSessions()
  loadViewingRecord()
})
```
改为：
```typescript
onMounted(async () => {
  try {
    const res = await fetch('/api/stock/strategies')
    if (res.ok) {
      const data = await res.json()
      strategyList.value = data.strategies || []
      // 初始化第一个策略的默认配置
      if (strategyList.value.length > 0) {
        const defaults: Record<string, any> = {}
        strategyList.value[0].configSchema.forEach(item => {
          defaults[item.key] = item.default
        })
        strategyConfig.value = defaults
      }
    }
  } catch {}

  await chatStore.loadSessions()
  loadViewingRecord()
})
```

- [ ] **Step 3: 替换 StockInput 的 props 绑定**

将模板中的 `StockInput`（第15-23行）从：
```vue
      <StockInput
        v-model="codes"
        v-model:days="days"
        :skills="skillList"
        v-model:selected-skills="selectedSkills"
        :is-analyzing="isAnalyzing"
        @start="handleStart"
        @clear="handleClear"
      />
```
改为：
```vue
      <StockInput
        v-model="codes"
        v-model:days="days"
        :strategy-list="strategyList"
        v-model:selected-strategy="selectedStrategy"
        v-model:strategy-config="strategyConfig"
        :is-analyzing="isAnalyzing"
        @start="handleStart"
        @clear="handleClear"
      />
```

- [ ] **Step 4: 替换 handleStart**

将 `handleStart` 函数（第159-168行）从：
```typescript
async function handleStart() {
  viewingRecord.value = null
  loadedSessionId.value = null
  try {
    await startAnalysis(codes.value, days.value, selectedSkills.value, undefined, chatStore.model || undefined)
    await chatStore.loadSessions()
  } catch (err: any) {
    ElMessage.error(err?.message || '分析启动失败，请重试')
  }
}
```
改为：
```typescript
async function handleStart() {
  viewingRecord.value = null
  loadedSessionId.value = null
  try {
    await startAnalysis(codes.value, days.value, selectedStrategy.value, strategyConfig.value)
    await chatStore.loadSessions()
  } catch (err: any) {
    ElMessage.error(err?.message || '分析启动失败，请重试')
  }
}
```

- [ ] **Step 5: 替换 loadViewingRecord 中的旧字段引用**

将 `loadViewingRecord` 中的：
```typescript
    selectedSkills.value = session.diagnosis.skills || []
```
改为：
```typescript
    selectedStrategy.value = session.diagnosis.strategy || 'ema_pullback'
    strategyConfig.value = session.diagnosis.strategyConfig || {}
```

- [ ] **Step 6: 验证 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit 2>&1 | grep -i "StockView" | head -5`
Expected: No errors for StockView.vue

- [ ] **Step 7: Commit**

```bash
git add harness-engineering-py/frontend/src/views/StockView.vue
git commit -m "feat: wire strategy selection and config through StockView

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 10: 端到端验证

- [ ] **Step 1: 启动后端并验证 API**

```bash
cd harness-engineering-py/backend && python -c "
import asyncio
from app.backtest_albrooks.strategies.registry import STRATEGY_REGISTRY
from app.backtest_albrooks.engine.runner import run_signal

# 1. 验证策略注册表
print('Strategies:', list(STRATEGY_REGISTRY.keys()))

# 2. 验证 run_signal
import os
csv_file = 'D:/codes/harness-engineering-mid/harness-engineering-mid/sh603650_2026-03-30_2026-06-28.csv'
if os.path.exists(csv_file):
    result = run_signal(csv_file)
    print(f'signal={result[\"signal\"]}, date={result[\"date\"]}')
    result2 = run_signal(csv_file, config_overrides={'ema_period': 50})
    print(f'with ema_period=50: signal={result2[\"signal\"]}')
else:
    print('CSV not found, skipping signal test')

# 3. 验证模型
from app.models.schemas import StockDiagnosis, StockAnalyzeRequest
d = StockDiagnosis(strategy='ema_pullback', strategyConfig={'ema_period': 30})
print(f'StockDiagnosis OK: strategy={d.strategy}')
r = StockAnalyzeRequest(codes=['sh600519'], strategy='ema_pullback', strategyConfig={'ema_period': 30})
print(f'StockAnalyzeRequest OK: strategy={r.strategy}')
print('All checks passed!')
"
```
Expected: All checks passed!

- [ ] **Step 2: 验证前端 TypeScript 编译**

Run: `cd harness-engineering-py/frontend && npx vue-tsc --noEmit 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: end-to-end verification of strategy signal mode

Co-Authored-By: Claude <noreply@anthropic.com>"
```
