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

from app.models.schemas import (
    StockAnalyzeRequest, StockDiagnosis, DiagnosisResult,
    ChatSession, ChatMessage,
)
from app.services.engine_factory import get_or_create_engine
from app.services.session_store import save_session, get_session, list_sessions
from app.services.worktree_manager import ensure_worktree, WORKTREES_DIR
from app.services.skill_store import load_skill_to_worktree, get_skill_metadata

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
    skills: list[str],
    session_id: str,
    model: str = "",
    sector: str = "",
) -> None:
    """后台任务：串行分析每只股票，逐只 SSE 推送结果."""
    import pandas as pd
    from a_stock_client import AStockClient

    client = AStockClient()
    session = await get_session(session_id)
    if session is None:
        return

    # 1. 先预加载 skills 到 worktree（在创建 engine 之前，确保 opencode 启动时可见）
    worktree_dir = str(ensure_worktree(session_id))
    skill_names: list[str] = []
    for skill_id in skills:
        try:
            result = await load_skill_to_worktree(skill_id, session_id)
            meta = await get_skill_metadata(skill_id)
            if meta:
                skill_names.append(meta.get("name", skill_id))
        except Exception as e:
            logger.warning(f"Failed to load skill {skill_id}: {e}")

    # 2. 创建 engine（skills 已在 worktree 中）
    engine = await get_or_create_engine(session_id)
    if engine is None:
        await _stream_event(analysis_id, "error", {"message": "引擎不可用"})
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

            kline_text = _df_to_text(df)
            prompt = _build_prompt(code, name, kline_text, skill_names)

            collected = []

            def on_text(evt):
                if evt.type == "text" and evt.content:
                    collected.append(evt.content)

            engine.on("stream", on_text)
            try:
                result = await engine.execute({
                    "prompt": prompt,
                    "model": model,
                    "workingDirectory": worktree_dir,
                    "sessionId": None,
                })
            finally:
                engine.off("stream", on_text)

            output = result.get("output", "") if result else ""
            if not output:
                output = "".join(collected)

            parsed = _parse_conclusion(output)

            diagnosis_result = DiagnosisResult(
                code=code,
                name=name,
                conclusion=parsed["conclusion"],
                reason=parsed["reason"] or output[:200],
                close=close_val,
                open=open_val,
                pct_chg=pct_chg_val,
                ema20=ema20_val,
                source=source,
                klinePath=kline_rel_path,
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
        skills=skills,
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
            skills=body.skills,
            session_id=session.id,
            model=body.model or "",
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
