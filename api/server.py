"""
API服务器模块
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from core.config import Config
from core.database import Database
from core.models import MonitoredAccount, LiveSession

app = FastAPI(
    title="抖音监控系统API",
    description="24小时监控抖音同行开播时间、时长、直播间数据",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
config = None
db = None

async def get_db():
    """获取数据库实例"""
    return db

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global config, db
    
    # 这里在实际应用中会从依赖注入获取
    # 为了简化，我们使用全局变量
    pass

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径，返回API文档链接"""
    html_content = """
    <html>
        <head>
            <title>抖音监控系统API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { display: inline-block; padding: 5px 10px; background: #4CAF50; color: white; border-radius: 3px; margin-right: 10px; }
                .url { font-family: monospace; color: #2196F3; }
            </style>
        </head>
        <body>
            <h1>抖音监控系统API</h1>
            <p>24小时监控抖音同行开播时间、时长、直播间数据</p>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/api/health</span>
                <p>健康检查</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/api/accounts</span>
                <p>获取监控账号列表</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/api/lives/active</span>
                <p>获取活跃直播</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/api/lives/recent</span>
                <p>获取最近直播</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/api/stats/daily</span>
                <p>获取每日统计</p>
            </div>
            
            <p>查看完整API文档: <a href="/docs">/docs</a> 或 <a href="/redoc">/redoc</a></p>
        </body>
    </html>
    """
    return html_content

@app.get("/api/health")
async def health_check(db: Database = Depends(get_db)):
    """健康检查"""
    try:
        # 检查数据库连接
        accounts = await db.get_monitored_accounts(active_only=True)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "monitored_accounts": len(accounts),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@app.get("/api/accounts")
async def get_accounts(
    active_only: bool = Query(True, description="是否只返回活跃账号"),
    db: Database = Depends(get_db)
):
    """获取监控账号列表"""
    try:
        accounts = await db.get_monitored_accounts(active_only=active_only)
        
        result = []
        for account in accounts:
            # 获取账号统计
            stats = await db.get_account_stats(account.id, days=7)
            
            result.append({
                "id": account.id,
                "douyin_id": account.douyin_id,
                "nickname": account.nickname,
                "is_active": account.is_active,
                "check_interval_minutes": account.check_interval_minutes,
                "last_checked": account.last_checked.isoformat() if account.last_checked else None,
                "stats": stats
            })
            
        return {
            "count": len(result),
            "accounts": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账号列表失败: {str(e)}")

@app.post("/api/accounts")
async def add_account(
    douyin_id: str = Query(..., description="抖音ID"),
    nickname: Optional[str] = Query(None, description="昵称"),
    check_interval_minutes: int = Query(10, description="检查间隔（分钟）"),
    db: Database = Depends(get_db)
):
    """添加监控账号"""
    try:
        # 检查是否已存在
        existing = await db.get_account_by_douyin_id(douyin_id)
        if existing:
            raise HTTPException(status_code=400, detail="账号已存在")
        
        # 这里需要实际创建账号的逻辑
        # 由于数据库模型需要会话，这里简化处理
        return {
            "success": True,
            "message": "账号添加成功（演示模式）",
            "data": {
                "douyin_id": douyin_id,
                "nickname": nickname,
                "check_interval_minutes": check_interval_minutes
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加账号失败: {str(e)}")

@app.get("/api/lives/active")
async def get_active_lives(db: Database = Depends(get_db)):
    """获取活跃直播"""
    try:
        active_sessions = await db.get_active_live_sessions()
        
        result = []
        for session in active_sessions:
            # 获取最新快照
            snapshots = await db.get_session_snapshots(session.id, limit=1)
            latest_snapshot = snapshots[0] if snapshots else None
            
            # 获取账号信息
            account = await db.get_account_by_douyin_id(str(session.account_id))
            
            result.append({
                "session_id": session.id,
                "live_id": session.live_id,
                "account": {
                    "id": account.id if account else None,
                    "douyin_id": account.douyin_id if account else None,
                    "nickname": account.nickname if account else None
                },
                "start_time": session.start_time.isoformat(),
                "duration_minutes": int((datetime.now() - session.start_time).total_seconds() / 60),
                "max_viewers": session.max_viewers,
                "current_viewers": latest_snapshot.viewers_count if latest_snapshot else None,
                "total_likes": session.total_likes,
                "total_comments": session.total_comments
            })
            
        return {
            "count": len(result),
            "active_lives": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃直播失败: {str(e)}")

@app.get("/api/lives/recent")
async def get_recent_lives(
    days: int = Query(7, description="天数", ge=1, le=30),
    limit: int = Query(50, description="限制数量", ge=1, le=100),
    db: Database = Depends(get_db)
):
    """获取最近直播"""
    try:
        # 这里简化实现，实际需要查询数据库
        # 使用原始SQL查询
        async with db.pg_pool.acquire() as conn:
            query = """
            SELECT 
                ls.*,
                ma.douyin_id,
                ma.nickname
            FROM live_sessions ls
            JOIN monitored_accounts ma ON ls.account_id = ma.id
            WHERE ls.start_time >= $1
            ORDER BY ls.start_time DESC
            LIMIT $2
            """
            
            start_date = datetime.now() - timedelta(days=days)
            rows = await conn.fetch(query, start_date, limit)
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "live_id": row["live_id"],
                    "account": {
                        "douyin_id": row["douyin_id"],
                        "nickname": row["nickname"]
                    },
                    "start_time": row["start_time"].isoformat(),
                    "end_time": row["end_time"].isoformat() if row["end_time"] else None,
                    "duration_minutes": row["duration_minutes"],
                    "max_viewers": row["max_viewers"],
                    "avg_viewers": row["avg_viewers"],
                    "total_likes": row["total_likes"],
                    "total_comments": row["total_comments"],
                    "total_gifts": float(row["total_gifts"]) if row["total_gifts"] else 0.0,
                    "status": row["status"]
                })
                
            return {
                "count": len(result),
                "recent_lives": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近直播失败: {str(e)}")

@app.get("/api/lives/{live_id}")
async def get_live_details(
    live_id: str,
    include_snapshots: bool = Query(False, description="是否包含快照数据"),
    db: Database = Depends(get_db)
):
    """获取直播详情"""
    try:
        # 这里简化实现
        # 实际需要查询数据库获取直播详情和快照
        
        return {
            "live_id": live_id,
            "message": "详情查询功能（演示模式）",
            "note": "实际实现需要查询数据库获取直播详情"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取直播详情失败: {str(e)}")

@app.get("/api/stats/daily")
async def get_daily_stats(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD"),
    db: Database = Depends(get_db)
):
    """获取每日统计"""
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()
            
        stats = await db.get_daily_stats(target_date)
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "stats": stats
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日统计失败: {str(e)}")

@app.get("/api/stats/account/{account_id}")
async def get_account_stats(
    account_id: int,
    days: int = Query(7, description="天数", ge=1, le=90),
    db: Database = Depends(get_db)
):
    """获取账号统计"""
    try:
        stats = await db.get_account_stats(account_id, days)
        
        # 获取账号信息
        async with db.pg_pool.acquire() as conn:
            query = "SELECT douyin_id, nickname FROM monitored_accounts WHERE id = $1"
            row = await conn.fetchrow(query, account_id)
            
            account_info = {
                "id": account_id,
                "douyin_id": row["douyin_id"] if row else None,
                "nickname": row["nickname"] if row else None
            }
            
        return {
            "account": account_info,
            "period_days": days,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账号统计失败: {str(e)}")

@app.get("/api/system/status")
async def get_system_status(db: Database = Depends(get_db)):
    """获取系统状态"""
    try:
        # 获取各种统计
        async with db.pg_pool.acquire() as conn:
            # 账号统计
            accounts_query = "SELECT COUNT(*) as total, COUNT(CASE WHEN is_active THEN 1 END) as active FROM monitored_accounts"
            accounts_row = await conn.fetchrow(accounts_query)
            
            # 直播统计
            lives_query = """
            SELECT 
                COUNT(*) as total_lives,
                COUNT(CASE WHEN status = 'live' THEN 1 END) as active_lives,
                COALESCE(SUM(duration_minutes), 0) as total_duration
            FROM live_sessions
            WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
            """
            lives_row = await conn.fetchrow(lives_query)
            
            # 监控日志统计
            logs_query = """
            SELECT 
                COUNT(*) as total_checks,
                COUNT(CASE WHEN success THEN 1 END) as successful_checks,
                COUNT(CASE WHEN is_live THEN 1 END) as live_checks
            FROM monitoring_logs
            WHERE check_time >= CURRENT_DATE
            """
            logs_row = await conn.fetchrow(logs_query)
            
        return {
            "timestamp": datetime.now().isoformat(),
            "accounts": {
                "total": accounts_row["total"],
                "active": accounts_row["active"]
            },
            "lives_7days": {
                "total": lives_row["total_lives"],
                "active": lives_row["active_lives"],
                "total_duration_minutes": lives_row["total_duration"]
            },
            "today_checks": {
                "total": logs_row["total_checks"],
                "successful": logs_row["successful_checks"],
                "live_detections": logs_row["live_checks"]
            },
            "system": {
                "status": "running",
                "version": "1.0.0"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

async def start_api_server(config_obj: Config, db_obj: Database):
    """启动API服务器"""
    global config, db
    config = config_obj
    db = db_obj
    
    import uvicorn
    api_config = config.get_api_config()
    
    logger.info(f"启动API服务器: {api_config['host']}:{api_config['port']}")
    
    uvicorn.run(
        app,
        host=api_config["host"],
        port=api_config["port"],
        log_level="info" if api_config["debug"] else "warning"
    )