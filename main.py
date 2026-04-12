#!/usr/bin/env python3
"""
Douyin Live Stream Monitor
24小时监控抖音同行开播时间、时长、直播间数据
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

from loguru import logger
from dotenv import load_dotenv

from core.config import Config
from core.database import Database
from core.scheduler import Scheduler
from core.monitor import DouyinMonitor
from core.notifier import Notifier
from api.server import start_api_server

# Load environment variables
load_dotenv()

class DouyinMonitorApp:
    """主应用程序类"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.scheduler = Scheduler()
        self.monitor = DouyinMonitor(self.config, self.db)
        self.notifier = Notifier(self.config)
        self.api_task = None
        self.is_running = False
        
        # 设置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """配置日志"""
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.config.log_level
        )
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.config.log_level
        )
        
    async def initialize(self):
        """初始化应用程序"""
        logger.info("正在初始化抖音监控系统...")
        
        # 初始化数据库连接
        await self.db.connect()
        logger.info("数据库连接成功")
        
        # 初始化监控器
        await self.monitor.initialize()
        logger.info("监控器初始化成功")
        
        # 加载监控账号
        accounts = await self.db.get_monitored_accounts()
        logger.info(f"加载了 {len(accounts)} 个监控账号")
        
        # 设置信号处理
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """设置信号处理"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"收到信号 {signum}，正在关闭应用程序...")
        self.is_running = False
        
    async def start_monitoring(self):
        """开始监控任务"""
        logger.info("开始监控任务...")
        self.is_running = True
        
        # 添加定时任务
        await self.scheduler.add_job(
            self.monitor.check_all_accounts,
            minutes=1,  # 每分钟检查一次任务队列
            name="monitor_check"
        )
        
        # 添加数据清理任务（每天凌晨3点）
        await self.scheduler.add_job(
            self._cleanup_old_data,
            hour=3,
            minute=0,
            name="data_cleanup"
        )
        
        # 添加报告生成任务（每小时）
        await self.scheduler.add_job(
            self._generate_hourly_report,
            minutes=60,
            name="hourly_report"
        )
        
        # 启动API服务器（如果启用）
        if self.config.api_enabled:
            self.api_task = asyncio.create_task(start_api_server(self.config, self.db))
            logger.info("API服务器已启动")
        
        # 主循环
        while self.is_running:
            try:
                # 执行调度任务
                await self.scheduler.run_pending()
                
                # 检查是否有直播需要高频监控
                await self.monitor.check_active_lives()
                
                # 短暂休眠避免CPU占用过高
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(5)
                
    async def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            # 保留30天的数据
            cutoff_date = datetime.now() - timedelta(days=30)
            deleted = await self.db.cleanup_old_data(cutoff_date)
            logger.info(f"清理了 {deleted} 条旧数据")
        except Exception as e:
            logger.error(f"清理数据时出错: {e}")
            
    async def _generate_hourly_report(self):
        """生成小时报告"""
        try:
            report = await self.monitor.generate_hourly_report()
            if report:
                await self.notifier.send_report(report)
                logger.info("小时报告已生成并发送")
        except Exception as e:
            logger.error(f"生成报告时出错: {e}")
            
    async def shutdown(self):
        """关闭应用程序"""
        logger.info("正在关闭应用程序...")
        
        self.is_running = False
        
        # 取消API任务
        if self.api_task:
            self.api_task.cancel()
            try:
                await self.api_task
            except asyncio.CancelledError:
                pass
                
        # 关闭监控器
        await self.monitor.shutdown()
        
        # 关闭数据库连接
        await self.db.disconnect()
        
        logger.info("应用程序已关闭")

async def main():
    """主函数"""
    app = DouyinMonitorApp()
    
    try:
        # 初始化
        await app.initialize()
        
        # 开始监控
        await app.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"应用程序出错: {e}")
        raise
    finally:
        # 关闭应用程序
        await app.shutdown()

if __name__ == "__main__":
    # 检查必要的环境变量
    required_env_vars = ["DATABASE_URL", "REDIS_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {missing_vars}")
        logger.info("请设置以下环境变量:")
        for var in missing_vars:
            logger.info(f"  {var}")
        sys.exit(1)
    
    # 运行主程序
    asyncio.run(main())