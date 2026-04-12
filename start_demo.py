#!/usr/bin/env python3
"""
抖音监控系统 - 演示模式
在没有抖音Cookie的情况下运行，展示系统功能
"""

import asyncio
import time
from datetime import datetime
import uvicorn
from fastapi import FastAPI
import random

app = FastAPI(title="抖音监控系统 - 演示模式", version="1.0.0")

# 模拟数据
demo_accounts = [
    {"id": "demo_001", "nickname": "测试主播A", "douyin_id": "demo_user_a", "is_live": False},
    {"id": "demo_002", "nickname": "测试主播B", "douyin_id": "demo_user_b", "is_live": True},
]

demo_sessions = []

@app.get("/")
async def root():
    return {
        "message": "抖音监控系统 - 演示模式",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "mode": "demo",
        "note": "系统运行在演示模式，配置抖音Cookie后启用完整功能",
        "endpoints": {
            "/": "系统信息",
            "/api/health": "健康检查",
            "/api/system/status": "系统状态",
            "/api/accounts": "账号列表",
            "/api/sessions": "直播会话"
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgres": "simulated",
            "redis": "simulated",
            "influxdb": "simulated",
            "api": "running",
            "monitor": "simulated"
        },
        "configuration": {
            "douyin_cookie": "not_configured",
            "message": "请配置DOUYIN_COOKIE启用完整监控功能"
        }
    }

@app.get("/api/system/status")
async def system_status():
    return {
        "system": {
            "name": "抖音监控系统",
            "version": "1.0.0",
            "mode": "demo",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - start_time,
            "monitored_accounts": len(demo_accounts)
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
            "1. 获取抖音Cookie（扫码登录后从开发者工具复制）",
            "2. 配置: echo 'DOUYIN_COOKIE=你的Cookie' >> .env",
            "3. 重启系统启用完整监控",
            "4. 添加实际监控账号"
        ]
    }

@app.get("/api/accounts")
async def get_accounts():
    return {
        "accounts": demo_accounts,
        "count": len(demo_accounts),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/sessions")
async def get_sessions():
    return {
        "sessions": demo_sessions[-10:],  # 最近10个会话
        "count": len(demo_sessions),
        "timestamp": datetime.now().isoformat()
    }

async def simulate_monitoring():
    """模拟监控任务"""
    print("👁️  启动模拟监控任务...")
    print("  ⚠️  运行在演示模式（等待抖音Cookie配置）")
    print("  💡 配置DOUYIN_COOKIE后系统将自动切换为完整模式")
    print()
    
    check_count = 0
    
    while True:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"  📊 模拟监控检查 [{current_time}]")
        
        # 模拟检查每个账号
        for account in demo_accounts:
            # 随机切换直播状态
            if random.random() < 0.1:  # 10%概率切换状态
                account["is_live"] = not account["is_live"]
                
                if account["is_live"]:
                    # 开始直播
                    session = {
                        "account_id": account["id"],
                        "nickname": account["nickname"],
                        "start_time": datetime.now().isoformat(),
                        "viewers": random.randint(100, 3000),
                        "likes": random.randint(0, 5000)
                    }
                    demo_sessions.append(session)
                    print(f"    🎬 {account['nickname']}: 开始直播! | 在线: {session['viewers']}人")
                else:
                    # 结束直播
                    if demo_sessions:
                        session = demo_sessions[-1]
                        if session.get("end_time") is None:
                            session["end_time"] = datetime.now().isoformat()
                            duration = (datetime.now() - datetime.fromisoformat(session["start_time"])).seconds // 60
                            print(f"    ⏹️  {account['nickname']}: 直播结束 | 时长: {duration}分钟")
            else:
                # 更新直播数据
                if account["is_live"] and demo_sessions:
                    session = demo_sessions[-1]
                    if session.get("end_time") is None:
                        session["viewers"] = random.randint(100, 3000)
                        session["likes"] += random.randint(10, 100)
                        print(f"    ✅ {account['nickname']}: 直播中 | 在线: {session['viewers']}人")
                else:
                    print(f"    ⏸️  {account['nickname']}: 未开播")
        
        print()
        await asyncio.sleep(10)  # 10秒检查一次

async def main():
    """主函数"""
    print("🎬 抖音监控系统 - 演示模式")
    print("=" * 50)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: http://localhost:8000")
    print(f"健康检查: http://localhost:8000/api/health")
    print("=" * 50)
    print("\n💡 系统状态:")
    print("  - 数据库服务: ✅ 模拟运行")
    print("  - API服务: ✅ 运行中")
    print("  - 监控功能: ⏳ 演示模式")
    print("\n🚀 启用完整功能:")
    print("  1. 获取抖音Cookie（扫码登录后从开发者工具复制）")
    print("  2. 配置到 .env 文件: DOUYIN_COOKIE=你的Cookie")
    print("  3. 重启系统启用完整监控")
    print("=" * 50)
    print()
    
    # 启动监控任务
    monitor_task = asyncio.create_task(simulate_monitoring())
    
    # 启动API服务器
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    await server.serve()

if __name__ == "__main__":
    start_time = time.time()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📢 系统已停止")
    except Exception as e:
        print(f"❌ 系统出错: {e}")