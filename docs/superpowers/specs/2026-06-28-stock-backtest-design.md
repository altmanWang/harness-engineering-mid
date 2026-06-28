# 智能诊股 — 策略回测可视化设计

> 创建: 2026-06-28 | 修订: 2026-06-29 | 状态: 已确认

---

## 1. 概述

在现有智能诊股功能基础上，新增**策略回测**能力。利用 `backtest_albrooks` 模块的 `run_backtest()`（backtrader 引擎），对诊股完成的股票进行完整回测，可视化展示 K 线买卖点、收益率曲线和资金变化曲线。

与诊股的 `run_signal()` 不同，`run_backtest()` 运行完整 Cerebro 回测，输出每根 K 线的信号/资金记录（CSV）和汇总指标（JSON）。

## 2. 交互流程

```
诊股完成 → StockResultTable 每行出现"回测"按钮
  → 用户点击"回测"
    → 检查 result.backtestSummaryPath
      ├── 有缓存 → 直接 GET bars + summary → 渲染 BacktestDialog
      └── 无缓存 → POST /api/stock/backtest（显示 loading）
                    → 后端 run_backtest() 输出 CSV + JSON
                    → 回填 result.backtestBarsPath / backtestSummaryPath
                    → 保存 session
                    → 返回 summary → 渲染 BacktestDialog
```

- **触发方式**: 诊股结果表格中"操作"列新增"回测"按钮
- **缓存策略**: 首次点击跑回测，结果 CSV/JSON 存 worktree 目录，路径写入 session JSON，后续秒开
- **数据来源**: `backtest_albrooks` 模块 `--mode backtest`，策略沿用诊股时选择的策略（如 `ema_pullback`）

## 3. 数据模型

### 后端 Pydantic 模型（新增到 `app/models/schemas.py`）

```python
class BacktestSummary(BaseModel):
    stock_code: str
    stock_name: str
    initial_capital: float       # 初始资金 (20000)
    final_capital: float         # 最终资金
    total_return: float          # 总收益率 (%)
    max_drawdown: float          # 最大回撤 (%)
    win_rate: float              # 胜率 (%)
    trade_count: int             # 交易次数


class BacktestBar(BaseModel):
    date: str
    stock_name: str
    open: float
    close: float
    signal: str | None           # "买入" | "卖出" | "持有" | "观望"
    cost: float | None           # 交易成本
    profit: float | None         # 盈亏
    capital: float               # 当日资金
    stop_loss: float | None      # 止损价
    target_price: float | None   # 目标价
```

### DiagnosisResult 扩展

```python
class DiagnosisResult(BaseModel):
    # ... 现有字段不变 ...
    backtestBarsPath: str | None = None     # 回测 bars CSV 相对路径
    backtestSummaryPath: str | None = None  # 回测 summary JSON 相对路径
```

### 文件存储结构

```
data/worktrees/{sessionId}/backtest/
  {code}_bars.csv       ← TradeRecorder.to_csv() 输出
  {code}_summary.json   ← BacktestSummary JSON
```

路径记录到 `data/chat-sessions/session-{sessionId}.json` 的 `diagnosis.results[i].backtestBarsPath` / `backtestSummaryPath`。

### 前端类型（新增到 `types/stock.ts`）

```typescript
interface BacktestSummary {
  stock_code: string
  stock_name: string
  initial_capital: number
  final_capital: number
  total_return: number
  max_drawdown: number
  win_rate: number
  trade_count: number
}

interface BacktestBar {
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

## 4. API 设计

| Method | Path | 说明 |
|--------|------|------|
| `POST` | `/api/stock/backtest` | 触发回测，调用 `run_backtest()` |
| `GET` | `/api/stock/backtest/summary/{sessionId}/{code}` | 获取回测汇总 |
| `GET` | `/api/stock/backtest/bars/{sessionId}/{code}` | 获取逐 bar 数据（图表用） |

### POST /api/stock/backtest

**请求体:**
```json
{
  "code": "603650",
  "sessionId": "abc123",
  "strategy": "ema_pullback",
  "strategyConfig": {}
}
```

**后端流程** (`stock.py`):
1. 从 session worktree 读取已有 K 线 CSV（复用诊股保存的）
2. 调用 `run_backtest(csv_path, config_overrides)` → 输出 `{code}_bars.csv` + `{code}_summary.json` 到 `worktrees/{sessionId}/backtest/`
3. 从 CSV 解析汇总指标，构建 `BacktestSummary`
4. 回填 `DiagnosisResult.backtestBarsPath` / `backtestSummaryPath`
5. 保存 session
6. 返回 `BacktestSummary`

### GET /api/stock/backtest/bars/{sessionId}/{code}

读取 `worktrees/{sessionId}/backtest/{code}_bars.csv`，返回 JSON 数组：

```json
{
  "code": "603650",
  "name": "彤程新材",
  "bars": [
    {
      "date": "2026-03-30",
      "stock_name": "彤程新材",
      "open": 45.50,
      "close": 46.20,
      "signal": null,
      "cost": null,
      "profit": null,
      "capital": 20000.0,
      "stop_loss": null,
      "target_price": null
    }
  ]
}
```

### GET /api/stock/backtest/summary/{sessionId}/{code}

读取 `worktrees/{sessionId}/backtest/{code}_summary.json`，直接返回 JSON。

## 5. 前端组件设计

### 组件树

```
StockResultTable.vue
  └── "操作"列新增"回测"按钮（仅 status === 'done' 时可用）
        └── BacktestDialog.vue  ← 新建（el-dialog）
              ├── 标题栏：股票代码 + 名称
              ├── 汇总指标卡片（4 个）
              ├── K线图（ECharts，~55% 高度）
              │     ├── 蜡烛图 (OHLC)
              │     ├── EMA20 线（橙色折线）
              │     ├── 买入标记 ▲（绿色箭头，买入日最低价下方）
              │     ├── 卖出标记 ▼（红色箭头，卖出日最高价上方）
              │     ├── 成交量柱（下部，红涨绿跌）
              │     └── dataZoom 滑块 + 滚轮缩放
              ├── 底部双图并排（各 ~45% 高度）
              │     ├── 收益率曲线（折线 + 面积填充，0% 参考线）
              │     └── 资金变化曲线（折线，初始资金参考线）
              └── dataZoom 联动（三图同步缩放）
```

### 新增文件

| 文件 | 职责 |
|------|------|
| `components/stock/BacktestDialog.vue` | 回测弹窗容器：loading → 获取数据 → 渲染汇总卡片 + 三个图表 |
| `composables/useBacktest.ts` | 封装回测 API 调用：`fetchBacktest()` / `loading` / `error` / `summary` / `bars` |

### 修改文件

| 文件 | 变更 |
|------|------|
| `components/stock/StockResultTable.vue` | "操作"列新增"回测"按钮，点击 emit `backtest` 事件 |
| `views/StockView.vue` | 集成 BacktestDialog，处理 backtest 事件 |
| `types/stock.ts` | 新增 `BacktestSummary`、`BacktestBar` 接口 |

## 6. 图表设计

### K 线图（中上部，~55%）

| 元素 | 说明 |
|------|------|
| 蜡烛图 | 红涨绿跌（中式配色），占上部 ~70% |
| EMA20 线 | 橙色折线，叠加在蜡烛图上 |
| 买入标记 | 绿色上箭头 ▲，定位在买入日最低价下方，label: "买入" |
| 卖出标记 | 红色下箭头 ▼，定位在卖出日最高价上方，label: "卖出" |
| 成交量柱 | 下部 ~30%，红柱（涨）/ 绿柱（跌） |
| dataZoom | 底部滑块 + 内部滚轮缩放 |
| tooltip | 十字准星，日期/OHLC/EMA20/当日信号 |

基于现有 `KLineChart.vue` 的 ECharts 配置扩展。

### 收益率曲线（左下）

- X 轴：日期
- Y 轴：收益率百分比
- 折线：正值段绿色，负值段红色，下方面积半透明填充
- 0% 参考线（灰色虚线）

### 资金变化曲线（右下）

- X 轴：日期
- Y 轴：资金金额（元）
- 折线：蓝色
- 初始资金参考线（灰色虚线，标记 20000）
- 最高/最低点标记

### 图表联动

三个图通过 ECharts `connect` API 共享 dataZoom 范围，拖动任一图缩放滑块，三图同步。

## 7. 文件变更清单

### 后端

| 文件 | 变更 |
|------|------|
| `app/models/schemas.py` | 新增 `BacktestSummary`、`BacktestBar`；`DiagnosisResult` 新增 `backtestBarsPath`、`backtestSummaryPath` |
| `app/routers/stock.py` | 新增 `POST /api/stock/backtest`、`GET /api/stock/backtest/summary/{sessionId}/{code}`、`GET /api/stock/backtest/bars/{sessionId}/{code}`；新增 `_run_backtest()` 函数 |
| `app/services/session_store.py` | 无需变更（DiagnosisResult 新字段随 ChatSession 自动持久化） |

### 前端

| 文件 | 变更 |
|------|------|
| `types/stock.ts` | 新增 `BacktestSummary`、`BacktestBar` 接口 |
| `composables/useBacktest.ts` | **新文件**：封装回测 API 调用 |
| `components/stock/BacktestDialog.vue` | **新文件**：回测弹窗（汇总卡片 + 三图） |
| `components/stock/StockResultTable.vue` | "操作"列新增"回测"按钮 |
| `views/StockView.vue` | 集成 BacktestDialog |

## 8. 边界与异常处理

- **K 线数据不存在**：诊股时已保存 CSV，若丢失则重新拉取；拉取失败返回 404
- **回测计算失败**：策略异常或数据格式问题，返回 500 + error message，前端显示错误提示
- **回测结果为空**（无交易信号）：图表仍正常渲染，汇总指标显示 0
- **缓存命中**：`backtestSummaryPath` 非空直接读缓存，跳过计算
- **并发安全**：同一 code 的回测通过 session worktree 隔离，无并发冲突
- **session 中已有部分回测结果**：加载历史 session 时，`backtestBarsPath` / `backtestSummaryPath` 非空的股票直接展示"回测"按钮（无需重新计算）
