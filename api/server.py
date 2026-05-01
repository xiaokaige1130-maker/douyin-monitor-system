"""
API服务器模块
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from loguru import logger

from core.config import Config
from core.database import Database

app = FastAPI(
    title="抖音同行直播监控API",
    description="监控同行开播时间、直播时长、在线人数、进店人数与直播运营数据",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = None
db = None


def _jsonable(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(val) for key, val in value.items()}
    return value


async def get_db():
    if db is None:
        raise HTTPException(status_code=503, detail="数据库尚未初始化")
    return db


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head><title>抖音同行直播监控</title></head>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; line-height: 1.6;">
        <h1>抖音同行直播监控</h1>
        <p>用于监控同行开播时间、直播时长、在线人数、进店人数、点赞评论等运营数据。</p>
        <ul>
          <li><a href="/docs">API 文档</a></li>
          <li><a href="/api/health">健康检查</a></li>
          <li><a href="/api/operations/overview">运营总览</a></li>
          <li><a href="/api/operations/accounts/ranking">同行排行榜</a></li>
          <li><a href="/api/operations/live-calendar">开播日历</a></li>
        </ul>
      </body>
    </html>
    """


@app.get("/api/health")
async def health_check(db: Database = Depends(get_db)):
    try:
        accounts = await db.get_monitored_accounts(active_only=True)
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "monitored_accounts": len(accounts),
            "version": "1.1.0",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@app.get("/api/accounts")
async def get_accounts(active_only: bool = Query(True), days: int = Query(7, ge=1, le=90), db: Database = Depends(get_db)):
    try:
        accounts = await db.get_monitored_accounts(active_only=active_only)
        result = []
        for account in accounts:
            stats = await db.get_account_stats(account.id, days=days)
            result.append({
                "id": account.id,
                "douyin_id": account.douyin_id,
                "nickname": account.nickname,
                "sec_uid": account.sec_uid,
                "live_room_id": account.live_room_id,
                "live_url": account.live_url,
                "is_active": account.is_active,
                "check_interval_minutes": account.check_interval_minutes,
                "last_checked": account.last_checked,
                "risk_status": account.risk_status,
                "cooldown_until": account.cooldown_until,
                "consecutive_failures": account.consecutive_failures,
                "last_error": account.last_error,
                "stats": stats,
            })
        return _jsonable({"count": len(result), "accounts": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账号列表失败: {str(e)}")


@app.post("/api/accounts")
async def add_account(
    douyin_id: str = Query(..., description="抖音号或账号标识"),
    nickname: Optional[str] = Query(None, description="同行昵称/备注"),
    sec_uid: Optional[str] = Query(None, description="抖音 sec_uid，知道时优先填写"),
    live_room_id: Optional[str] = Query(None, description="固定直播间 room_id，知道时填写"),
    live_url: Optional[str] = Query(None, description="用户页或直播间 URL，推荐填写"),
    check_interval_minutes: int = Query(10, ge=2, le=240),
    db: Database = Depends(get_db),
):
    try:
        existing = await db.get_account_by_douyin_id(douyin_id)
        if existing:
            raise HTTPException(status_code=400, detail="账号已存在")

        account = await db.create_monitored_account(
            douyin_id=douyin_id,
            nickname=nickname,
            sec_uid=sec_uid,
            live_room_id=live_room_id,
            live_url=live_url,
            check_interval_minutes=check_interval_minutes,
        )
        return _jsonable({"success": True, "message": "账号已写入监控列表", "account": {
            "id": account.id,
            "douyin_id": account.douyin_id,
            "nickname": account.nickname,
            "sec_uid": account.sec_uid,
            "live_room_id": account.live_room_id,
            "live_url": account.live_url,
            "check_interval_minutes": account.check_interval_minutes,
        }})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加账号失败: {str(e)}")


@app.patch("/api/accounts/{account_id}")
async def update_account(
    account_id: int,
    nickname: Optional[str] = Query(None),
    sec_uid: Optional[str] = Query(None),
    live_room_id: Optional[str] = Query(None),
    live_url: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    check_interval_minutes: Optional[int] = Query(None, ge=2, le=240),
    clear_cooldown: bool = Query(False),
    db: Database = Depends(get_db),
):
    updates: Dict[str, Any] = {}
    for key, value in {
        "nickname": nickname,
        "sec_uid": sec_uid,
        "live_room_id": live_room_id,
        "live_url": live_url,
        "is_active": is_active,
        "check_interval_minutes": check_interval_minutes,
    }.items():
        if value is not None:
            updates[key] = value
    if clear_cooldown:
        updates.update({"cooldown_until": None, "consecutive_failures": 0, "risk_status": "normal", "last_error": None})
    if not updates:
        raise HTTPException(status_code=400, detail="没有可更新字段")
    ok = await db.update_monitored_account(account_id, **updates)
    if not ok:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"success": True, "updated": updates}


@app.get("/api/lives/active")
async def get_active_lives(db: Database = Depends(get_db)):
    try:
        sessions = await db.get_active_live_sessions()
        result = []
        for session in sessions:
            snapshots = await db.get_session_snapshots(session.id, limit=1)
            latest = snapshots[0] if snapshots else None
            account = await db.get_account_by_id(session.account_id)
            result.append({
                "session_id": session.id,
                "live_id": session.live_id,
                "room_id": session.room_id,
                "title": session.title,
                "live_url": session.live_url,
                "account": {
                    "id": account.id if account else None,
                    "douyin_id": account.douyin_id if account else None,
                    "nickname": account.nickname if account else None,
                },
                "start_time": session.start_time,
                "duration_minutes": int((datetime.now() - session.start_time).total_seconds() / 60),
                "current_viewers": latest.viewers_count if latest else None,
                "current_enter_count": latest.enter_count if latest else None,
                "max_viewers": session.max_viewers,
                "avg_viewers": session.avg_viewers,
                "max_enter_count": session.max_enter_count,
                "avg_enter_count": session.avg_enter_count,
                "total_likes": session.total_likes,
                "total_comments": session.total_comments,
                "total_shares": session.total_shares,
            })
        return _jsonable({"count": len(result), "active_lives": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃直播失败: {str(e)}")


@app.get("/api/lives/recent")
async def get_recent_lives(days: int = Query(7, ge=1, le=90), limit: int = Query(50, ge=1, le=200), db: Database = Depends(get_db)):
    rows = await db.get_live_calendar(days, limit)
    return _jsonable({"count": len(rows), "recent_lives": rows})


@app.get("/api/lives/{live_id}")
async def get_live_details(live_id: str, include_snapshots: bool = Query(False), db: Database = Depends(get_db)):
    session = await db.get_live_session_by_live_id(live_id)
    if not session:
        raise HTTPException(status_code=404, detail="直播不存在")
    account = await db.get_account_by_id(session.account_id)
    data = {
        "id": session.id,
        "live_id": session.live_id,
        "room_id": session.room_id,
        "title": session.title,
        "live_url": session.live_url,
        "account": {"id": account.id, "douyin_id": account.douyin_id, "nickname": account.nickname} if account else None,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "duration_minutes": session.duration_minutes,
        "max_viewers": session.max_viewers,
        "avg_viewers": session.avg_viewers,
        "max_enter_count": session.max_enter_count,
        "avg_enter_count": session.avg_enter_count,
        "total_likes": session.total_likes,
        "total_comments": session.total_comments,
        "total_shares": session.total_shares,
        "status": session.status,
    }
    if include_snapshots:
        snapshots = await db.get_session_snapshots(session.id, limit=1000)
        data["snapshots"] = [{
            "snapshot_time": item.snapshot_time,
            "viewers_count": item.viewers_count,
            "enter_count": item.enter_count,
            "likes_count": item.likes_count,
            "comments_count": item.comments_count,
            "shares_count": item.shares_count,
            "products": item.get_products(),
        } for item in snapshots]
    return _jsonable(data)


@app.get("/api/stats/daily")
async def get_daily_stats(date: Optional[str] = Query(None), db: Database = Depends(get_db)):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
        return _jsonable({"date": target_date.strftime("%Y-%m-%d"), "stats": await db.get_daily_stats(target_date)})
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")


@app.get("/api/stats/account/{account_id}")
async def get_account_stats(account_id: int, days: int = Query(7, ge=1, le=90), db: Database = Depends(get_db)):
    account = await db.get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return _jsonable({
        "account": {"id": account.id, "douyin_id": account.douyin_id, "nickname": account.nickname},
        "period_days": days,
        "stats": await db.get_account_stats(account_id, days),
    })


@app.get("/api/operations/overview")
async def operations_overview(days: int = Query(7, ge=1, le=90), db: Database = Depends(get_db)):
    overview = await db.get_operations_overview(days)
    ranking = await db.get_competitor_ranking(days, limit=10)
    calendar = await db.get_live_calendar(days, limit=20)
    return _jsonable({
        "period_days": days,
        "overview": overview,
        "top_accounts": ranking,
        "recent_lives": calendar,
        "notes": {
            "viewers_count": "直播在线人数口径",
            "enter_count": "采样时获取到的进房/看播人数口径；平台未返回时用在线人数兜底",
        },
    })


@app.get("/api/operations/accounts/ranking")
async def operations_account_ranking(days: int = Query(7, ge=1, le=90), limit: int = Query(50, ge=1, le=200), db: Database = Depends(get_db)):
    rows = await db.get_competitor_ranking(days=days, limit=limit)
    return _jsonable({"period_days": days, "count": len(rows), "accounts": rows})


@app.get("/api/operations/live-calendar")
async def operations_live_calendar(days: int = Query(7, ge=1, le=90), limit: int = Query(200, ge=1, le=500), db: Database = Depends(get_db)):
    rows = await db.get_live_calendar(days=days, limit=limit)
    return _jsonable({"period_days": days, "count": len(rows), "lives": rows})


@app.get("/api/system/status")
async def get_system_status(db: Database = Depends(get_db)):
    try:
        accounts = await db.get_monitored_accounts(active_only=False)
        active_lives = await db.get_active_live_sessions()
        overview = await db.get_operations_overview(days=7)
        risk_accounts = [a for a in accounts if a.risk_status and a.risk_status != "normal"]
        return _jsonable({
            "timestamp": datetime.now(),
            "system": {"status": "running", "version": "1.1.0"},
            "accounts": {"total": len(accounts), "active": len([a for a in accounts if a.is_active]), "risk": len(risk_accounts)},
            "active_lives": len(active_lives),
            "overview_7days": overview,
            "risk_accounts": [{"id": a.id, "douyin_id": a.douyin_id, "nickname": a.nickname, "risk_status": a.risk_status, "cooldown_until": a.cooldown_until, "last_error": a.last_error} for a in risk_accounts[:20]],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


async def start_api_server(config_obj: Config, db_obj: Database):
    global config, db
    config = config_obj
    db = db_obj

    import uvicorn
    api_config = config.get_api_config()
    logger.info(f"启动API服务器: {api_config['host']}:{api_config['port']}")
    server_config = uvicorn.Config(
        app,
        host=api_config["host"],
        port=api_config["port"],
        log_level="info" if api_config["debug"] else "warning",
    )
    server = uvicorn.Server(server_config)
    await server.serve()
