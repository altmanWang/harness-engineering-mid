# -*- coding: utf-8 -*-
"""Stock 智能诊股 API — SSE 流式逐只分析"""

import asyncio
import json
import re
import time
import sys
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.schemas import (
    StockAnalyzeRequest, StockDiagnosis, DiagnosisResult,
    ChatSession, ChatMessage,
)
from app.services.session_store import save_session, get_session, list_sessions
from app.services.worktree_manager import WORKTREES_DIR
from app.backtest_albrooks.strategies.registry import STRATEGY_REGISTRY
from app.backtest_albrooks.engine.runner import run_signal, run_backtest

# 确保 a_stock_client 可导入
_STOCK_CLIENT_ROOT = Path(__file__).resolve().parent.parent.parent / "a_stock_client"
if str(_STOCK_CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STOCK_CLIENT_ROOT))

router = APIRouter()

# 模块级状态
_active_analyses: dict = {}
_stream_queues: dict = {}

logger = logging.getLogger(__name__)

# 东方财富 API
_EM_BASE = "https://push2.eastmoney.com/api/qt/clist/get"
_EM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
}
# 板块列表缓存 (TTL 1 小时)
_sector_cache: dict = {"data": None, "timestamp": 0, "ttl": 3600}


def _fetch_sectors() -> list[dict]:
    """获取东方财富行业+概念板块列表，返回 [{code, name, type}]。"""
    now = time.time()
    if _sector_cache["data"] is not None and (now - _sector_cache["timestamp"]) < _sector_cache["ttl"]:
        return _sector_cache["data"]

    all_sectors: list[dict] = []

    # 行业板块 (m:90+t:2) + 概念板块 (m:90+t:3)
    for fs, type_label in [("m:90+t:2", "行业"), ("m:90+t:3", "概念")]:
        try:
            params = {
                "pn": "1", "pz": "500", "po": "1", "np": "1",
                "fltt": "2", "invt": "2", "fid": "f3",
                "fs": fs,
                "fields": "f12,f14",
            }
            r = requests.get(_EM_BASE, params=params, headers=_EM_HEADERS, timeout=10)
            data = r.json()
            items = data.get("data", {}).get("diff", [])
            for item in items:
                if item.get("f12") and item.get("f14"):
                    all_sectors.append({
                        "code": item["f12"],
                        "name": item["f14"],
                        "type": type_label,
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch {type_label} sectors from Eastmoney: {e}")

    _sector_cache["data"] = all_sectors
    _sector_cache["timestamp"] = now
    logger.info(f"Loaded {len(all_sectors)} sectors from Eastmoney")
    return all_sectors


# 东方财富行业板块代码参考（供前端展示时用）
# 可通过 GET /api/stock/sectors/{code}/stocks 获取成分股


def _fetch_sector_stocks(sector_code: str) -> list[str]:
    """获取指定板块的成分股代码列表。"""
    try:
        params = {
            "pn": "1", "pz": "500", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fid": "f3",
            "fs": f"b:{sector_code}",
            "fields": "f12",
        }
        r = requests.get(_EM_BASE, params=params, headers=_EM_HEADERS, timeout=10)
        data = r.json()
        items = data.get("data", {}).get("diff", [])
        codes = [item["f12"] for item in items if item.get("f12")]
        logger.info(f"Sector {sector_code}: {len(codes)} stocks")
        return codes
    except Exception as e:
        logger.error(f"Failed to fetch sector stocks for {sector_code}: {e}")
        return []


def _gen_id(prefix: str) -> str:
    import random
    import string
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{int(time.time() * 1000)}-{suffix}"


def _get_sector_name(sector_code: str) -> str:
    """根据板块代码查找板块名称."""
    sectors = _fetch_sectors()
    for s in sectors:
        if s["code"] == sector_code:
            return s["name"]
    return sector_code


async def _stream_event(analysis_id: str, event_type: str, data: dict) -> None:
    """Send an SSE event to all listeners for an analysis."""
    if analysis_id in _stream_queues:
        for q in _stream_queues[analysis_id]:
            await q.put((event_type, data))


def _parse_conclusion(text: str) -> dict:
    """从 LLM 输出中解析结论和理由."""
    conclusion = None
    reason = ""

    conclusion_match = re.search(r'结论[：:]\s*(.+?)(?:\n|$)', text)
    if conclusion_match:
        raw = conclusion_match.group(1).strip()
        if '看多' in raw:
            conclusion = '看多'
        elif '看空' in raw:
            conclusion = '看空'
        elif '观望' in raw:
            conclusion = '观望'

    reason_match = re.search(r'理由[：:]\s*(.+?)(?:\n|$)', text, re.DOTALL)
    if reason_match:
        reason = reason_match.group(1).strip()[:200]

    return {"conclusion": conclusion, "reason": reason}


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


def _build_prompt(code: str, name: str, kline_text: str, skill_names: list[str]) -> str:
    """构建单只股票的分析 prompt."""
    skills_section = ""
    if skill_names:
        skills_list = "\n".join(f"  - {s}" for s in skill_names)
        skills_section = f"""
## 可用技能（必须使用）

项目空间已注入以下技能，请在分析时主动调用相关技能获取数据：

{skills_list}

分析流程：
1. 首先调用 westock-data 技能查询 {code} ({name}) 的实时行情、技术指标、资金流向等数据
2. 结合提供的K线数据和技能查询结果，综合判断
"""
    else:
        skills_section = """
分析流程：
1. 首先调用 westock-data 技能查询该股票的实时行情、技术指标、资金流向等数据
2. 结合提供的K线数据和技能查询结果，综合判断
"""

    return f"""# 角色定义

你是一位顶级的**价格行为学分析大师**（Price Action Master），专注于A股市场的技术分析。你精通：

- K线形态识别与价格行为解读
- 均线系统、MACD、RSI、布林带等技术指标的综合运用
- 量价关系分析（成交量与价格趋势的配合）
- 支撑位/阻力位的判断
- 市场情绪与资金流向的洞察

## 分析任务

股票代码: **{code}**
股票名称: **{name}**

## K线数据（{name}）

以下为近90天日K线数据，包含 date, open, high, low, close, volume, pct_chg, ma5, ma10, ma20, volume_ratio：

```
{kline_text}
```
{skills_section}

## 输出格式

请基于价格行为学和技术指标给出专业判断，严格按以下格式输出：

结论: 看多/看空/观望
理由: (结合价格行为学和技术指标，简明扼要地说明判断依据，200字以内)"""


def _df_to_text(df, max_rows: int = 90) -> str:
    """将 DataFrame 格式化为文本表格."""
    import pandas as pd
    df = df.tail(max_rows)
    cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'pct_chg',
            'ma5', 'ma10', 'ma20', 'volume_ratio']
    available = [c for c in cols if c in df.columns]
    df_display = df[available].copy()
    if 'date' in df_display.columns:
        df_display['date'] = pd.to_datetime(df_display['date']).dt.strftime('%Y-%m-%d')
    for col in df_display.columns:
        if col != 'date' and df_display[col].dtype in ('float64', 'float32'):
            df_display[col] = df_display[col].round(2)
    return df_display.to_string(index=False)


async def _run_analysis(
    analysis_id: str,
    codes: list[str],
    days: int,
    strategy: str,
    strategy_config: dict,
    session_id: str,
    sector: str = "",
) -> None:
    """后台任务：串行分析每只股票，逐只 SSE 推送结果."""
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


@router.post("/stock/analyze")
async def start_analysis(body: StockAnalyzeRequest):
    # 优先使用 sector（板块代码），自动展开为成分股
    if body.sector:
        codes = _fetch_sector_stocks(body.sector)
        if not codes:
            raise HTTPException(status_code=400, detail=f"板块 {body.sector} 无成分股数据")
        sector_name = _get_sector_name(body.sector)
    else:
        if not body.codes or len(body.codes) == 0:
            raise HTTPException(status_code=400, detail="股票代码或板块不能为空")
        codes = [c.strip() for c in body.codes if c.strip()]
        if not codes:
            raise HTTPException(status_code=400, detail="股票代码不能为空")
        sector_name = ""

    from datetime import datetime as dt

    # 校验策略
    strategy = body.strategy or "ema_pullback"
    if strategy not in STRATEGY_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy}")
    strategy_config = _validate_config(strategy, body.strategyConfig or {})

    if body.sessionId:
        session = await get_session(body.sessionId)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        now = dt.now(timezone.utc)
        existing_sessions = await list_sessions()
        today_prefix = now.strftime("%m.%d诊股")
        if sector_name:
            today_prefix = f"{today_prefix}({sector_name})"
        same_day_count = sum(
            1 for s in existing_sessions
            if getattr(s, "type", "chat") == "stock_diagnosis"
            and (s.title or "").startswith(today_prefix)
        )
        title = today_prefix if same_day_count == 0 else f"{today_prefix}({same_day_count + 1})"

        session = ChatSession(
            id=_gen_id("session"),
            type="stock_diagnosis",
            title=title,
            engine="opencode",
            model=body.model or "",
            messages=[],
            createdAt=now.isoformat(),
            updatedAt=now.isoformat(),
        )
        await save_session(session)

    analysis_id = _gen_id("stock")

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
    _active_analyses[analysis_id] = task

    async def cleanup():
        try:
            await task
        except Exception:
            pass
        await asyncio.sleep(30)
        _active_analyses.pop(analysis_id, None)

    asyncio.ensure_future(cleanup())

    return {"analysisId": analysis_id, "sessionId": session.id}


@router.get("/stock/stream")
async def stream_analysis(id: str = Query(..., alias="analysisId")):
    task = _active_analyses.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    queue: asyncio.Queue = asyncio.Queue()

    if id not in _stream_queues:
        _stream_queues[id] = []
    _stream_queues[id].append(queue)

    async def generate():
        try:
            while True:
                try:
                    event_type, data = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    if task.done():
                        break
            await asyncio.sleep(0.3)
        except asyncio.CancelledError:
            pass
        finally:
            if id in _stream_queues:
                _stream_queues[id] = [q for q in _stream_queues[id] if q is not queue]
                if not _stream_queues[id]:
                    del _stream_queues[id]

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.get("/stock/sectors")
async def list_sectors():
    """返回所有行业板块列表，供前端下拉选择."""
    sectors = _fetch_sectors()
    return {"sectors": sectors}


@router.get("/stock/sectors/{sector_code}/stocks")
async def get_sector_stocks(sector_code: str):
    """返回指定板块的成分股代码列表."""
    codes = _fetch_sector_stocks(sector_code)
    if not codes:
        raise HTTPException(status_code=404, detail=f"板块 {sector_code} 无数据")
    return {"codes": codes, "sector": sector_code}


# westock-data 脚本路径（skill 目录下的 scripts/index.js）
import shutil as _shutil
_WESTOCK_DATA_SCRIPT = str(
    Path.home() / ".claude" / "skills" / "westock-data" / "scripts" / "index.js"
)
_NODE_EXE = _shutil.which("node") or "node"


async def _run_node(*args: str, timeout: float = 15) -> str | None:
    """运行 westock-data 脚本，返回 stdout 字符串或 None.

    使用线程池 + subprocess.run，兼容 Windows ProactorEventLoop。
    """
    import asyncio as _asyncio
    import concurrent.futures as _futures
    import subprocess as _subprocess
    import traceback as _traceback

    cmd = [_NODE_EXE, _WESTOCK_DATA_SCRIPT, *args]
    try:
        loop = _asyncio.get_running_loop()
        with _futures.ThreadPoolExecutor(max_workers=1) as pool:
            proc = await loop.run_in_executor(
                pool,
                lambda: _subprocess.run(
                    cmd, capture_output=True, timeout=timeout,
                    encoding="utf-8", errors="replace",
                ),
            )
        if proc.returncode != 0:
            err_msg = (proc.stderr or "").strip()
            logger.warning(f"westock-data error ({args}): {err_msg}")
            return None
        return (proc.stdout or "").strip()
    except _subprocess.TimeoutExpired:
        logger.warning(f"westock-data timeout for: {args}")
        return None
    except OSError:
        logger.error("node or westock-data script not found")
        return None
    except Exception:
        logger.error(f"westock-data failed ({args}):\n{_traceback.format_exc()}")
        return None


@router.get("/stock/search")
async def search_stocks(keyword: str = Query(..., min_length=1)):
    """通过 westock-data 搜索股票，返回 [{code, name, type}].

    先尝试 --stock 搜索个股，无结果时自动 fallback 到 sector 搜索板块成份股。
    板块搜索失败时逐步缩短关键字重试。
    匹配到多个板块时合并所有板块的成份股。
    """
    # 第一步：搜索个股
    raw = await _run_node("search", keyword, "--stock")
    stocks = _parse_search_table(raw or "")
    if stocks:
        logger.info(f"Stock search '{keyword}': {len(stocks)} individual results")
        return {"stocks": stocks}

    # 第二步：无个股结果时，尝试搜索板块（渐进式缩短关键字）
    sector_codes = await _search_sector_with_fallback(keyword)
    if not sector_codes:
        logger.info(f"Stock search '{keyword}': no results")
        return {"stocks": []}

    # 第三步：查所有匹配板块的成份股并合并去重
    all_stocks: list[dict] = []
    seen: set[str] = set()
    sector_names: list[str] = []
    for sc in sector_codes:
        raw = await _run_node("sector", sc["code"], timeout=30)
        for s in _parse_search_table(raw or ""):
            if s["code"] not in seen:
                seen.add(s["code"])
                all_stocks.append(s)
        sector_names.append(sc["name"])

    # 标注来源板块
    source_label = "、".join(sector_names[:3])
    if len(sector_names) > 3:
        source_label += f"等{len(sector_names)}个板块"
    for s in all_stocks:
        s["type"] = source_label
    logger.info(f"Stock search '{keyword}': {len(all_stocks)} stocks from {source_label}")
    return {"stocks": all_stocks}


async def _search_sector_with_fallback(keyword: str) -> list[dict]:
    """搜索板块，失败时逐步缩短关键字重试."""
    # 逐步缩短：优先按词分（空格），否则逐字缩短
    parts = keyword.split()
    candidates: list[str] = []
    if len(parts) > 1:
        for i in range(len(parts), 0, -1):
            candidates.append(" ".join(parts[:i]))
    else:
        # 单段中文：逐字缩短，最少保留 2 字
        for i in range(len(keyword), 1, -1):
            candidates.append(keyword[:i])
        # 最后也尝试原始关键字
        if keyword not in candidates:
            candidates.append(keyword)

    for candidate in candidates:
        raw = await _run_node("sector", "--search", candidate)
        if not raw:
            continue
        sector_codes = _parse_search_table(raw)
        if sector_codes:
            if candidate != keyword:
                logger.info(f"Sector search fallback: '{keyword}' -> '{candidate}', found {len(sector_codes)} sectors")
            return sector_codes
    return []


@router.get("/stock/kline/{session_id}/{code}")
async def get_kline_data(session_id: str, code: str):
    """读取 session worktree 中的 K 线 CSV，返回 ECharts 可用格式."""
    import csv
    from pathlib import Path

    kline_dir = WORKTREES_DIR / session_id / "kline"
    if not kline_dir.exists():
        raise HTTPException(status_code=404, detail=f"K-line dir not found for session {session_id}")

    # 查找匹配的 CSV 文件: {code}_{start}_{end}.csv
    csv_files = sorted(kline_dir.glob(f"{code}_*.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail=f"No K-line file for {code} in session {session_id}")

    csv_path = csv_files[0]
    rows: list[dict] = []
    kline_date = ""
    name = code

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_val = (row.get("date") or "").strip()
                try:
                    open_val = float(row.get("open", 0) or 0)
                    close_val = float(row.get("close", 0) or 0)
                    high_val = float(row.get("high", 0) or 0)
                    low_val = float(row.get("low", 0) or 0)
                    volume_val = float(row.get("volume", 0) or 0)
                    ema20_val = float(row.get("ma20", 0) or 0)
                except (ValueError, TypeError):
                    continue

                rows.append({
                    "date": date_val,
                    "open": round(open_val, 2),
                    "close": round(close_val, 2),
                    "high": round(high_val, 2),
                    "low": round(low_val, 2),
                    "volume": int(volume_val),
                    "ema20": round(ema20_val, 2),
                })

                if date_val:
                    kline_date = date_val

                # 从 CSV 中取股票名称
                row_name = (row.get("name") or "").strip()
                if row_name and name == code:
                    name = row_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read K-line CSV: {e}")

    if not rows:
        raise HTTPException(status_code=404, detail="K-line CSV is empty")

    return {
        "code": code,
        "name": name,
        "klineDate": kline_date,
        "data": rows,
    }


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
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_backtest, kline_path,
                output_dir=str(backtest_dir),
                config_overrides=strategy_config,
            ),
            timeout=300.0,  # 5 minutes
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


def _parse_search_table(text: str) -> list[dict]:
    """解析 westock-data search 返回的 markdown 表格.

    格式:
    | code | name | type |
    | --- | --- | --- |
    | sh600519 | 贵州茅台 | GP-A |
    """
    stocks: list[dict] = []
    in_header = False
    in_separator = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if not in_header:
            in_header = True
            continue
        if not in_separator:
            in_separator = True
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells[0] 和 cells[-1] 为空（表格边界的 |）
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            stocks.append({
                "code": cells[0],
                "name": cells[1],
                "type": cells[2] if len(cells) > 2 else "",
            })
    return stocks
