#!/usr/bin/env python3
"""
简化的API测试
"""

from fastapi import FastAPI
import uvicorn
from datetime import datetime

app = FastAPI(title="抖音监控系统 - 测试API")

@app.get("/")
async def root():
    return {
        "message": "抖音监控系统API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "mode": "demo (no douyin cookie)"
        },
        "message": "系统运行中，等待配置抖音Cookie"
    }

@app.get("/api/system/status")
async def system_status():
    return {
        "system": {
            "name": "抖音监控系统",
            "version": "1.0.0",
            "status": "demo_mode",
            "timestamp": datetime.now().isoformat()
        },
        "services": {
            "postgres": "running",
            "redis": "running",
            "influxdb": "running",
            "monitor": "demo_mode"
        },
        "monitoring": {
            "accounts": 0,
            "active_lives": 0,
            "total_checks": 0
        }
    }

@app.get("/api/docs")
async def get_docs():
    """返回API文档信息"""
    return {
        "endpoints": [
            {"method": "GET", "path": "/", "description": "根路径"},
            {"method": "GET", "path": "/api/health", "description": "健康检查"},
            {"method": "GET", "path": "/api/system/status", "description": "系统状态"},
            {"method": "GET", "path": "/api/docs", "description": "API文档"},
        ],
        "note": "完整API需要配置抖音Cookie"
    }

if __name__ == "__main__":
    print("🚀 启动抖音监控系统测试API...")
    print("📍 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("💡 注意: 这是测试版本，需要配置抖音Cookie才能使用完整功能")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )