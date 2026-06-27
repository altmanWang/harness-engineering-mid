# AStockClient — 独立 A 股数据模块

## 文件位置

`backend/a_stock_client/` (相对于后端启动目录 `harness-engineering-py/`)

## 概述

独立可复用的 A 股（及跨市场）K 线数据获取模块，**已通过 `app/routers/stock.py` 集成到 API**，在股票诊股流程中自动调用 `AStockClient.get_kline()` 获取 K 线数据。

## 目录结构

```
a_stock_client/
├── __init__.py              # AStockClient 主类
├── __main__.py              # CLI 入口
├── data_provider/           # 数据源层
│   ├── base.py              # BaseFetcher + DataFetcherManager (核心)
│   ├── efinance_fetcher.py  # P0 东财
│   ├── tencent_fetcher.py   # 腾讯
│   ├── akshare_fetcher.py   # P1 AKShare
│   ├── tushare_fetcher.py   # 可选 (需 Token)
│   ├── pytdx_fetcher.py     # P2 通达信
│   ├── baostock_fetcher.py  # P3 宝信
│   ├── yfinance_fetcher.py  # P4 Yahoo Finance
│   ├── longbridge_fetcher.py # 可选 长桥
│   ├── finnhub_fetcher.py   # 可选 Finnhub
│   ├── alphavantage_fetcher.py # 可选 AlphaVantage
│   ├── tickflow_fetcher.py  # TickFlow
│   ├── fundamental_adapter.py # 基本面适配器
│   └── realtime_types.py    # 实时行情类型
└── src/                     # 辅助模块
    ├── config.py            # 配置 (环境变量)
    ├── data/                # 股票索引 & 名称映射
    ├── services/            # 诊断记录
    ├── patches/             # 东方财富补丁
    └── llm/                 # LLM 后端注册
```

## 核心类

### AStockClient (`__init__.py`)

对外暴露的简化接口:

```python
from a_stock_client import AStockClient

client = AStockClient()
df = client.get_kline("600519", "2025-01-01", "2025-06-24")
client.to_csv("600519", "2025-01-01", "2025-06-24", "kline_600519.csv")
```

### 输出字段

| 字段 | 说明 |
|------|------|
| date | 交易日期 |
| open | 开盘价 (前复权) |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 (股) |
| amount | 成交额 (元) |
| pct_chg | 涨跌幅 (%) |
| ma5/ma10/ma20 | 移动均线 |
| volume_ratio | 量比 |
| code | 股票代码 |
| name | 股票名称 |
| source | 数据来源 |

### 支持市场

- A 股 (沪深/科创/北交所): 6 位数字, 如 600519
- 港股: 5 位数字 / HK 前缀, 如 00700
- 美股: 字母代码, 如 AAPL
- 日股: 如 7203.T
- 韩股: 如 005930.KS

## DataFetcherManager (策略管理器)

### 数据源优先级

```
EfinanceFetcher (P0) → TencentFetcher → AkshareFetcher (P1)
→ PytdxFetcher (P2) → BaostockFetcher (P3) → YfinanceFetcher (P4)
```

可选数据源 (需配置): Tushare, Longbridge, Finnhub, AlphaVantage

### 故障切换

1. 按优先级依次尝试
2. 失败自动降级到下一个
3. 熔断机制: 连续失败 3 次 → 冷却 300 秒
4. 美股走专用路由, 港股过滤不支持的数据源

### 其他能力

| 方法 | 说明 |
|------|------|
| `get_daily_data()` | 日线 K 线 (主要方法) |
| `get_realtime_quote()` | 实时行情 |
| `get_chip_distribution()` | 筹码分布 |
| `get_stock_name()` | 股票名称 |
| `get_belong_boards()` | 所属板块 |
| `get_main_indices()` | 主要指数 |
| `get_market_stats()` | 市场统计 |
| `get_sector_rankings()` | 板块涨跌榜 |
| `get_hot_stocks()` | 人气股榜 |

## CLI 使用

```bash
python -m a_stock_client 600519 2025-01-01 2025-06-24
python -m a_stock_client 600519 2025-01-01 2025-06-24 -o kline.csv -v
```

## 配置 (src/config.py)

全部从环境变量读取:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TUSHARE_TOKEN` | "" | Tushare API token |
| `TICKFLOW_API_KEY` | "" | TickFlow API key |
| `FINNHUB_API_KEY` | "" | Finnhub API key |
| `ALPHAVANTAGE_API_KEY` | "" | AlphaVantage API key |
| `LONGBRIDGE_*` | "" | 长桥证券凭据 |
| `ENABLE_REALTIME_QUOTE` | true | 实时行情开关 |
| `ENABLE_CHIP_DISTRIBUTION` | true | 筹码分布开关 |
| `REALTIME_SOURCE_PRIORITY` | "tencent,akshare_sina,efinance,akshare_em" | 实时行情优先级 |
| `REALTIME_CACHE_TTL` | 600 | 实时缓存 TTL (秒) |

## 独立运行机制

通过 `sys.path.insert(0, _CLIENT_ROOT)` 将自身目录插入 path，确保 `data_provider/` 和 `src/` 的导入优先于项目根目录的同名包。
