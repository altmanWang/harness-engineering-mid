# -*- coding: utf-8 -*-
"""Stock 智能诊股 API — SSE 流式逐只分析"""

import asyncio
import json
import re
import time
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    StockAnalyzeRequest, StockDiagnosis, DiagnosisResult,
    ChatSession, ChatMessage,
)
from app.services.engine_factory import get_or_create_engine
from app.services.session_store import save_session, get_session, list_sessions
from app.services.worktree_manager import ensure_worktree
from app.services.skill_store import load_skill_to_worktree

# 确保 a_stock_client 可导入
_STOCK_CLIENT_ROOT = Path(__file__).resolve().parent.parent.parent / "a_stock_client"
if str(_STOCK_CLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STOCK_CLIENT_ROOT))

router = APIRouter()

# 模块级状态
_active_analyses: dict = {}
_stream_queues: dict = {}


def _gen_id(prefix: str) -> str:
    import random
    import string
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{int(time.time() * 1000)}-{suffix}"


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


def _build_prompt(code: str, name: str, kline_text: str) -> str:
    """构建单只股票的分析 prompt."""
    return f"""你是一个A股技术分析专家。请根据以下股票的近90天K线数据，判断该股票当前应该"看多"、"看空"还是"观望"。

股票代码: {code}
股票名称: {name}

近90天K线数据（date, open, high, low, close, volume, pct_chg, ma5, ma10, ma20, volume_ratio）:
{kline_text}

请基于技术指标（均线排列、成交量变化、涨跌幅趋势、量比等）给出判断。
回复格式:
结论: 看多/看空/观望
理由: (100字以内)"""


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
) -> None:
    """后台任务：串行分析每只股票，逐只 SSE 推送结果."""
    import pandas as pd
    from a_stock_client import AStockClient

    client = AStockClient()
    session = await get_session(session_id)
    if session is None:
        return

    engine = await get_or_create_engine(session_id)
    if engine is None:
        await _stream_event(analysis_id, "error", {"message": "引擎不可用"})
        return

    # 预加载 skills 到 worktree
    worktree_dir = str(ensure_worktree(session_id))
    for skill_id in skills:
        try:
            await load_skill_to_worktree(skill_id, session_id)
        except Exception:
            pass

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

            kline_text = _df_to_text(df)
            prompt = _build_prompt(code, name, kline_text)

            collected = []

            def on_text(evt):
                if evt.type == "text" and evt.content:
                    collected.append(evt.content)

            engine.on("stream", on_text)

            result = await engine.execute({
                "prompt": prompt,
                "model": model,
                "workingDirectory": worktree_dir,
                "sessionId": None,
            })

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

    if session:
        session.diagnosis = StockDiagnosis(
            codes=codes,
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
    if not body.codes or len(body.codes) == 0:
        raise HTTPException(status_code=400, detail="股票代码不能为空")

    codes = [c.strip() for c in body.codes if c.strip()]
    if not codes:
        raise HTTPException(status_code=400, detail="股票代码不能为空")

    from datetime import datetime as dt

    if body.sessionId:
        session = await get_session(body.sessionId)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        now = dt.now(timezone.utc)
        existing_sessions = await list_sessions()
        today_prefix = now.strftime("%m.%d诊股")
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
            model="claude-sonnet-4-6",
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
