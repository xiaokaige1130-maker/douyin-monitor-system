"""
配置管理模块
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()


def _int_env(name: str, default: str) -> int:
    return int(os.getenv(name, default))


@dataclass
class Config:
    """应用程序配置。"""

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql+asyncpg://douyin:douyin123@localhost:5432/douyin_monitor"))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    influxdb_url: str = field(default_factory=lambda: os.getenv("INFLUXDB_URL", "http://localhost:8086"))
    influxdb_token: str = field(default_factory=lambda: os.getenv("INFLUXDB_TOKEN", "douyin-token-123"))
    influxdb_org: str = field(default_factory=lambda: os.getenv("INFLUXDB_ORG", "douyin"))
    influxdb_bucket: str = field(default_factory=lambda: os.getenv("INFLUXDB_BUCKET", "douyin_data"))

    check_interval_normal: int = field(default_factory=lambda: _int_env("CHECK_INTERVAL_NORMAL", "10"))
    check_interval_live: int = field(default_factory=lambda: _int_env("CHECK_INTERVAL_LIVE", "2"))
    max_concurrent_checks: int = field(default_factory=lambda: _int_env("MAX_CONCURRENT_CHECKS", "3"))

    min_request_delay_seconds: int = field(default_factory=lambda: _int_env("MIN_REQUEST_DELAY_SECONDS", "2"))
    max_request_delay_seconds: int = field(default_factory=lambda: _int_env("MAX_REQUEST_DELAY_SECONDS", "8"))
    account_cooldown_minutes: int = field(default_factory=lambda: _int_env("ACCOUNT_COOLDOWN_MINUTES", "30"))
    failure_cooldown_threshold: int = field(default_factory=lambda: _int_env("FAILURE_COOLDOWN_THRESHOLD", "3"))
    risk_cooldown_minutes: int = field(default_factory=lambda: _int_env("RISK_COOLDOWN_MINUTES", "180"))

    douyin_cookie: Optional[str] = field(default_factory=lambda: os.getenv("DOUYIN_COOKIE"))
    douyin_token: Optional[str] = field(default_factory=lambda: os.getenv("DOUYIN_TOKEN"))

    proxy_enabled: bool = field(default_factory=lambda: os.getenv("PROXY_ENABLED", "false").lower() == "true")
    proxy_url: Optional[str] = field(default_factory=lambda: os.getenv("PROXY_URL"))

    notification_enabled: bool = field(default_factory=lambda: os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true")
    dingtalk_webhook: Optional[str] = field(default_factory=lambda: os.getenv("DINGTALK_WEBHOOK"))
    wechat_webhook: Optional[str] = field(default_factory=lambda: os.getenv("WECHAT_WEBHOOK"))
    email_smtp_server: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_SMTP_SERVER"))
    email_smtp_port: int = field(default_factory=lambda: _int_env("EMAIL_SMTP_PORT", "587"))
    email_username: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_USERNAME"))
    email_password: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD"))
    email_recipients: str = field(default_factory=lambda: os.getenv("EMAIL_RECIPIENTS", ""))

    api_enabled: bool = field(default_factory=lambda: os.getenv("API_ENABLED", "true").lower() == "true")
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: _int_env("API_PORT", "8000"))

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/app.log"))
    data_retention_days: int = field(default_factory=lambda: _int_env("DATA_RETENTION_DAYS", "30"))

    headless_browser: bool = field(default_factory=lambda: os.getenv("HEADLESS_BROWSER", "true").lower() == "true")
    browser_timeout: int = field(default_factory=lambda: _int_env("BROWSER_TIMEOUT", "30"))

    request_timeout: int = field(default_factory=lambda: _int_env("REQUEST_TIMEOUT", "30"))
    max_retries: int = field(default_factory=lambda: _int_env("MAX_RETRIES", "2"))
    retry_delay: int = field(default_factory=lambda: _int_env("RETRY_DELAY", "5"))

    def get_database_config(self) -> Dict[str, Any]:
        return {
            "url": self.database_url,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_recycle": 3600,
        }

    def get_asyncpg_dsn(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    def get_redis_config(self) -> Dict[str, Any]:
        return {"url": self.redis_url, "decode_responses": True}

    def get_influxdb_config(self) -> Dict[str, Any]:
        return {
            "url": self.influxdb_url,
            "token": self.influxdb_token,
            "org": self.influxdb_org,
            "bucket": self.influxdb_bucket,
        }

    def get_proxy_config(self) -> Optional[str]:
        if not self.proxy_enabled or not self.proxy_url:
            return None
        return self.proxy_url

    def get_notification_config(self) -> Dict[str, Any]:
        return {
            "enabled": self.notification_enabled,
            "dingtalk": self.dingtalk_webhook,
            "wechat": self.wechat_webhook,
            "email": {
                "smtp_server": self.email_smtp_server,
                "smtp_port": self.email_smtp_port,
                "username": self.email_username,
                "password": self.email_password,
                "recipients": [email.strip() for email in self.email_recipients.split(",") if email.strip()],
            } if self.email_smtp_server else None,
        }

    def get_api_config(self) -> Dict[str, Any]:
        return {
            "enabled": self.api_enabled,
            "host": self.api_host,
            "port": self.api_port,
            "debug": self.log_level == "DEBUG",
        }

    def get_browser_config(self) -> Dict[str, Any]:
        return {
            "headless": self.headless_browser,
            "timeout": self.browser_timeout,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
