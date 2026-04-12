"""
数据模型定义
"""

from datetime import datetime
from typing import Optional, List
import json

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, BigInteger, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class MonitoredAccount(Base):
    """监控账号"""
    __tablename__ = "monitored_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    douyin_id = Column(String(100), nullable=False, unique=True, index=True)
    nickname = Column(String(200))
    sec_uid = Column(String(200))
    is_active = Column(Boolean, default=True)
    check_interval_minutes = Column(Integer, default=10)
    last_checked = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    live_sessions = relationship("LiveSession", back_populates="account", cascade="all, delete-orphan")
    monitoring_logs = relationship("MonitoringLog", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MonitoredAccount(id={self.id}, douyin_id='{self.douyin_id}', nickname='{self.nickname}')>"

class LiveSession(Base):
    """直播会话"""
    __tablename__ = "live_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("monitored_accounts.id"), nullable=False, index=True)
    live_id = Column(String(100), nullable=False, unique=True, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    max_viewers = Column(Integer)
    avg_viewers = Column(Integer)
    total_likes = Column(BigInteger, default=0)
    total_comments = Column(BigInteger, default=0)
    total_shares = Column(BigInteger, default=0)
    total_gifts = Column(Float, default=0.0)
    products_count = Column(Integer, default=0)
    status = Column(String(20), default="ended")  # live, ended, error
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    account = relationship("MonitoredAccount", back_populates="live_sessions")
    snapshots = relationship("LiveSnapshot", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LiveSession(id={self.id}, account_id={self.account_id}, live_id='{self.live_id}', status='{self.status}')>"

class LiveSnapshot(Base):
    """直播快照（时间序列数据）"""
    __tablename__ = "live_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("live_sessions.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)
    viewers_count = Column(Integer)
    likes_count = Column(Integer)
    comments_count = Column(Integer)
    shares_count = Column(Integer)
    gifts_value = Column(Float)
    products = Column(JSON)  # JSON数组，存储商品信息
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    session = relationship("LiveSession", back_populates="snapshots")
    
    def get_products(self) -> List[dict]:
        """获取商品列表"""
        if self.products:
            return json.loads(self.products) if isinstance(self.products, str) else self.products
        return []
    
    def __repr__(self):
        return f"<LiveSnapshot(id={self.id}, session_id={self.session_id}, viewers={self.viewers_count})>"

class LiveProduct(Base):
    """直播商品"""
    __tablename__ = "live_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("live_sessions.id"), nullable=False, index=True)
    product_id = Column(String(100))
    product_name = Column(String(500))
    price = Column(Float)
    sales_count = Column(Integer)
    platform = Column(String(50))
    mentioned_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<LiveProduct(id={self.id}, product_name='{self.product_name}', price={self.price})>"

class MonitoringLog(Base):
    """监控日志"""
    __tablename__ = "monitoring_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("monitored_accounts.id"), nullable=False, index=True)
    check_time = Column(DateTime, nullable=False, index=True)
    is_live = Column(Boolean, default=False)
    live_id = Column(String(100))
    viewers_count = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    account = relationship("MonitoredAccount", back_populates="monitoring_logs")
    
    def __repr__(self):
        return f"<MonitoringLog(id={self.id}, account_id={self.account_id}, is_live={self.is_live}, success={self.success})>"

class Alert(Base):
    """告警配置"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)  # live_start, live_end, viewer_threshold, etc.
    condition = Column(JSON, nullable=False)  # JSON条件配置
    channel = Column(String(50), default="email")  # email, dingtalk, wechat
    recipients = Column(JSON)  # JSON数组，接收人列表
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def get_condition(self) -> dict:
        """获取条件配置"""
        if self.condition:
            return json.loads(self.condition) if isinstance(self.condition, str) else self.condition
        return {}
    
    def get_recipients(self) -> List[str]:
        """获取接收人列表"""
        if self.recipients:
            return json.loads(self.recipients) if isinstance(self.recipients, str) else self.recipients
        return []
    
    def __repr__(self):
        return f"<Alert(id={self.id}, name='{self.name}', type='{self.alert_type}')>"