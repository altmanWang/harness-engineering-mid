# Stock Backtest Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strategy backtest visualization to stock diagnosis — click "回测" on a diagnosed stock, run `run_backtest()`, show K-line with buy/sell markers + return curve + capital curve in a dialog.

**Architecture:** Extend `DiagnosisResult` with `backtestBarsPath`/`backtestSummaryPath`. Add 3 API endpoints (POST trigger, GET bars, GET summary). Modify `run_backtest()` to compute summary JSON alongside the existing CSV output. New `BacktestDialog.vue` renders 4 summary cards + 3 ECharts charts with dataZoom sync.

**Tech Stack:** Python/FastAPI (backend), Vue 3 + Element Plus + ECharts 5 (frontend)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/app/models/schemas.py` | Modify | Add `BacktestSummary`, `BacktestBar`, extend `DiagnosisResult` |
| `backend/app/backtest_albrooks/engine/runner.py` | Modify | Extend `run_backtest()` with `config_overrides` + summary JSON output |
| `backend/app/routers/stock.py` | Modify | Add 3 backtest endpoints + `_run_backtest()` |
| `frontend/src/types/stock.ts` | Modify | Add `BacktestSummary`, `BacktestBar` interfaces |
| `frontend/src/composables/useBacktest.ts` | Create | Fetch/cache backtest data |
| `frontend/src/components/stock/BacktestDialog.vue` | Create | Dialog with summary cards + 3 ECharts charts |
| `frontend/src/components/stock/StockResultTable.vue` | Modify | Add "回测" button in operation column |
| `frontend/src/views/StockView.vue` | Modify | Integrate BacktestDialog |

---

### Task 1: Backend — Add Pydantic models

**Files:**
- Modify: `harness-engineering-py/backend/app/models/schemas.py`

- [ ] **Step 1: Add BacktestSummary, BacktestBar models and extend DiagnosisResult**

Add after `DiagnosisResult` class (after line 50):

```python
class BacktestSummary(BaseModel):
    stock_code: str
    stock_name: str
    initial_capital: float = 20000.0
    final_capital: float = 0.0
    total_return: float = 0.0       # 总收益率 (%)
    max_drawdown: float = 0.0       # 最大回撤 (%)
    win_rate: float = 0.0           # 胜率 (%)
    trade_count: int = 0            # 交易次数


class BacktestBar(BaseModel):
    date: str
    stock_name: str = ""
    open: float = 0.0
    close: float = 0.0
    signal: Optional[str] = None    # "买入" | "卖出" | "持有" | "观望"
    cost: Optional[float] = None
    profit: Optional[float] = None
    capital: float = 0.0
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
```

Modify `DiagnosisResult` to add two new fields after `klineDate`:

```python
class DiagnosisResult(BaseModel):
    code: str
    name: str = ""
    conclusion: Optional[str] = None
    reason: str = ""
    close: Optional[float] = None
    open: Optional[float] = None
    pct_chg: Optional[float] = None
    ema20: Optional[float] = None
    error: Optional[str] = None
    source: Optional[str] = None
    klinePath: Optional[str] = None
    klineDate: Optional[str] = None
    backtestBarsPath: Optional[str] = None     # 回测 bars CSV 相对路径
    backtestSummaryPath: Optional[str] = None  # 回测 summary JSON 相对路径
```

- [ ] **Step 2: Verify imports work**

```bash
cd harness-engineering-py/backend && python -c "from app.models.schemas import BacktestSummary, BacktestBar, DiagnosisResult; d = DiagnosisResult(code='test', backtestBarsPath='a.csv'); print(d.model_dump())"
```

Expected: prints dict with `backtestBarsPath: 'a.csv'`, `backtestSummaryPath: None`.

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/backend/app/models/schemas.py
git commit -m "feat: add BacktestSummary, BacktestBar models and extend DiagnosisResult"
```

---

### Task 2: Backend — Extend run_backtest() with summary JSON output

**Files:**
- Modify: `harness-engineering-py/backend/app/backtest_albrooks/engine/runner.py`

- [ ] **Step 1: Add config_overrides parameter and summary computation**

Replace the `run_backtest` function signature and body:

```python
import json


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
```

- [ ] **Step 2: Verify run_backtest works**

```bash
cd harness-engineering-py/backend && python -c "
from app.backtest_albrooks.engine.runner import run_backtest
result = run_backtest('D:/codes/harness-engineering-mid/harness-engineering-mid/sh603650_2026-03-30_2026-06-28.csv')
print(result)
"
```

Expected: prints dict with `bars_csv`, `summary_json`, `summary` paths and data. Verify CSV and JSON files exist.

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/backend/app/backtest_albrooks/engine/runner.py
git commit -m "feat: extend run_backtest with config_overrides and summary JSON output"
```

---

### Task 3: Backend — Add backtest API endpoints

**Files:**
- Modify: `harness-engineering-py/backend/app/routers/stock.py`

- [ ] **Step 1: Add import for run_backtest and BacktestSummary**

Change line 25 from:
```python
from app.backtest_albrooks.engine.runner import run_signal
```
to:
```python
from app.backtest_albrooks.engine.runner import run_signal, run_backtest
```

Add `BacktestSummary` to the schemas import on line 18-21:
```python
from app.models.schemas import (
    StockAnalyzeRequest, StockDiagnosis, DiagnosisResult,
    ChatSession, ChatMessage, BacktestSummary,
)
```

- [ ] **Step 2: Add GET /api/stock/backtest/summary/{session_id}/{code}**

Add before the `_parse_search_table` function (before line 718):

```python
@router.get("/stock/backtest/summary/{session_id}/{code}")
async def get_backtest_summary(session_id: str, code: str):
    """读取缓存的回测汇总 JSON."""
    import json as _json

    backtest_dir = WORKTREES_DIR / session_id / "backtest"
    summary_path = backtest_dir / f"{code}_summary.json"

    if not summary_path.exists():
        raise HTTPException(status_code=404, detail=f"Backtest summary not found for {code}")

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read backtest summary: {e}")
```

- [ ] **Step 3: Add GET /api/stock/backtest/bars/{session_id}/{code}**

Add after the summary endpoint:

```python
@router.get("/stock/backtest/bars/{session_id}/{code}")
async def get_backtest_bars(session_id: str, code: str):
    """读取缓存的回测 bars CSV，返回 JSON."""
    import csv as _csv

    backtest_dir = WORKTREES_DIR / session_id / "backtest"
    bars_path = backtest_dir / f"{code}_bars.csv"

    if not bars_path.exists():
        raise HTTPException(status_code=404, detail=f"Backtest bars not found for {code}")

    bars: list[dict] = []
    try:
        with open(bars_path, "r", encoding="utf-8-sig") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                bars.append({
                    "date": (row.get("date") or "").strip(),
                    "stock_name": (row.get("stock_name") or "").strip(),
                    "open": float(row.get("open", 0) or 0),
                    "close": float(row.get("close", 0) or 0),
                    "signal": (row.get("signal") or "").strip() or None,
                    "cost": float(row.get("cost", 0) or 0) if row.get("cost", "").strip() else None,
                    "profit": float(row.get("profit", 0) or 0) if row.get("profit", "").strip() else None,
                    "capital": float(row.get("capital", 0) or 0),
                    "stop_loss": float(row.get("stop_loss", 0) or 0) if row.get("stop_loss", "").strip() else None,
                    "target_price": float(row.get("target_price", 0) or 0) if row.get("target_price", "").strip() else None,
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read backtest bars: {e}")

    return {"code": code, "bars": bars}
```

- [ ] **Step 4: Add POST /api/stock/backtest**

Add after the bars endpoint:

```python
class BacktestTriggerRequest(BaseModel):
    code: str
    sessionId: str
    strategy: str = "ema_pullback"
    strategyConfig: dict = {}


@router.post("/stock/backtest")
async def trigger_backtest(body: BacktestTriggerRequest):
    """触发回测：调用 run_backtest，保存结果，返回 summary."""
    session = await get_session(body.sessionId)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 查找 K 线 CSV
    kline_dir = WORKTREES_DIR / body.sessionId / "kline"
    if not kline_dir.exists():
        raise HTTPException(status_code=404, detail="K-line data not found for session")

    csv_files = sorted(kline_dir.glob(f"{body.code}_*.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail=f"No K-line file for {body.code}")

    kline_path = str(csv_files[0])

    # 回测输出目录
    backtest_dir = WORKTREES_DIR / body.sessionId / "backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)

    # 校验策略配置
    strategy_config = _validate_config(body.strategy, body.strategyConfig or {})

    # 运行回测（同步，在线程池中执行）
    import concurrent.futures as _futures
    import asyncio as _asyncio

    loop = _asyncio.get_running_loop()
    try:
        with _futures.ThreadPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(
                pool,
                lambda: run_backtest(kline_path, output_dir=str(backtest_dir), config_overrides=strategy_config),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")

    # 回填 DiagnosisResult
    if session.diagnosis:
        for r in session.diagnosis.results:
            if r.code == body.code:
                r.backtestBarsPath = f"worktrees/{body.sessionId}/backtest/{body.code}_bars.csv"
                r.backtestSummaryPath = f"worktrees/{body.sessionId}/backtest/{body.code}_summary.json"
                break
        await save_session(session)

    return result["summary"]
```

- [ ] **Step 5: Verify API endpoints**

Start backend:
```bash
cd harness-engineering-py/backend && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Test POST (use an existing sessionId from a prior diagnosis):
```bash
curl -X POST http://localhost:8080/api/stock/backtest \
  -H "Content-Type: application/json" \
  -d '{"code":"603650","sessionId":"<real-session-id>","strategy":"ema_pullback","strategyConfig":{}}'
```
Expected: returns summary JSON.

Test GET summary:
```bash
curl http://localhost:8080/api/stock/backtest/summary/<sessionId>/603650
```
Expected: returns same summary JSON.

Test GET bars:
```bash
curl http://localhost:8080/api/stock/backtest/bars/<sessionId>/603650
```
Expected: returns `{"code":"603650","bars":[...]}`.

- [ ] **Step 6: Commit**

```bash
git add harness-engineering-py/backend/app/routers/stock.py
git commit -m "feat: add backtest API endpoints (POST trigger, GET bars/summary)"
```

---

### Task 4: Frontend — Add TypeScript types

**Files:**
- Modify: `harness-engineering-py/frontend/src/types/stock.ts`

- [ ] **Step 1: Add BacktestSummary and BacktestBar interfaces**

Add after the `StockSearchResult` interface:

```typescript
export interface BacktestSummary {
  stock_code: string
  stock_name: string
  initial_capital: number
  final_capital: number
  total_return: number
  max_drawdown: number
  win_rate: number
  trade_count: number
}

export interface BacktestBar {
  date: string
  stock_name: string
  open: number
  close: number
  signal: string | null
  cost: number | null
  profit: number | null
  capital: number
  stop_loss: number | null
  target_price: number | null
}
```

Also add `backtestBarsPath` and `backtestSummaryPath` to `DiagnosisResult`:

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
  backtestBarsPath?: string
  backtestSummaryPath?: string
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd harness-engineering-py/frontend && npx vue-tsc --noEmit src/types/stock.ts
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/frontend/src/types/stock.ts
git commit -m "feat: add BacktestSummary, BacktestBar types and extend DiagnosisResult"
```

---

### Task 5: Frontend — Create useBacktest composable

**Files:**
- Create: `harness-engineering-py/frontend/src/composables/useBacktest.ts`

- [ ] **Step 1: Write the composable**

```typescript
import { ref } from 'vue'
import type { BacktestSummary, BacktestBar, DiagnosisResult } from '@/types/stock'

export function useBacktest() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const summary = ref<BacktestSummary | null>(null)
  const bars = ref<BacktestBar[]>([])

  async function fetchBacktest(result: DiagnosisResult, sessionId: string) {
    // Already cached — fetch directly
    if (result.backtestSummaryPath && result.backtestBarsPath) {
      loading.value = true
      error.value = null
      try {
        const [summaryRes, barsRes] = await Promise.all([
          fetch(`/api/stock/backtest/summary/${sessionId}/${result.code}`),
          fetch(`/api/stock/backtest/bars/${sessionId}/${result.code}`),
        ])

        if (!summaryRes.ok) throw new Error('Failed to load backtest summary')
        if (!barsRes.ok) throw new Error('Failed to load backtest bars')

        summary.value = await summaryRes.json()
        const barsData = await barsRes.json()
        bars.value = barsData.bars as BacktestBar[]
      } catch (e: any) {
        error.value = e.message || '加载回测数据失败'
      } finally {
        loading.value = false
      }
      return
    }

    // No cache — trigger backtest
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/stock/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: result.code,
          sessionId,
          strategy: 'ema_pullback',
          strategyConfig: {},
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '回测计算失败')
      }

      summary.value = await res.json()

      // Fetch bars after successful backtest
      const barsRes = await fetch(`/api/stock/backtest/bars/${sessionId}/${result.code}`)
      if (barsRes.ok) {
        const barsData = await barsRes.json()
        bars.value = barsData.bars as BacktestBar[]
      }

      // Update result cache paths for subsequent opens
      result.backtestSummaryPath = `worktrees/${sessionId}/backtest/${result.code}_summary.json`
      result.backtestBarsPath = `worktrees/${sessionId}/backtest/${result.code}_bars.csv`
    } catch (e: any) {
      error.value = e.message || '回测计算失败'
    } finally {
      loading.value = false
    }
  }

  function reset() {
    loading.value = false
    error.value = null
    summary.value = null
    bars.value = []
  }

  return { loading, error, summary, bars, fetchBacktest, reset }
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd harness-engineering-py/frontend && npx vue-tsc --noEmit src/composables/useBacktest.ts
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/frontend/src/composables/useBacktest.ts
git commit -m "feat: add useBacktest composable for backtest API calls"
```

---

### Task 6: Frontend — Create BacktestDialog component

**Files:**
- Create: `harness-engineering-py/frontend/src/components/stock/BacktestDialog.vue`

- [ ] **Step 1: Write the full component**

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="1100px"
    top="3vh"
    destroy-on-close
    @opened="onOpened"
    @closed="onClosed"
  >
    <div v-if="loading" class="bt-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>回测计算中...</span>
    </div>

    <div v-else-if="error" class="bt-error">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>

    <template v-else-if="summary">
      <!-- 汇总卡片 -->
      <div class="bt-summary-cards">
        <div class="bt-card">
          <div class="bt-card-label">总收益率</div>
          <div class="bt-card-value" :class="summary.total_return >= 0 ? 'text-green' : 'text-red'">
            {{ summary.total_return >= 0 ? '+' : '' }}{{ summary.total_return.toFixed(2) }}%
          </div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">最大回撤</div>
          <div class="bt-card-value text-red">-{{ summary.max_drawdown.toFixed(2) }}%</div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">胜率</div>
          <div class="bt-card-value" :class="summary.win_rate >= 50 ? 'text-green' : 'text-orange'">
            {{ summary.win_rate.toFixed(1) }}%
          </div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">交易次数</div>
          <div class="bt-card-value text-default">{{ summary.trade_count }}</div>
        </div>
      </div>

      <!-- K线图 -->
      <div class="bt-chart-section">
        <div class="bt-chart-title">K线图 · 买卖信号</div>
        <div ref="klineChartRef" class="bt-chart kline-chart"></div>
      </div>

      <!-- 底部双图 -->
      <div class="bt-charts-row">
        <div class="bt-chart-section bt-chart-half">
          <div class="bt-chart-title">收益率曲线</div>
          <div ref="returnChartRef" class="bt-chart"></div>
        </div>
        <div class="bt-chart-section bt-chart-half">
          <div class="bt-chart-title">资金变化</div>
          <div ref="capitalChartRef" class="bt-chart"></div>
        </div>
      </div>
    </template>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useBacktest } from '@/composables/useBacktest'
import type { DiagnosisResult } from '@/types/stock'

const props = defineProps<{
  modelValue: boolean
  result: DiagnosisResult | null
  sessionId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => { visible.value = v })
watch(visible, v => { emit('update:modelValue', v) })

const { loading, error, summary, bars, fetchBacktest, reset } = useBacktest()

const title = computed(() => {
  if (!props.result) return '回测详情'
  return `回测详情 — ${props.result.name || props.result.code} (${props.result.code})`
})

const klineChartRef = ref<HTMLDivElement | null>(null)
const returnChartRef = ref<HTMLDivElement | null>(null)
const capitalChartRef = ref<HTMLDivElement | null>(null)

let klineInstance: echarts.ECharts | null = null
let returnInstance: echarts.ECharts | null = null
let capitalInstance: echarts.ECharts | null = null

function onOpened() {
  if (!props.result) return
  fetchBacktest(props.result, props.sessionId).then(() => {
    if (!error.value && bars.value.length > 0) {
      nextTick(() => {
        renderKLineChart()
        renderReturnChart()
        renderCapitalChart()
      })
    }
  })
}

function onClosed() {
  reset()
  disposeCharts()
}

function disposeCharts() {
  klineInstance?.dispose(); klineInstance = null
  returnInstance?.dispose(); returnInstance = null
  capitalInstance?.dispose(); capitalInstance = null
}

function renderKLineChart() {
  if (!klineChartRef.value || bars.value.length === 0) return
  if (klineInstance) klineInstance.dispose()
  klineInstance = echarts.init(klineChartRef.value)

  const dates = bars.value.map(b => b.date)
  const ohlc = bars.value.map(b => [b.open, b.close, b.open, b.close])
  // Use actual high/low from the data if available, else approximate with open/close
  // Note: bars CSV doesn't have high/low, so we approximate
  const ohlcApprox = bars.value.map(b => {
    const o = b.open; const c = b.close
    return [o, c, Math.max(o, c), Math.min(o, c)]
  })
  const volumes = bars.value.map(b => {
    // Approximate volume from cost (cost / close ≈ volume)
    const cost = b.cost || 0
    return cost > 0 ? Math.round(cost / (b.close || 1)) : 0
  })

  // Buy/Sell markers
  const buyMarks = bars.value
    .map((b, i) => b.signal === '买入' ? { coord: [dates[i], ohlcApprox[i][2]], value: '买入' } : null)
    .filter(Boolean) as { coord: [string, number]; value: string }[]
  const sellMarks = bars.value
    .map((b, i) => b.signal === '卖出' ? { coord: [dates[i], ohlcApprox[i][3]], value: '卖出' } : null)
    .filter(Boolean) as { coord: [string, number]; value: string }[]

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    grid: [
      { left: '8%', right: '4%', top: 20, height: '55%' },
      { left: '8%', right: '4%', top: '76%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: true, axisLine: { onZero: false }, gridIndex: 0 },
      { type: 'category', data: dates, boundaryGap: true, axisLabel: { show: false }, axisTick: { show: false }, gridIndex: 1 },
    ],
    yAxis: [
      { type: 'value', scale: true, position: 'left', gridIndex: 0 },
      { type: 'value', scale: true, position: 'left', gridIndex: 1, splitNumber: 3 },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100, bottom: 4 },
    ],
    series: [
      {
        name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlcApprox,
        itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' },
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes.map((vol, i) => {
          const item = ohlcApprox[i]
          return { value: vol, itemStyle: { color: item[1] >= item[0] ? '#ef5350' : '#26a69a' } }
        }),
      },
      {
        name: '买入', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0,
        data: buyMarks.map(m => m.coord),
        symbol: 'triangle', symbolSize: 16, symbolRotate: 0,
        itemStyle: { color: '#16a34a' },
        label: { show: true, formatter: '买', position: 'bottom', color: '#16a34a', fontSize: 10, fontWeight: 'bold' },
      },
      {
        name: '卖出', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0,
        data: sellMarks.map(m => m.coord),
        symbol: 'triangle', symbolSize: 16, symbolRotate: 180,
        itemStyle: { color: '#dc2626' },
        label: { show: true, formatter: '卖', position: 'top', color: '#dc2626', fontSize: 10, fontWeight: 'bold' },
      },
    ],
  }

  klineInstance.setOption(option)
  klineInstance.group = 'backtest-group'
}

function renderReturnChart() {
  if (!returnChartRef.value || bars.value.length === 0 || !summary.value) return
  if (returnInstance) returnInstance.dispose()
  returnInstance = echarts.init(returnChartRef.value)

  const dates = bars.value.map(b => b.date)
  const initialCapital = summary.value.initial_capital
  const returns = bars.value.map(b => {
    const cap = b.capital || initialCapital
    return ((cap / initialCapital) - 1) * 100
  })

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `${p.axisValue}<br/>收益率: ${p.data >= 0 ? '+' : ''}${p.data.toFixed(2)}%`
      },
    },
    grid: { left: '12%', right: '6%', top: 16, bottom: 32 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `${v.toFixed(1)}%` },
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, bottom: 4, height: 20 },
    ],
    series: [
      {
        type: 'line', data: returns, smooth: true, symbol: 'none',
        lineStyle: { color: '#059669', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(5, 150, 105, 0.15)' },
            { offset: 1, color: 'rgba(5, 150, 105, 0.02)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: '#94a3b8', type: 'dashed' },
          data: [{ yAxis: 0, label: { formatter: '0%', color: '#94a3b8' } }],
        },
      },
    ],
  }
  returnInstance.setOption(option)
  returnInstance.group = 'backtest-group'
}

function renderCapitalChart() {
  if (!capitalChartRef.value || bars.value.length === 0 || !summary.value) return
  if (capitalInstance) capitalInstance.dispose()
  capitalInstance = echarts.init(capitalChartRef.value)

  const dates = bars.value.map(b => b.date)
  const capitals = bars.value.map(b => b.capital || summary.value!.initial_capital)
  const initialCapital = summary.value.initial_capital
  const maxCap = Math.max(...capitals, initialCapital)
  const minCap = Math.min(...capitals, initialCapital)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `${p.axisValue}<br/>资金: ¥${p.data.toLocaleString()}`
      },
    },
    grid: { left: '12%', right: '6%', top: 16, bottom: 32 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `¥${(v / 10000).toFixed(1)}万` },
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, bottom: 4, height: 20 },
    ],
    series: [
      {
        type: 'line', data: capitals, smooth: true, symbol: 'none',
        lineStyle: { color: '#3b82f6', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.12)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.02)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: '#94a3b8', type: 'dashed' },
          data: [{ yAxis: initialCapital, label: { formatter: `初始 ¥${(initialCapital / 10000).toFixed(1)}万`, color: '#94a3b8' } }],
        },
        markPoint: {
          data: [
            { type: 'max', name: '最高', symbol: 'pin', symbolSize: 24, itemStyle: { color: '#16a34a' } },
            { type: 'min', name: '最低', symbol: 'pin', symbolSize: 24, itemStyle: { color: '#dc2626' } },
          ],
        },
      },
    ],
  }
  capitalInstance.setOption(option)
  capitalInstance.group = 'backtest-group'

  // Connect dataZoom across all three charts
  echarts.connect('backtest-group')
}

// Resize on window resize
function onResize() {
  klineInstance?.resize()
  returnInstance?.resize()
  capitalInstance?.resize()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})

// Watch for dialog open to attach resize
watch(visible, v => {
  if (v) {
    window.addEventListener('resize', onResize)
  } else {
    window.removeEventListener('resize', onResize)
  }
})
</script>

<style scoped>
.bt-loading,
.bt-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 20px;
  color: #64748b;
  font-size: 15px;
}

.bt-error {
  color: #dc2626;
}

.bt-summary-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.bt-card {
  flex: 1;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 20px;
  text-align: center;
}

.bt-card-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.bt-card-value {
  font-size: 22px;
  font-weight: 700;
}

.text-green { color: #059669; }
.text-red { color: #dc2626; }
.text-orange { color: #d97706; }
.text-default { color: #0F172A; }

.bt-chart-section {
  margin-bottom: 16px;
}

.bt-chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}

.bt-charts-row {
  display: flex;
  gap: 16px;
}

.bt-chart-half {
  flex: 1;
  min-width: 0;
}

.bt-chart {
  width: 100%;
  height: 280px;
}

.kline-chart {
  height: 380px;
}
</style>
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd harness-engineering-py/frontend && npx vue-tsc --noEmit src/components/stock/BacktestDialog.vue
```
Expected: no errors (may have some ECharts type warnings, acceptable).

- [ ] **Step 3: Commit**

```bash
git add harness-engineering-py/frontend/src/components/stock/BacktestDialog.vue
git commit -m "feat: add BacktestDialog with summary cards and 3 ECharts charts"
```

---

### Task 7: Frontend — Add "回测" button to StockResultTable

**Files:**
- Modify: `harness-engineering-py/frontend/src/components/stock/StockResultTable.vue`

- [ ] **Step 1: Add emit for backtest event**

In the `<script setup>` section, add to the existing `defineEmits` or add a new one. Currently the component has no emits. Add after `defineProps`:

```typescript
const emit = defineEmits<{
  backtest: [row: StockItem]
}>()
```

- [ ] **Step 2: Add "回测" button in the operation column**

In the template, in the "操作" column (line 91-103), add a second button after "详情":

```html
<el-table-column label="操作" width="150" align="center" fixed="right">
  <template #default="{ row }">
    <el-button
      v-if="row.status === 'done' && row.result"
      type="primary"
      link
      size="small"
      @click="openKLine(row)"
    >
      详情
    </el-button>
    <el-button
      v-if="row.status === 'done' && row.result"
      type="primary"
      link
      size="small"
      @click="emit('backtest', row)"
    >
      回测
    </el-button>
  </template>
</el-table-column>
```

Note: column width changed from `90` to `150`.

- [ ] **Step 3: Verify component compiles**

```bash
cd harness-engineering-py/frontend && npx vue-tsc --noEmit src/components/stock/StockResultTable.vue
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add harness-engineering-py/frontend/src/components/stock/StockResultTable.vue
git commit -m "feat: add backtest button to StockResultTable operation column"
```

---

### Task 8: Frontend — Integrate BacktestDialog into StockView

**Files:**
- Modify: `harness-engineering-py/frontend/src/views/StockView.vue`

- [ ] **Step 1: Import and add BacktestDialog**

In `<script setup>`, add import:
```typescript
import BacktestDialog from '@/components/stock/BacktestDialog.vue'
```

Add reactive state after existing refs:
```typescript
const backtestVisible = ref(false)
const backtestResult = ref<DiagnosisResult | null>(null)
```

Add handler function:
```typescript
function handleBacktest(row: StockItem) {
  if (!row.result) return
  backtestResult.value = row.result
  backtestVisible.value = true
}
```

- [ ] **Step 2: Add BacktestDialog to template**

Add after the `StockResultTable` block (after line 33):

```html
<BacktestDialog
  v-model="backtestVisible"
  :result="backtestResult"
  :session-id="sessionId || loadedSessionId || ''"
/>
```

- [ ] **Step 3: Wire the backtest event from StockResultTable**

Update the `StockResultTable` usage to listen for the `backtest` event:

```html
<StockResultTable
  v-if="items.length > 0"
  :items="items"
  :session-id="sessionId || loadedSessionId || ''"
  @backtest="handleBacktest"
/>
```

- [ ] **Step 4: Verify full TypeScript compilation**

```bash
cd harness-engineering-py/frontend && npx vue-tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Manual integration test**

1. Start backend: `cd harness-engineering-py/backend && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`
2. Start frontend: `cd harness-engineering-py/frontend && npm run dev`
3. Navigate to `/stock`, run a diagnosis for a stock (e.g. 603650)
4. After diagnosis completes, click "回测" button
5. Verify: loading spinner → summary cards + 3 charts appear
6. Verify: close dialog, click "回测" again → instant load (cached)
7. Verify: K-line chart shows buy/sell markers
8. Verify: return curve and capital curve render correctly

- [ ] **Step 6: Commit**

```bash
git add harness-engineering-py/frontend/src/views/StockView.vue
git commit -m "feat: integrate BacktestDialog into StockView"
```

---

## Edge Cases Covered

| Scenario | Handling |
|----------|----------|
| K-line CSV not found for backtest | `POST /api/stock/backtest` returns 404 |
| Backtest computation fails | Returns 500, frontend shows error in dialog |
| Backtest produces no trades | Summary shows 0 trades, charts render without markers |
| Cached backtest already exists | `backtestSummaryPath` non-null → skip POST, direct GET |
| Session loaded from history | `backtestBarsPath`/`backtestSummaryPath` in result → "回测" button available immediately |
| Dialog closed and reopened | `destroy-on-close` resets state, `reset()` clears data |
| Window resize | All 3 chart instances call `.resize()` |
