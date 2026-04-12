"""
数据库管理模块
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json

import asyncpg
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, update, delete, func
from sqlalchemy.sql import and_

from core.config import Config
from core.models import Base, MonitoredAccount, LiveSession, LiveSnapshot, MonitoringLog

class Database:
    """数据库管理类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.async_session = None
        self.redis = None
        self.pg_pool = None
        
    async def connect(self):
        """连接数据库"""
        # 连接PostgreSQL
        db_config = self.config.get_database_config()
        self.engine = create_async_engine(
            db_config["url"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_recycle=db_config["pool_recycle"],
            echo=self.config.log_level == "DEBUG"
        )
        
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # 创建表
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 连接Redis
        redis_config = self.config.get_redis_config()
        self.redis = aioredis.from_url(
            redis_config["url"],
            decode_responses=redis_config["decode_responses"]
        )
        
        # 连接PostgreSQL连接池（用于原始查询）
        # 转换URL格式：postgresql:// -> postgresql+asyncpg://
        asyncpg_url = self.config.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self.pg_pool = await asyncpg.create_pool(
            dsn=asyncpg_url,
            min_size=5,
            max_size=20
        )
        
    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
        
        if self.redis:
            await self.redis.close()
        
        if self.pg_pool:
            await self.pg_pool.close()
    
    # 监控账号管理
    async def get_monitored_accounts(self, active_only: bool = True) -> List[MonitoredAccount]:
        """获取监控账号列表"""
        async with self.async_session() as session:
            query = select(MonitoredAccount)
            if active_only:
                query = query.where(MonitoredAccount.is_active == True)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def get_account_by_douyin_id(self, douyin_id: str) -> Optional[MonitoredAccount]:
        """根据抖音ID获取账号"""
        async with self.async_session() as session:
            query = select(MonitoredAccount).where(MonitoredAccount.douyin_id == douyin_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def update_account_last_checked(self, account_id: int, check_time: datetime):
        """更新账号最后检查时间"""
        async with self.async_session() as session:
            query = update(MonitoredAccount).where(MonitoredAccount.id == account_id).values(
                last_checked=check_time
            )
            await session.execute(query)
            await session.commit()
    
    # 直播会话管理
    async def create_live_session(self, account_id: int, live_id: str, start_time: datetime) -> LiveSession:
        """创建直播会话"""
        async with self.async_session() as session:
            # 检查是否已存在
            existing = await session.execute(
                select(LiveSession).where(LiveSession.live_id == live_id)
            )
            if existing.scalar_one_or_none():
                return None
            
            session_obj = LiveSession(
                account_id=account_id,
                live_id=live_id,
                start_time=start_time,
                status="live"
            )
            session.add(session_obj)
            await session.commit()
            await session.refresh(session_obj)
            return session_obj
    
    async def update_live_session(self, session_id: int, **kwargs) -> bool:
        """更新直播会话"""
        async with self.async_session() as session:
            query = update(LiveSession).where(LiveSession.id == session_id).values(**kwargs)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
    
    async def end_live_session(self, session_id: int, end_time: datetime):
        """结束直播会话"""
        async with self.async_session() as session:
            # 获取会话信息
            query = select(LiveSession).where(LiveSession.id == session_id)
            result = await session.execute(query)
            live_session = result.scalar_one_or_none()
            
            if live_session:
                # 计算时长
                duration = (end_time - live_session.start_time).total_seconds() / 60
                
                # 更新会话
                update_query = update(LiveSession).where(LiveSession.id == session_id).values(
                    end_time=end_time,
                    duration_minutes=int(duration),
                    status="ended",
                    updated_at=datetime.now()
                )
                await session.execute(update_query)
                await session.commit()
    
    async def get_active_live_sessions(self) -> List[LiveSession]:
        """获取活跃的直播会话"""
        async with self.async_session() as session:
            query = select(LiveSession).where(LiveSession.status == "live")
            result = await session.execute(query)
            return list(result.scalars().all())
    
    # 直播快照管理
    async def add_live_snapshot(self, session_id: int, snapshot_data: Dict[str, Any]) -> LiveSnapshot:
        """添加直播快照"""
        async with self.async_session() as session:
            snapshot = LiveSnapshot(
                session_id=session_id,
                snapshot_time=snapshot_data.get("snapshot_time", datetime.now()),
                viewers_count=snapshot_data.get("viewers_count"),
                likes_count=snapshot_data.get("likes_count"),
                comments_count=snapshot_data.get("comments_count"),
                shares_count=snapshot_data.get("shares_count"),
                gifts_value=snapshot_data.get("gifts_value"),
                products=json.dumps(snapshot_data.get("products", []), ensure_ascii=False)
            )
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)
            return snapshot
    
    async def get_session_snapshots(self, session_id: int, limit: int = 100) -> List[LiveSnapshot]:
        """获取会话快照"""
        async with self.async_session() as session:
            query = select(LiveSnapshot).where(
                LiveSnapshot.session_id == session_id
            ).order_by(LiveSnapshot.snapshot_time.desc()).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    # 监控日志
    async def add_monitoring_log(self, log_data: Dict[str, Any]) -> MonitoringLog:
        """添加监控日志"""
        async with self.async_session() as session:
            log = MonitoringLog(
                account_id=log_data.get("account_id"),
                check_time=log_data.get("check_time", datetime.now()),
                is_live=log_data.get("is_live", False),
                live_id=log_data.get("live_id"),
                viewers_count=log_data.get("viewers_count"),
                response_time_ms=log_data.get("response_time_ms"),
                success=log_data.get("success", True),
                error_message=log_data.get("error_message")
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log
    
    # 统计数据查询
    async def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        """获取每日统计"""
        async with self.pg_pool.acquire() as conn:
            # 获取当天的直播统计
            query = """
            SELECT 
                COUNT(DISTINCT ls.id) as total_lives,
                COUNT(DISTINCT ls.account_id) as active_accounts,
                COALESCE(SUM(ls.duration_minutes), 0) as total_duration,
                COALESCE(AVG(ls.max_viewers), 0) as avg_max_viewers,
                COALESCE(SUM(ls.total_likes), 0) as total_likes,
                COALESCE(SUM(ls.total_comments), 0) as total_comments
            FROM live_sessions ls
            WHERE DATE(ls.start_time) = DATE($1)
            """
            
            result = await conn.fetchrow(query, date)
            
            if result:
                return dict(result)
            return {}
    
    async def get_account_stats(self, account_id: int, days: int = 7) -> Dict[str, Any]:
        """获取账号统计"""
        async with self.pg_pool.acquire() as conn:
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
            SELECT 
                COUNT(*) as total_lives,
                COALESCE(AVG(duration_minutes), 0) as avg_duration,
                COALESCE(AVG(max_viewers), 0) as avg_max_viewers,
                COALESCE(SUM(total_likes), 0) as total_likes,
                COALESCE(SUM(total_comments), 0) as total_comments,
                COALESCE(SUM(total_gifts), 0) as total_gifts
            FROM live_sessions
            WHERE account_id = $1 AND start_time >= $2
            """
            
            result = await conn.fetchrow(query, account_id, start_date)
            
            if result:
                return dict(result)
            return {}
    
    # 数据清理
    async def cleanup_old_data(self, cutoff_date: datetime) -> int:
        """清理旧数据"""
        async with self.async_session() as session:
            # 删除旧的监控日志
            log_query = delete(MonitoringLog).where(MonitoringLog.check_time < cutoff_date)
            log_result = await session.execute(log_query)
            log_deleted = log_result.rowcount
            
            # 删除旧的直播快照（保留有活跃会话的）
            snapshot_query = delete(LiveSnapshot).where(
                and_(
                    LiveSnapshot.snapshot_time < cutoff_date,
                    ~LiveSnapshot.session_id.in_(
                        select(LiveSession.id).where(LiveSession.status == "live")
                    )
                )
            )
            snapshot_result = await session.execute(snapshot_query)
            snapshot_deleted = snapshot_result.rowcount
            
            await session.commit()
            return log_deleted + snapshot_deleted
    
    # Redis操作
    async def set_cache(self, key: str, value: Any, expire: int = 300):
        """设置缓存"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await self.redis.setex(key, expire, value)
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def delete_cache(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)
    
    async def increment_counter(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        return await self.redis.incrby(key, amount)
    
    async def add_to_set(self, key: str, value: str):
        """添加到集合"""
        await self.redis.sadd(key, value)
    
    async def get_set_members(self, key: str) -> List[str]:
        """获取集合成员"""
        return await self.redis.smembers(key)
    
    async def remove_from_set(self, key: str, value: str):
        """从集合中移除"""
        await self.redis.srem(key, value)