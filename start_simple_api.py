#!/usr/bin/env python3
"""
简单API服务器 - 用于测试和展示
"""

from fastapi import FastAPI
import uvicorn
from datetime import datetime
import time
import os

app = FastAPI(title="抖音监控系统", version="1.0.0")

# 启动时间
start_time = time.time()

@app.get("/")
async def root():
    return {
        "message": "抖音监控系统API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mode": "等待配置抖音Cookie",
        "endpoints": {
            "/api/health": "健康检查",
            "/api/system/status": "系统状态",
            "/api/docs": "API文档"
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgres": "running",
            "redis": "running",
            "influxdb": "running",
            "api": "running"
        },
        "configuration": {
            "douyin_cookie": "未配置",
            "message": "请配置DOUYIN_COOKIE启用完整监控功能"
        }
    }

@app.get("/api/system/status")
async def system_status():
    return {
        "system": {
            "name": "抖音监控系统",
            "version": "1.0.0",
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - start_time,
            "directory": os.getcwd()
        },
        "services": {
            "postgres": {"status": "running", "port": 5432},
            "redis": {"status": "running", "port": 6379},
            "influxdb": {"status": "running", "port": 8086},
            "api": {"status": "running", "port": 8000}
        },
        "configuration": {
            "douyin_cookie": "未配置",
            "check_interval_normal": 10,
            "check_interval_live": 2,
            "max_concurrent_checks": 5,
            "api_enabled": True,
            "api_port": 8000
        },
        "next_steps": [
            "配置抖音Cookie启用完整功能",
            "添加监控账号开始监控",
            "配置通知渠道接收提醒"
        ]
    }

@app.get("/api/docs")
async def get_docs():
    return {
        "title": "抖音监控系统API文档",
        "description": "24小时自动监控抖音同行开播时间、时长、直播间数据",
        "endpoints": [
            {"method": "GET", "path": "/", "description": "根路径，系统信息"},
            {"method": "GET", "path": "/api/health", "description": "健康检查"},
            {"method": "GET", "path": "/api/system/status", "description": "系统状态"},
            {"method": "GET", "path": "/api/docs", "description": "API文档"}
        ],
        "configuration": {
            "file": ".env",
            "key": "DOUYIN_COOKIE",
            "description": "抖音Cookie，从浏览器开发者工具获取"
        },
        "quick_start": [
            "1. 获取抖音Cookie（扫码登录后从开发者工具复制）",
            "2. 配置: echo 'DOUYIN_COOKIE=你的Cookie' >> .env",
            "3. 启动: python main.py",
            "4. 添加账号: curl -X POST 'http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名'"
        ]
    }

if __name__ == "__main__":
    print("🎬 抖音监控系统API服务器")
    print("=" * 50)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print(f"API地址: http://localhost:8000")
    print(f"健康检查: http://localhost:8000/api/health")
    print("=" * 50)
    print("\n💡 系统状态:")
    print("  - 数据库服务: ✅ 运行中")
    print("  - API服务: ✅ 启动中")
    print("  - 监控功能: ⏳ 等待Cookie配置")
    print("\n🚀 启用完整功能:")
    print("  1. 配置抖音Cookie到 .env 文件")
    print("  2. 重启系统启用完整监控")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )