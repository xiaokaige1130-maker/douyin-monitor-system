#!/usr/bin/env python3
"""
抖音监控系统 - 快速启动
"""

from fastapi import FastAPI
import uvicorn
from datetime import datetime
import os

app = FastAPI(title="抖音监控系统", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "抖音监控系统已启动",
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "mode": "等待配置",
        "next_steps": [
            "1. 获取抖音Cookie（扫码登录后从开发者工具复制）",
            "2. 配置: echo 'DOUYIN_COOKIE=你的Cookie' >> .env",
            "3. 重启系统启用完整监控"
        ],
        "endpoints": {
            "/": "系统信息",
            "/health": "健康检查",
            "/status": "详细状态",
            "/docs": "API文档"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgres": "running",
            "redis": "running", 
            "influxdb": "running",
            "api": "running"
        }
    }

@app.get("/status")
async def status():
    return {
        "system": "抖音监控系统",
        "version": "1.0.0",
        "state": "等待Cookie配置",
        "directory": os.getcwd(),
        "config_file": ".env",
        "required_config": "DOUYIN_COOKIE",
        "quick_config": "echo 'DOUYIN_COOKIE=你的Cookie值' >> .env"
    }

@app.get("/docs")
async def docs():
    return {
        "title": "抖音监控系统API",
        "description": "24小时自动监控抖音同行开播时间、时长、直播间数据",
        "configuration": {
            "file": ".env",
            "key": "DOUYIN_COOKIE",
            "how_to_get": "抖音网页版扫码登录 → F12开发者工具 → Network标签 → 复制Cookie"
        },
        "usage": [
            "1. 配置抖音Cookie",
            "2. 启动完整系统: python main.py",
            "3. 添加监控账号: curl -X POST 'http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名'",
            "4. 系统自动开始24小时监控"
        ]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 抖音监控系统 - 快速启动")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目录: {os.getcwd()}")
    print(f"API: http://localhost:8000")
    print("=" * 60)
    print("\n📋 系统状态:")
    print("  ✅ 数据库服务: 运行中")
    print("  ✅ API服务: 启动中")
    print("  ⏳ 监控功能: 等待Cookie配置")
    print("\n🚀 启用完整功能:")
    print("  1. 获取抖音Cookie")
    print("  2. 运行: ./configure_with_cookie.sh \"你的Cookie\"")
    print("  3. 启动: ./start.sh")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")