"""
抖音监控核心模块
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import time
import json

import aiohttp
from loguru import logger

from core.config import Config
from core.database import Database
from core.models import MonitoredAccount, LiveSession

class DouyinMonitor:
    """抖音监控器"""
    
    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.session = None
        self.proxy_config = config.get_proxy_config()
        self.active_lives = {}  # 活跃直播会话缓存
        self.check_queue = asyncio.Queue()
        self.is_initialized = False
        
    async def initialize(self):
        """初始化监控器"""
        if self.is_initialized:
            return
            
        # 创建aiohttp会话
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )
        
        # 加载活跃直播会话
        await self._load_active_lives()
        
        self.is_initialized = True
        logger.info("监控器初始化完成")
        
    async def shutdown(self):
        """关闭监控器"""
        if self.session:
            await self.session.close()
        self.is_initialized = False
        logger.info("监控器已关闭")
        
    async def _load_active_lives(self):
        """加载活跃直播会话"""
        active_sessions = await self.db.get_active_live_sessions()
        for session in active_sessions:
            self.active_lives[session.account_id] = {
                "session_id": session.id,
                "live_id": session.live_id,
                "start_time": session.start_time,
                "last_check": datetime.now()
            }
        logger.info(f"加载了 {len(active_sessions)} 个活跃直播会话")
        
    async def check_all_accounts(self):
        """检查所有账号"""
        try:
            accounts = await self.db.get_monitored_accounts(active_only=True)
            logger.info(f"开始检查 {len(accounts)} 个账号")
            
            # 将账号加入检查队列
            for account in accounts:
                await self.check_queue.put(account)
                
            # 创建并发检查任务
            tasks = []
            for i in range(min(self.config.max_concurrent_checks, len(accounts))):
                task = asyncio.create_task(self._check_worker(f"worker-{i+1}"))
                tasks.append(task)
                
            # 等待所有任务完成
            await self.check_queue.join()
            
            # 取消worker任务
            for task in tasks:
                task.cancel()
                
            # 等待任务取消
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("所有账号检查完成")
            
        except Exception as e:
            logger.error(f"检查所有账号时出错: {e}")
            
    async def _check_worker(self, worker_name: str):
        """检查工作线程"""
        logger.debug(f"工作线程 {worker_name} 启动")
        
        while True:
            try:
                account = await self.check_queue.get()
                
                # 检查是否需要检查该账号
                if await self._should_check_account(account):
                    await self.check_single_account(account)
                else:
                    logger.debug(f"跳过检查账号 {account.douyin_id}")
                    
                self.check_queue.task_done()
                
                # 随机延迟，避免请求过于频繁
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 出错: {e}")
                self.check_queue.task_done()
                await asyncio.sleep(1)
                
        logger.debug(f"工作线程 {worker_name} 停止")
        
    async def _should_check_account(self, account: MonitoredAccount) -> bool:
        """判断是否需要检查账号"""
        # 如果账号有活跃直播，使用更短的检查间隔
        if account.id in self.active_lives:
            check_interval = self.config.check_interval_live
        else:
            check_interval = account.check_interval_minutes or self.config.check_interval_normal
            
        # 检查上次检查时间
        if account.last_checked:
            time_since_last = (datetime.now() - account.last_checked).total_seconds() / 60
            return time_since_last >= check_interval
            
        return True
        
    async def check_single_account(self, account: MonitoredAccount):
        """检查单个账号"""
        start_time = time.time()
        check_time = datetime.now()
        
        try:
            logger.debug(f"正在检查账号: {account.douyin_id} ({account.nickname})")
            
            # 检查账号是否在直播
            is_live, live_data = await self._check_account_live_status(account)
            
            # 记录监控日志
            await self.db.add_monitoring_log({
                "account_id": account.id,
                "check_time": check_time,
                "is_live": is_live,
                "live_id": live_data.get("live_id") if is_live else None,
                "viewers_count": live_data.get("viewers_count") if is_live else None,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": True
            })
            
            # 更新账号最后检查时间
            await self.db.update_account_last_checked(account.id, check_time)
            
            # 处理直播状态
            if is_live:
                await self._handle_live_status(account, live_data)
            else:
                await self._handle_non_live_status(account)
                
            logger.debug(f"账号 {account.douyin_id} 检查完成，直播状态: {is_live}")
            
        except Exception as e:
            logger.error(f"检查账号 {account.douyin_id} 时出错: {e}")
            
            # 记录错误日志
            await self.db.add_monitoring_log({
                "account_id": account.id,
                "check_time": check_time,
                "is_live": False,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": False,
                "error_message": str(e)
            })
            
    async def _check_account_live_status(self, account: MonitoredAccount) -> Tuple[bool, Dict[str, Any]]:
        """检查账号直播状态"""
        # 这里实现抖音直播状态检查逻辑
        # 由于抖音API限制，这里提供两种实现方式
        
        # 方法1: 使用抖音Web API（需要cookie/token）
        if self.config.douyin_cookie:
            return await self._check_via_web_api(account)
        
        # 方法2: 模拟浏览器访问（更稳定但较慢）
        return await self._check_via_browser(account)
        
    async def _check_via_web_api(self, account: MonitoredAccount) -> Tuple[bool, Dict[str, Any]]:
        """通过Web API检查直播状态"""
        # 这里需要实现抖音Web API调用
        # 由于API可能变化，这里提供伪代码
        
        try:
            url = f"https://www.douyin.com/aweme/v1/web/live/room/info/?aid=6383&live_id={account.douyin_id}"
            
            headers = {
                "Cookie": self.config.douyin_cookie,
                "Referer": "https://www.douyin.com/",
            }
            
            async with self.session.get(url, headers=headers, proxy=self.proxy_config) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status_code") == 0:
                        live_info = data.get("data", {})
                        if live_info.get("status") == 2:  # 2表示直播中
                            return True, {
                                "live_id": live_info.get("room_id"),
                                "viewers_count": live_info.get("user_count", 0),
                                "title": live_info.get("title", ""),
                                "cover_url": live_info.get("cover", {}).get("url_list", [""])[0]
                            }
                
                return False, {}
                
        except Exception as e:
            logger.error(f"Web API检查失败: {e}")
            return False, {}
            
    async def _check_via_browser(self, account: MonitoredAccount) -> Tuple[bool, Dict[str, Any]]:
        """通过浏览器检查直播状态"""
        # 这里使用Playwright模拟浏览器访问
        # 由于需要安装浏览器，这里提供伪代码
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.config.headless_browser)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                # 访问抖音主页
                await page.goto(f"https://www.douyin.com/user/{account.douyin_id}")
                await page.wait_for_timeout(3000)
                
                # 检查是否有直播标签或提示
                is_live = False
                live_data = {}
                
                # 尝试查找直播相关元素
                live_indicators = [
                    "//div[contains(text(), '直播中')]",
                    "//div[contains(@class, 'live')]",
                    "//span[contains(text(), '直播')]"
                ]
                
                for indicator in live_indicators:
                    elements = await page.query_selector_all(indicator)
                    if elements:
                        is_live = True
                        
                        # 尝试获取在线人数
                        viewer_elements = await page.query_selector_all("//span[contains(text(), '人在看')]")
                        if viewer_elements:
                            viewer_text = await viewer_elements[0].text_content()
                            import re
                            match = re.search(r'(\d+)', viewer_text)
                            if match:
                                live_data["viewers_count"] = int(match.group(1))
                        
                        break
                
                await browser.close()
                return is_live, live_data
                
        except Exception as e:
            logger.error(f"浏览器检查失败: {e}")
            return False, {}
            
    async def _handle_live_status(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        """处理直播状态"""
        account_id = account.id
        
        if account_id not in self.active_lives:
            # 新直播开始
            await self._handle_live_start(account, live_data)
        else:
            # 直播持续中，更新数据
            await self._handle_live_update(account, live_data)
            
    async def _handle_live_start(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        """处理直播开始"""
        logger.info(f"检测到新直播开始: {account.douyin_id} ({account.nickname})")
        
        # 创建直播会话
        live_session = await self.db.create_live_session(
            account_id=account.id,
            live_id=live_data.get("live_id", f"live_{int(time.time())}"),
            start_time=datetime.now()
        )
        
        if live_session:
            # 添加到活跃直播缓存
            self.active_lives[account.id] = {
                "session_id": live_session.id,
                "live_id": live_session.live_id,
                "start_time": live_session.start_time,
                "last_check": datetime.now()
            }
            
            # 添加初始快照
            await self.db.add_live_snapshot(live_session.id, {
                "snapshot_time": datetime.now(),
                "viewers_count": live_data.get("viewers_count", 0),
                "likes_count": 0,
                "comments_count": 0,
                "shares_count": 0,
                "gifts_value": 0.0,
                "products": []
            })
            
            # 发送通知
            await self._send_live_start_notification(account, live_session, live_data)
            
    async def _handle_live_update(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        """处理直播更新"""
        live_info = self.active_lives[account.id]
        session_id = live_info["session_id"]
        
        # 更新最后检查时间
        self.active_lives[account.id]["last_check"] = datetime.now()
        
        # 添加快照
        await self.db.add_live_snapshot(session_id, {
            "snapshot_time": datetime.now(),
            "viewers_count": live_data.get("viewers_count", 0),
            "likes_count": 0,  # 需要从API获取
            "comments_count": 0,  # 需要从API获取
            "shares_count": 0,  # 需要从API获取
            "gifts_value": 0.0,  # 需要从API获取
            "products": []
        })
        
        # 更新会话统计数据
        await self._update_session_stats(session_id)
        
    async def _handle_non_live_status(self, account: MonitoredAccount):
        """处理非直播状态"""
        account_id = account.id
        
        if account_id in self.active_lives:
            # 直播结束
            await self._handle_live_end(account)
            
    async def _handle_live_end(self, account: MonitoredAccount):
        """处理直播结束"""
        logger.info(f"检测到直播结束: {account.douyin_id} ({account.nickname})")
        
        live_info = self.active_lives.pop(account.id, None)
        if live_info:
            # 结束直播会话
            await self.db.end_live_session(live_info["session_id"], datetime.now())
            
            # 发送通知
            await self._send_live_end_notification(account, live_info)
            
    async def _update_session_stats(self, session_id: int):
        """更新会话统计数据"""
        # 获取会话的所有快照
        snapshots = await self.db.get_session_snapshots(session_id, limit=1000)
        
        if not snapshots:
            return
            
        # 计算统计数据
        viewers = [s.viewers_count for s in snapshots if s.viewers_count]
        max_viewers = max(viewers) if viewers else 0
        avg_viewers = sum(viewers) // len(viewers) if viewers else 0
        
        # 更新会话
        await self.db.update_live_session(session_id, 
            max_viewers=max_viewers,
            avg_viewers=avg_viewers,
            updated_at=datetime.now()
        )
        
    async def check_active_lives(self):
        """检查活跃直播"""
        if not self.active_lives:
            return
            
        current_time = datetime.now()
        accounts_to_check = []
        
        # 找出需要检查的活跃直播
        for account_id, live_info in self.active_lives.items():
            last_check = live_info["last_check"]
            check_interval = timedelta(minutes=self.config.check_interval_live)
            
            if current_time - last_check >= check_interval:
                accounts_to_check.append(account_id)
                
        if accounts_to_check:
            logger.debug(f"需要检查 {len(accounts_to_check)} 个活跃直播")
            
            # 获取账号信息并检查
            for account_id in accounts_to_check:
                account = await self.db.get_account_by_douyin_id(str(account_id))
                if account:
                    await self.check_single_account(account)
                    
    async def _send_live_start_notification(self, account: MonitoredAccount, session: LiveSession, live_data: Dict[str, Any]):
        """发送直播开始通知"""
        # 这里实现通知逻辑
        # 可以发送到钉钉、微信、邮件等
        pass
        
    async def _send_live_end_notification(self, account: MonitoredAccount, live_info: Dict[str, Any]):
        """发送直播结束通知"""
        # 这里实现通知逻辑
        pass
        
    async def generate_hourly_report(self) -> Optional[Dict[str, Any]]:
        """生成小时报告"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            # 获取小时内的统计数据
            # 这里实现报告生成逻辑
            
            report = {
                "period": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "total_lives": 0,
                "active_accounts": 0,
                "total_viewers": 0,
                "top_live": None
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成报告时出错: {e}")
            return None