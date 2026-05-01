"""
数据库管理模块
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

import asyncpg
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import and_

from core.config import Config
from core.models import Base, MonitoredAccount, LiveSession, LiveSnapshot, MonitoringLog


class Database:
    """数据库管理类。"""

    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.async_session = None
        self.redis = None
        self.pg_pool = None

    async def connect(self):
        db_config = self.config.get_database_config()
        self.engine = create_async_engine(
            db_config["url"],
            pool_size=db_config["pool_size"],
            max_overflow=db_config["max_overflow"],
            pool_recycle=db_config["pool_recycle"],
            echo=self.config.log_level == "DEBUG",
        )

        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        redis_config = self.config.get_redis_config()
        self.redis = aioredis.from_url(redis_config["url"], decode_responses=redis_config["decode_responses"])

        self.pg_pool = await asyncpg.create_pool(dsn=self.config.get_asyncpg_dsn(), min_size=2, max_size=20)
        await self.ensure_schema()

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
        if self.redis:
            await self.redis.close()
        if self.pg_pool:
            await self.pg_pool.close()

    async def ensure_schema(self):
        """兼容旧库，自动补齐新增列。"""
        statements = [
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS live_room_id VARCHAR(100)",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS live_url VARCHAR(500)",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS cooldown_until TIMESTAMP",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS risk_status VARCHAR(40) DEFAULT 'normal'",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS last_error TEXT",
            "ALTER TABLE monitored_accounts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS room_id VARCHAR(100)",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS live_url VARCHAR(500)",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(500)",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS max_enter_count INTEGER",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS avg_enter_count INTEGER",
            "ALTER TABLE live_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE live_snapshots ADD COLUMN IF NOT EXISTS enter_count INTEGER",
            "ALTER TABLE live_snapshots ADD COLUMN IF NOT EXISTS raw_data JSONB",
            "ALTER TABLE monitoring_logs ADD COLUMN IF NOT EXISTS enter_count INTEGER",
            "ALTER TABLE monitoring_logs ADD COLUMN IF NOT EXISTS risk_status VARCHAR(40) DEFAULT 'normal'",
        ]
        async with self.pg_pool.acquire() as conn:
            for statement in statements:
                await conn.execute(statement)

    # 监控账号管理
    async def get_monitored_accounts(self, active_only: bool = True) -> List[MonitoredAccount]:
        async with self.async_session() as session:
            query = select(MonitoredAccount).order_by(MonitoredAccount.id.asc())
            if active_only:
                query = query.where(MonitoredAccount.is_active == True)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_account_by_id(self, account_id: int) -> Optional[MonitoredAccount]:
        async with self.async_session() as session:
            result = await session.execute(select(MonitoredAccount).where(MonitoredAccount.id == account_id))
            return result.scalar_one_or_none()

    async def get_account_by_douyin_id(self, douyin_id: str) -> Optional[MonitoredAccount]:
        async with self.async_session() as session:
            result = await session.execute(select(MonitoredAccount).where(MonitoredAccount.douyin_id == douyin_id))
            return result.scalar_one_or_none()

    async def create_monitored_account(
        self,
        douyin_id: str,
        nickname: Optional[str] = None,
        sec_uid: Optional[str] = None,
        live_room_id: Optional[str] = None,
        live_url: Optional[str] = None,
        check_interval_minutes: int = 10,
    ) -> MonitoredAccount:
        async with self.async_session() as session:
            account = MonitoredAccount(
                douyin_id=douyin_id,
                nickname=nickname,
                sec_uid=sec_uid,
                live_room_id=live_room_id,
                live_url=live_url,
                check_interval_minutes=check_interval_minutes,
                is_active=True,
            )
            session.add(account)
            await session.commit()
            await session.refresh(account)
            return account

    async def update_monitored_account(self, account_id: int, **kwargs) -> bool:
        async with self.async_session() as session:
            kwargs["updated_at"] = datetime.now()
            result = await session.execute(update(MonitoredAccount).where(MonitoredAccount.id == account_id).values(**kwargs))
            await session.commit()
            return result.rowcount > 0

    async def update_account_last_checked(self, account_id: int, check_time: datetime):
        await self.update_monitored_account(account_id, last_checked=check_time)

    async def mark_account_success(self, account_id: int):
        await self.update_monitored_account(
            account_id,
            consecutive_failures=0,
            cooldown_until=None,
            risk_status="normal",
            last_error=None,
        )

    async def mark_account_failure(self, account: MonitoredAccount, error_message: str, risk_status: str = "error"):
        failures = (account.consecutive_failures or 0) + 1
        cooldown_until = None
        if risk_status in {"verify_required", "login_required", "blocked"}:
            cooldown_until = datetime.now() + timedelta(minutes=self.config.risk_cooldown_minutes)
        elif failures >= self.config.failure_cooldown_threshold:
            cooldown_until = datetime.now() + timedelta(minutes=self.config.account_cooldown_minutes)

        await self.update_monitored_account(
            account.id,
            consecutive_failures=failures,
            cooldown_until=cooldown_until,
            risk_status=risk_status,
            last_error=error_message[:1000],
        )

    # 直播会话管理
    async def create_live_session(self, account_id: int, live_id: str, start_time: datetime, **kwargs) -> Optional[LiveSession]:
        async with self.async_session() as session:
            existing = await session.execute(select(LiveSession).where(LiveSession.live_id == live_id))
            if existing.scalar_one_or_none():
                return None

            session_obj = LiveSession(account_id=account_id, live_id=live_id, start_time=start_time, status="live", **kwargs)
            session.add(session_obj)
            await session.commit()
            await session.refresh(session_obj)
            return session_obj

    async def update_live_session(self, session_id: int, **kwargs) -> bool:
        async with self.async_session() as session:
            kwargs["updated_at"] = datetime.now()
            result = await session.execute(update(LiveSession).where(LiveSession.id == session_id).values(**kwargs))
            await session.commit()
            return result.rowcount > 0

    async def end_live_session(self, session_id: int, end_time: datetime):
        async with self.async_session() as session:
            result = await session.execute(select(LiveSession).where(LiveSession.id == session_id))
            live_session = result.scalar_one_or_none()
            if live_session:
                duration = (end_time - live_session.start_time).total_seconds() / 60
                await session.execute(
                    update(LiveSession).where(LiveSession.id == session_id).values(
                        end_time=end_time,
                        duration_minutes=int(duration),
                        status="ended",
                        updated_at=datetime.now(),
                    )
                )
                await session.commit()

    async def get_active_live_sessions(self) -> List[LiveSession]:
        async with self.async_session() as session:
            result = await session.execute(select(LiveSession).where(LiveSession.status == "live").order_by(LiveSession.start_time.desc()))
            return list(result.scalars().all())

    async def get_live_session_by_live_id(self, live_id: str) -> Optional[LiveSession]:
        async with self.async_session() as session:
            result = await session.execute(select(LiveSession).where(LiveSession.live_id == live_id))
            return result.scalar_one_or_none()

    # 直播快照管理
    async def add_live_snapshot(self, session_id: int, snapshot_data: Dict[str, Any]) -> LiveSnapshot:
        async with self.async_session() as session:
            snapshot = LiveSnapshot(
                session_id=session_id,
                snapshot_time=snapshot_data.get("snapshot_time", datetime.now()),
                viewers_count=snapshot_data.get("viewers_count"),
                enter_count=snapshot_data.get("enter_count"),
                likes_count=snapshot_data.get("likes_count"),
                comments_count=snapshot_data.get("comments_count"),
                shares_count=snapshot_data.get("shares_count"),
                gifts_value=snapshot_data.get("gifts_value"),
                products=snapshot_data.get("products", []),
                raw_data=snapshot_data.get("raw_data", {}),
            )
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)
            return snapshot

    async def get_session_snapshots(self, session_id: int, limit: int = 100) -> List[LiveSnapshot]:
        async with self.async_session() as session:
            result = await session.execute(
                select(LiveSnapshot).where(LiveSnapshot.session_id == session_id).order_by(LiveSnapshot.snapshot_time.desc()).limit(limit)
            )
            return list(result.scalars().all())

    # 监控日志
    async def add_monitoring_log(self, log_data: Dict[str, Any]) -> MonitoringLog:
        async with self.async_session() as session:
            log = MonitoringLog(
                account_id=log_data.get("account_id"),
                check_time=log_data.get("check_time", datetime.now()),
                is_live=log_data.get("is_live", False),
                live_id=log_data.get("live_id"),
                viewers_count=log_data.get("viewers_count"),
                enter_count=log_data.get("enter_count"),
                response_time_ms=log_data.get("response_time_ms"),
                success=log_data.get("success", True),
                error_message=log_data.get("error_message"),
                risk_status=log_data.get("risk_status", "normal"),
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    # 统计数据查询
    async def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(DISTINCT ls.id) AS total_lives,
                       COUNT(DISTINCT ls.account_id) AS active_accounts,
                       COALESCE(SUM(ls.duration_minutes), 0) AS total_duration,
                       COALESCE(AVG(ls.max_viewers), 0) AS avg_max_viewers,
                       COALESCE(MAX(ls.max_viewers), 0) AS max_viewers,
                       COALESCE(SUM(ls.total_likes), 0) AS total_likes,
                       COALESCE(SUM(ls.total_comments), 0) AS total_comments
                FROM live_sessions ls
                WHERE DATE(ls.start_time) = DATE($1)
                """,
                date,
            )
            return dict(row) if row else {}

    async def get_account_stats(self, account_id: int, days: int = 7) -> Dict[str, Any]:
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS total_lives,
                       COALESCE(AVG(duration_minutes), 0) AS avg_duration,
                       COALESCE(SUM(duration_minutes), 0) AS total_duration,
                       COALESCE(AVG(max_viewers), 0) AS avg_max_viewers,
                       COALESCE(MAX(max_viewers), 0) AS max_viewers,
                       COALESCE(AVG(max_enter_count), 0) AS avg_enter_count,
                       COALESCE(MAX(max_enter_count), 0) AS max_enter_count,
                       COALESCE(SUM(total_likes), 0) AS total_likes,
                       COALESCE(SUM(total_comments), 0) AS total_comments,
                       COALESCE(SUM(total_gifts), 0) AS total_gifts
                FROM live_sessions
                WHERE account_id = $1 AND start_time >= $2
                """,
                account_id,
                datetime.now() - timedelta(days=days),
            )
            return dict(row) if row else {}

    async def get_competitor_ranking(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT ma.id AS account_id,
                       ma.douyin_id,
                       ma.nickname,
                       COUNT(ls.id) AS live_count,
                       COALESCE(SUM(ls.duration_minutes), 0) AS total_duration_minutes,
                       COALESCE(AVG(ls.duration_minutes), 0) AS avg_duration_minutes,
                       COALESCE(MAX(ls.max_viewers), 0) AS peak_viewers,
                       COALESCE(AVG(ls.avg_viewers), 0) AS avg_viewers,
                       COALESCE(MAX(ls.max_enter_count), 0) AS peak_enter_count,
                       COALESCE(AVG(ls.avg_enter_count), 0) AS avg_enter_count,
                       COALESCE(SUM(ls.total_likes), 0) AS total_likes,
                       COALESCE(SUM(ls.total_comments), 0) AS total_comments,
                       MAX(ls.start_time) AS last_live_time
                FROM monitored_accounts ma
                LEFT JOIN live_sessions ls ON ls.account_id = ma.id AND ls.start_time >= $1
                WHERE ma.is_active = TRUE
                GROUP BY ma.id, ma.douyin_id, ma.nickname
                ORDER BY peak_viewers DESC, total_duration_minutes DESC
                LIMIT $2
                """,
                datetime.now() - timedelta(days=days),
                limit,
            )
            return [dict(row) for row in rows]

    async def get_live_calendar(self, days: int = 7, limit: int = 200) -> List[Dict[str, Any]]:
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT ls.id,
                       ls.live_id,
                       ls.title,
                       ls.live_url,
                       ls.start_time,
                       ls.end_time,
                       ls.duration_minutes,
                       ls.max_viewers,
                       ls.avg_viewers,
                       ls.max_enter_count,
                       ls.avg_enter_count,
                       ls.status,
                       ma.douyin_id,
                       ma.nickname
                FROM live_sessions ls
                JOIN monitored_accounts ma ON ma.id = ls.account_id
                WHERE ls.start_time >= $1
                ORDER BY ls.start_time DESC
                LIMIT $2
                """,
                datetime.now() - timedelta(days=days),
                limit,
            )
            return [dict(row) for row in rows]

    async def get_operations_overview(self, days: int = 7) -> Dict[str, Any]:
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(DISTINCT ma.id) AS monitored_accounts,
                       COUNT(ls.id) AS live_count,
                       COALESCE(SUM(ls.duration_minutes), 0) AS total_duration_minutes,
                       COALESCE(MAX(ls.max_viewers), 0) AS peak_viewers,
                       COALESCE(AVG(ls.avg_viewers), 0) AS avg_viewers,
                       COALESCE(MAX(ls.max_enter_count), 0) AS peak_enter_count,
                       COALESCE(AVG(ls.avg_enter_count), 0) AS avg_enter_count
                FROM monitored_accounts ma
                LEFT JOIN live_sessions ls ON ls.account_id = ma.id AND ls.start_time >= $1
                WHERE ma.is_active = TRUE
                """,
                datetime.now() - timedelta(days=days),
            )
            return dict(row) if row else {}

    async def cleanup_old_data(self, cutoff_date: datetime) -> int:
        async with self.async_session() as session:
            log_result = await session.execute(delete(MonitoringLog).where(MonitoringLog.check_time < cutoff_date))
            snapshot_result = await session.execute(
                delete(LiveSnapshot).where(
                    and_(
                        LiveSnapshot.snapshot_time < cutoff_date,
                        ~LiveSnapshot.session_id.in_(select(LiveSession.id).where(LiveSession.status == "live")),
                    )
                )
            )
            await session.commit()
            return log_result.rowcount + snapshot_result.rowcount

    # Redis操作
    async def set_cache(self, key: str, value: Any, expire: int = 300):
        if not self.redis:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        await self.redis.setex(key, expire, value)

    async def get_cache(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def delete_cache(self, key: str):
        if self.redis:
            await self.redis.delete(key)

    async def increment_counter(self, key: str, amount: int = 1) -> int:
        if not self.redis:
            return 0
        return await self.redis.incrby(key, amount)

    async def add_to_set(self, key: str, value: str):
        if self.redis:
            await self.redis.sadd(key, value)

    async def get_set_members(self, key: str) -> List[str]:
        if not self.redis:
            return []
        return await self.redis.smembers(key)

    async def remove_from_set(self, key: str, value: str):
        if self.redis:
            await self.redis.srem(key, value)
