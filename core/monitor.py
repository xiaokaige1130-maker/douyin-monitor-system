"""
抖音直播监控核心模块
"""

import asyncio
import json
import random
import re
import time
from datetime import datetime, timedelta
from html import unescape
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote

import aiohttp
from loguru import logger

from core.config import Config
from core.database import Database
from core.models import MonitoredAccount, LiveSession


RISK_KEYWORDS = ("验证码", "安全验证", "滑块", "访问过于频繁", "请稍后再试", "verify", "captcha")
LOGIN_KEYWORDS = ("登录", "扫码登录", "passport", "session expired")


class DouyinMonitor:
    """抖音直播监控器。"""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.session = None
        self.proxy_config = config.get_proxy_config()
        self.active_lives = {}
        self.check_queue = asyncio.Queue()
        self.is_initialized = False

    async def initialize(self):
        if self.is_initialized:
            return

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/json,text/plain,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            },
        )
        await self._load_active_lives()
        self.is_initialized = True
        logger.info("监控器初始化完成")

    async def shutdown(self):
        if self.session:
            await self.session.close()
        self.is_initialized = False
        logger.info("监控器已关闭")

    async def _load_active_lives(self):
        active_sessions = await self.db.get_active_live_sessions()
        for session in active_sessions:
            self.active_lives[session.account_id] = {
                "session_id": session.id,
                "live_id": session.live_id,
                "start_time": session.start_time,
                "last_check": datetime.now(),
            }
        logger.info(f"加载了 {len(active_sessions)} 个活跃直播会话")

    async def check_all_accounts(self):
        try:
            accounts = await self.db.get_monitored_accounts(active_only=True)
            logger.info(f"开始检查 {len(accounts)} 个账号")

            for account in accounts:
                await self.check_queue.put(account)

            tasks = [
                asyncio.create_task(self._check_worker(f"worker-{i + 1}"))
                for i in range(min(self.config.max_concurrent_checks, len(accounts)))
            ]
            await self.check_queue.join()

            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("所有账号检查完成")
        except Exception as e:
            logger.error(f"检查所有账号时出错: {e}")

    async def _check_worker(self, worker_name: str):
        logger.debug(f"工作线程 {worker_name} 启动")
        while True:
            try:
                account = await self.check_queue.get()
                if await self._should_check_account(account):
                    await self.check_single_account(account)
                else:
                    logger.debug(f"跳过检查账号 {account.douyin_id}")

                self.check_queue.task_done()
                await asyncio.sleep(random.uniform(self.config.min_request_delay_seconds, self.config.max_request_delay_seconds))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 出错: {e}")
                self.check_queue.task_done()
                await asyncio.sleep(1)
        logger.debug(f"工作线程 {worker_name} 停止")

    async def _should_check_account(self, account: MonitoredAccount) -> bool:
        now = datetime.now()
        if account.cooldown_until and account.cooldown_until > now:
            return False

        check_interval = self.config.check_interval_live if account.id in self.active_lives else (account.check_interval_minutes or self.config.check_interval_normal)
        if account.last_checked:
            time_since_last = (now - account.last_checked).total_seconds() / 60
            return time_since_last >= check_interval
        return True

    async def check_single_account(self, account: MonitoredAccount):
        start_time = time.time()
        check_time = datetime.now()

        try:
            logger.debug(f"正在检查账号: {account.douyin_id} ({account.nickname})")
            is_live, live_data = await self._check_account_live_status(account)
            risk_status = live_data.get("risk_status", "normal")
            success = risk_status not in {"verify_required", "login_required", "blocked", "request_error"}

            await self.db.add_monitoring_log({
                "account_id": account.id,
                "check_time": check_time,
                "is_live": is_live,
                "live_id": live_data.get("live_id") if is_live else None,
                "viewers_count": live_data.get("viewers_count") if is_live else None,
                "enter_count": live_data.get("enter_count") if is_live else None,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": success,
                "error_message": live_data.get("error_message"),
                "risk_status": risk_status,
            })
            await self.db.update_account_last_checked(account.id, check_time)

            if success:
                await self.db.mark_account_success(account.id)
            else:
                await self.db.mark_account_failure(account, live_data.get("error_message", risk_status), risk_status)
                if account.id in self.active_lives and risk_status in {"verify_required", "login_required", "blocked"}:
                    logger.warning(f"账号 {account.douyin_id} 触发 {risk_status}，保留直播状态等待下次确认")
                    return

            if is_live:
                await self._handle_live_status(account, live_data)
            else:
                await self._handle_non_live_status(account)

            logger.debug(f"账号 {account.douyin_id} 检查完成，直播状态: {is_live}, 风险状态: {risk_status}")
        except Exception as e:
            logger.error(f"检查账号 {account.douyin_id} 时出错: {e}")
            await self.db.add_monitoring_log({
                "account_id": account.id,
                "check_time": check_time,
                "is_live": False,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "success": False,
                "error_message": str(e),
                "risk_status": "error",
            })
            await self.db.mark_account_failure(account, str(e), "error")

    async def _check_account_live_status(self, account: MonitoredAccount) -> Tuple[bool, Dict[str, Any]]:
        live_url = self._build_live_url(account)
        headers = {"Referer": "https://www.douyin.com/"}
        if self.config.douyin_cookie:
            headers["Cookie"] = self.config.douyin_cookie

        for attempt in range(self.config.max_retries + 1):
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                async with self.session.get(live_url, headers=headers, proxy=self.proxy_config, allow_redirects=True) as response:
                    text = await response.text(errors="ignore")
                    risk_status = self._detect_risk_status(response.status, text)
                    if risk_status != "normal":
                        return False, {
                            "risk_status": risk_status,
                            "error_message": f"Douyin page returned {risk_status}, http={response.status}",
                            "source_url": str(response.url),
                        }

                    live_data = self._extract_live_data(text, account, str(response.url))
                    if live_data.get("is_live"):
                        return True, live_data

                    if account.live_room_id:
                        api_live = await self._check_room_api(account)
                        if api_live.get("is_live"):
                            return True, api_live

                    return False, {"risk_status": "normal", "source_url": str(response.url)}
            except Exception as e:
                if attempt >= self.config.max_retries:
                    return False, {"risk_status": "request_error", "error_message": str(e), "source_url": live_url}
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        return False, {"risk_status": "request_error", "error_message": "unknown request error", "source_url": live_url}

    async def _check_room_api(self, account: MonitoredAccount) -> Dict[str, Any]:
        headers = {"Referer": "https://www.douyin.com/"}
        if self.config.douyin_cookie:
            headers["Cookie"] = self.config.douyin_cookie

        url = f"https://www.douyin.com/aweme/v1/web/live/room/info/?aid=6383&room_id={quote(account.live_room_id)}"
        try:
            async with self.session.get(url, headers=headers, proxy=self.proxy_config) as response:
                text = await response.text(errors="ignore")
                risk_status = self._detect_risk_status(response.status, text)
                if risk_status != "normal":
                    return {"is_live": False, "risk_status": risk_status, "error_message": f"room api {risk_status}"}
                data = json.loads(text)
        except Exception as e:
            return {"is_live": False, "risk_status": "request_error", "error_message": str(e)}

        live_info = data.get("data") or data.get("room") or {}
        status = str(live_info.get("status") or live_info.get("live_status") or "")
        is_live = status in {"2", "live", "LIVE"}
        if not is_live:
            return {"is_live": False, "risk_status": "normal"}

        return {
            "is_live": True,
            "risk_status": "normal",
            "live_id": str(live_info.get("room_id") or account.live_room_id),
            "room_id": str(live_info.get("room_id") or account.live_room_id),
            "live_url": account.live_url or self._build_live_url(account),
            "title": live_info.get("title", ""),
            "viewers_count": self._to_int(live_info.get("user_count") or live_info.get("viewer_count")),
            "enter_count": self._to_int(live_info.get("user_count") or live_info.get("viewer_count")),
            "likes_count": self._to_int(live_info.get("like_count")),
            "comments_count": self._to_int(live_info.get("comment_count")),
            "shares_count": self._to_int(live_info.get("share_count")),
            "products": live_info.get("products") or [],
            "raw_data": live_info,
        }

    def _build_live_url(self, account: MonitoredAccount) -> str:
        if account.live_url:
            return account.live_url
        if account.sec_uid:
            return f"https://www.douyin.com/user/{account.sec_uid}"
        return f"https://www.douyin.com/user/{account.douyin_id}"

    def _detect_risk_status(self, status_code: int, text: str) -> str:
        low = text.lower()
        if status_code in {401, 403}:
            return "blocked"
        if status_code in {429, 418}:
            return "verify_required"
        if any(keyword.lower() in low for keyword in RISK_KEYWORDS):
            return "verify_required"
        if self.config.douyin_cookie and any(keyword.lower() in low for keyword in LOGIN_KEYWORDS) and "直播" not in text:
            return "login_required"
        return "normal"

    def _extract_live_data(self, html: str, account: MonitoredAccount, source_url: str) -> Dict[str, Any]:
        text = unescape(html)
        json_blocks = self._extract_json_blocks(text)
        merged_text = "\n".join(json.dumps(block, ensure_ascii=False) for block in json_blocks[:6]) if json_blocks else text[:80000]

        is_live = any(token in merged_text for token in ("直播中", "LIVE", "live_status", "room_id", "web_rid"))
        room_id = self._first_match(merged_text, [r'"room_id"\s*:\s*"?(\d+)"?', r'"roomId"\s*:\s*"?(\d+)"?', r'room_id=(\d+)'])
        web_rid = self._first_match(merged_text, [r'"web_rid"\s*:\s*"([^"]+)"', r'"webRid"\s*:\s*"([^"]+)"'])
        status = self._first_match(merged_text, [r'"status"\s*:\s*"?(\d+)"?', r'"live_status"\s*:\s*"?(\d+)"?'])
        if status and status not in {"2", "1"} and not room_id:
            is_live = False

        viewers = self._extract_metric(merged_text, ["user_count", "viewer_count", "room_user_count", "online_count"])
        enter_count = self._extract_metric(merged_text, ["enter_count", "user_count", "viewer_count", "room_user_count"])
        likes = self._extract_metric(merged_text, ["like_count", "digg_count", "total_like_count"])
        comments = self._extract_metric(merged_text, ["comment_count", "comments_count"])
        shares = self._extract_metric(merged_text, ["share_count", "share_total"])
        title = self._first_match(merged_text, [r'"title"\s*:\s*"([^"]{1,120})"', r'"room_title"\s*:\s*"([^"]{1,120})"']) or ""

        if not is_live:
            return {"is_live": False, "risk_status": "normal", "source_url": source_url}

        live_id = room_id or web_rid or f"{account.douyin_id}_{int(time.time())}"
        return {
            "is_live": True,
            "risk_status": "normal",
            "live_id": live_id,
            "room_id": room_id,
            "live_url": source_url,
            "title": title,
            "viewers_count": viewers,
            "enter_count": enter_count or viewers,
            "likes_count": likes,
            "comments_count": comments,
            "shares_count": shares,
            "products": self._extract_products(merged_text),
            "raw_data": {"room_id": room_id, "web_rid": web_rid, "status": status, "source_url": source_url},
        }

    def _extract_json_blocks(self, html: str):
        blocks = []
        patterns = [
            r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
            r'<script id="SIGI_STATE" type="application/json">(.*?)</script>',
            r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, html, re.S):
                raw = unescape(match.group(1))
                try:
                    if "%" in raw[:200]:
                        from urllib.parse import unquote
                        raw = unquote(raw)
                    blocks.append(json.loads(raw))
                except Exception:
                    continue
        return blocks

    def _extract_metric(self, text: str, keys) -> Optional[int]:
        for key in keys:
            value = self._first_match(text, [rf'"{key}"\s*:\s*"?([0-9.]+万?)"?'])
            if value is not None:
                return self._to_int(value)
        return None

    def _extract_products(self, text: str):
        products = []
        for match in re.finditer(r'"title"\s*:\s*"([^"]{2,80})"[^{}]{0,300}"price"\s*:\s*"?([0-9.]+)"?', text):
            products.append({"product_name": match.group(1), "price": float(match.group(2))})
            if len(products) >= 20:
                break
        return products

    def _first_match(self, text: str, patterns) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.S)
            if match:
                return match.group(1)
        return None

    def _to_int(self, value) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        multiplier = 10000 if text.endswith("万") else 1
        text = text.rstrip("万")
        try:
            return int(float(text) * multiplier)
        except ValueError:
            return None

    async def _handle_live_status(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        if account.id not in self.active_lives:
            await self._handle_live_start(account, live_data)
        else:
            await self._handle_live_update(account, live_data)

    async def _handle_live_start(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        logger.info(f"检测到新直播开始: {account.douyin_id} ({account.nickname})")
        live_session = await self.db.create_live_session(
            account_id=account.id,
            live_id=live_data.get("live_id", f"live_{account.id}_{int(time.time())}"),
            start_time=datetime.now(),
            room_id=live_data.get("room_id"),
            live_url=live_data.get("live_url"),
            title=live_data.get("title"),
        )

        if live_session:
            self.active_lives[account.id] = {
                "session_id": live_session.id,
                "live_id": live_session.live_id,
                "start_time": live_session.start_time,
                "last_check": datetime.now(),
            }
            await self._add_snapshot_and_update_stats(live_session.id, live_data)
            await self._send_live_start_notification(account, live_session, live_data)

    async def _handle_live_update(self, account: MonitoredAccount, live_data: Dict[str, Any]):
        live_info = self.active_lives[account.id]
        self.active_lives[account.id]["last_check"] = datetime.now()
        await self._add_snapshot_and_update_stats(live_info["session_id"], live_data)

    async def _add_snapshot_and_update_stats(self, session_id: int, live_data: Dict[str, Any]):
        await self.db.add_live_snapshot(session_id, {
            "snapshot_time": datetime.now(),
            "viewers_count": live_data.get("viewers_count"),
            "enter_count": live_data.get("enter_count"),
            "likes_count": live_data.get("likes_count"),
            "comments_count": live_data.get("comments_count"),
            "shares_count": live_data.get("shares_count"),
            "gifts_value": live_data.get("gifts_value", 0.0),
            "products": live_data.get("products", []),
            "raw_data": live_data.get("raw_data", {}),
        })
        await self._update_session_stats(session_id)

    async def _handle_non_live_status(self, account: MonitoredAccount):
        if account.id in self.active_lives:
            await self._handle_live_end(account)

    async def _handle_live_end(self, account: MonitoredAccount):
        logger.info(f"检测到直播结束: {account.douyin_id} ({account.nickname})")
        live_info = self.active_lives.pop(account.id, None)
        if live_info:
            await self.db.end_live_session(live_info["session_id"], datetime.now())
            await self._send_live_end_notification(account, live_info)

    async def _update_session_stats(self, session_id: int):
        snapshots = await self.db.get_session_snapshots(session_id, limit=2000)
        if not snapshots:
            return

        viewers = [s.viewers_count for s in snapshots if s.viewers_count is not None]
        enters = [s.enter_count for s in snapshots if s.enter_count is not None]
        likes = [s.likes_count for s in snapshots if s.likes_count is not None]
        comments = [s.comments_count for s in snapshots if s.comments_count is not None]
        shares = [s.shares_count for s in snapshots if s.shares_count is not None]
        products_count = max((len(s.get_products()) for s in snapshots), default=0)

        await self.db.update_live_session(
            session_id,
            max_viewers=max(viewers) if viewers else 0,
            avg_viewers=int(sum(viewers) / len(viewers)) if viewers else 0,
            max_enter_count=max(enters) if enters else 0,
            avg_enter_count=int(sum(enters) / len(enters)) if enters else 0,
            total_likes=max(likes) if likes else 0,
            total_comments=max(comments) if comments else 0,
            total_shares=max(shares) if shares else 0,
            products_count=products_count,
        )

    async def check_active_lives(self):
        if not self.active_lives:
            return

        current_time = datetime.now()
        accounts_to_check = []
        for account_id, live_info in self.active_lives.items():
            if current_time - live_info["last_check"] >= timedelta(minutes=self.config.check_interval_live):
                accounts_to_check.append(account_id)

        for account_id in accounts_to_check:
            account = await self.db.get_account_by_id(account_id)
            if account:
                await self.check_single_account(account)

    async def _send_live_start_notification(self, account: MonitoredAccount, session: LiveSession, live_data: Dict[str, Any]):
        logger.info(f"直播开始: {account.nickname or account.douyin_id}, 在线={live_data.get('viewers_count')}, 进店={live_data.get('enter_count')}")

    async def _send_live_end_notification(self, account: MonitoredAccount, live_info: Dict[str, Any]):
        logger.info(f"直播结束: {account.nickname or account.douyin_id}, session={live_info.get('session_id')}")

    async def generate_hourly_report(self) -> Optional[Dict[str, Any]]:
        try:
            ranking = await self.db.get_competitor_ranking(days=1, limit=5)
            return {
                "type": "hourly",
                "period": f"{(datetime.now() - timedelta(hours=1)).strftime('%H:%M')} - {datetime.now().strftime('%H:%M')}",
                "total_lives": sum(1 for row in ranking if row.get("live_count")),
                "top_lives": ranking,
            }
        except Exception as e:
            logger.error(f"生成报告时出错: {e}")
            return None
