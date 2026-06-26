# a_stock_client

独立可复用的 A 股 K 线数据获取模块。

## 快速开始

```python
from a_stock_client import AStockClient

client = AStockClient()

# 获取 K 线数据
df = client.get_kline("600519", "2025-01-01", "2025-06-24")
print(df.head())

# 保存到 CSV
client.to_csv("600519", "2025-01-01", "2025-06-24", "kline_600519.csv")
```

## 命令行

```bash
# 打印到终端
python -m a_stock_client 600519 2025-01-01 2025-06-24

# 保存到 CSV
python -m a_stock_client 600519 2025-01-01 2025-06-24 -o kline.csv

# 详细日志
python -m a_stock_client 600519 2025-01-01 2025-06-24 -v
```

## 输出字段

| 字段 | 说明 |
|------|------|
| date | 交易日期 |
| open | 开盘价（前复权） |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量（股） |
| amount | 成交额（元） |
| pct_chg | 涨跌幅（%） |
| ma5/ma10/ma20 | 移动均线 |
| volume_ratio | 量比 |
| code | 股票代码 |
| name | 股票名称 |
| source | 数据来源 |
