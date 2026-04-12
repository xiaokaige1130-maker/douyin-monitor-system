"""
通知模块
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

import aiohttp
from loguru import logger

from core.config import Config

class Notifier:
    """通知发送器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.notification_config = config.get_notification_config()
        
    async def send_notification(self, 
                               title: str, 
                               message: str, 
                               notification_type: str = "info",
                               data: Optional[Dict[str, Any]] = None) -> bool:
        """发送通知"""
        
        if not self.notification_config["enabled"]:
            logger.debug("通知功能已禁用")
            return False
            
        success = True
        
        # 发送到钉钉
        if self.notification_config["dingtalk"]:
            dingtalk_success = await self._send_dingtalk(title, message, data)
            success = success and dingtalk_success
            
        # 发送到微信
        if self.notification_config["wechat"]:
            wechat_success = await self._send_wechat(title, message, data)
            success = success and wechat_success
            
        # 发送邮件
        if self.notification_config["email"]:
            email_success = await self._send_email(title, message, data)
            success = success and email_success
            
        return success
        
    async def _send_dingtalk(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """发送钉钉通知"""
        try:
            webhook_url = self.notification_config["dingtalk"]
            
            # 构建消息
            text = f"**{title}**\n\n{message}"
            
            if data:
                text += "\n\n**数据详情:**"
                for key, value in data.items():
                    text += f"\n- {key}: {value}"
                    
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": text
                },
                "at": {
                    "isAtAll": False
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"钉钉通知发送成功: {title}")
                        return True
                    else:
                        logger.error(f"钉钉通知发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"发送钉钉通知时出错: {e}")
            return False
            
    async def _send_wechat(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """发送微信通知"""
        try:
            webhook_url = self.notification_config["wechat"]
            
            # 构建消息
            content = f"{title}\n{message}"
            
            if data:
                content += "\n\n数据详情:"
                for key, value in data.items():
                    content += f"\n{key}: {value}"
                    
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"微信通知发送成功: {title}")
                        return True
                    else:
                        logger.error(f"微信通知发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"发送微信通知时出错: {e}")
            return False
            
    async def _send_email(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """发送邮件通知"""
        try:
            email_config = self.notification_config["email"]
            if not email_config:
                return False
                
            recipients = email_config["recipients"]
            if not recipients:
                logger.warning("没有配置邮件接收人")
                return False
                
            # 构建邮件内容
            html_content = f"""
            <html>
            <body>
                <h2>{title}</h2>
                <p>{message}</p>
            """
            
            if data:
                html_content += "<h3>数据详情:</h3><ul>"
                for key, value in data.items():
                    html_content += f"<li><strong>{key}:</strong> {value}</li>"
                html_content += "</ul>"
                
            html_content += f"""
                <hr>
                <p><small>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                <p><small>来自: 抖音监控系统</small></p>
            </body>
            </html>
            """
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[抖音监控] {title}"
            msg['From'] = email_config["username"]
            msg['To'] = ', '.join(recipients)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)
                
            logger.debug(f"邮件通知发送成功: {title}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件通知时出错: {e}")
            return False
            
    async def send_live_start_notification(self, 
                                          account_name: str, 
                                          live_title: str, 
                                          viewers_count: int,
                                          live_url: Optional[str] = None) -> bool:
        """发送直播开始通知"""
        title = f"直播开始: {account_name}"
        message = f"账号 {account_name} 开始直播\n标题: {live_title}\n在线人数: {viewers_count}"
        
        data = {
            "账号": account_name,
            "直播标题": live_title,
            "在线人数": viewers_count,
            "开始时间": datetime.now().strftime("%H:%M:%S")
        }
        
        if live_url:
            data["直播链接"] = live_url
            
        return await self.send_notification(title, message, "live_start", data)
        
    async def send_live_end_notification(self, 
                                        account_name: str, 
                                        duration_minutes: int,
                                        max_viewers: int,
                                        avg_viewers: int,
                                        total_likes: int) -> bool:
        """发送直播结束通知"""
        title = f"直播结束: {account_name}"
        message = f"账号 {account_name} 直播结束\n时长: {duration_minutes}分钟\n最高在线: {max_viewers}\n平均在线: {avg_viewers}\n总点赞: {total_likes}"
        
        data = {
            "账号": account_name,
            "直播时长": f"{duration_minutes}分钟",
            "最高在线人数": max_viewers,
            "平均在线人数": avg_viewers,
            "总点赞数": total_likes,
            "结束时间": datetime.now().strftime("%H:%M:%S")
        }
        
        return await self.send_notification(title, message, "live_end", data)
        
    async def send_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """发送每日报告"""
        title = "抖音监控每日报告"
        
        # 构建报告消息
        message_lines = [
            f"报告时间: {datetime.now().strftime('%Y-%m-%d')}",
            f"监控账号数: {report_data.get('total_accounts', 0)}",
            f"总直播场次: {report_data.get('total_lives', 0)}",
            f"总直播时长: {report_data.get('total_duration', 0)}分钟",
            f"最高在线人数: {report_data.get('max_viewers', 0)}",
        ]
        
        # 添加top直播
        top_lives = report_data.get('top_lives', [])
        if top_lives:
            message_lines.append("\n**热门直播:**")
            for i, live in enumerate(top_lives[:5], 1):
                message_lines.append(f"{i}. {live.get('account')} - {live.get('viewers')}人在线")
                
        message = "\n".join(message_lines)
        
        return await self.send_notification(title, message, "daily_report", report_data)
        
    async def send_error_notification(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """发送错误通知"""
        title = f"监控系统错误: {error_type}"
        message = f"错误类型: {error_type}\n错误信息: {error_message}"
        
        data = {
            "错误类型": error_type,
            "错误信息": error_message,
            "发生时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if context:
            data.update(context)
            
        return await self.send_notification(title, message, "error", data)
        
    async def send_report(self, report: Dict[str, Any]) -> bool:
        """发送报告（通用方法）"""
        report_type = report.get("type", "unknown")
        
        if report_type == "daily":
            return await self.send_daily_report(report)
        elif report_type == "hourly":
            # 处理小时报告
            title = "抖音监控小时报告"
            message = f"时间段: {report.get('period', '未知')}\n直播场次: {report.get('total_lives', 0)}"
            return await self.send_notification(title, message, "hourly_report", report)
        else:
            # 通用报告
            title = report.get("title", "抖音监控报告")
            message = report.get("message", "")
            return await self.send_notification(title, message, "report", report)