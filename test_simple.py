#!/usr/bin/env python3
"""
简化测试版本 - 验证核心功能
"""

import asyncio
import time
from datetime import datetime
import random

async def test_monitor_simulation():
    """测试监控模拟"""
    print("抖音监控系统测试启动...")
    print("=" * 50)
    
    # 模拟的监控账号
    test_accounts = [
        {"id": 1, "douyin_id": "test_account_1", "nickname": "测试主播1", "is_live": False},
        {"id": 2, "douyin_id": "test_account_2", "nickname": "测试主播2", "is_live": True, "viewers": 1500},
        {"id": 3, "douyin_id": "test_account_3", "nickname": "测试主播3", "is_live": False},
    ]
    
    print(f"监控 {len(test_accounts)} 个测试账号")
    print()
    
    for i in range(5):  # 模拟5轮检查
        print(f"第 {i+1} 轮检查 - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        for account in test_accounts:
            # 模拟检查结果
            if account["is_live"]:
                # 模拟在线人数波动
                viewers_change = random.randint(-100, 200)
                account["viewers"] = max(100, account["viewers"] + viewers_change)
                
                print(f"✅ {account['nickname']} 直播中 | 在线: {account['viewers']}人 | 波动: {viewers_change:+d}")
            else:
                # 模拟随机开播
                if random.random() < 0.2:  # 20%概率开播
                    account["is_live"] = True
                    account["viewers"] = random.randint(500, 3000)
                    print(f"🎬 {account['nickname']} 开始直播! | 初始在线: {account['viewers']}人")
                else:
                    print(f"⏸️  {account['nickname']} 未开播")
        
        print()
        await asyncio.sleep(3)  # 等待3秒
    
    print("=" * 50)
    print("测试完成!")
    
    # 生成测试报告
    print("\n测试报告:")
    live_accounts = [a for a in test_accounts if a["is_live"]]
    print(f"- 总监控账号: {len(test_accounts)}")
    print(f"- 正在直播: {len(live_accounts)}")
    print(f"- 未开播: {len(test_accounts) - len(live_accounts)}")
    
    if live_accounts:
        max_viewers = max(a["viewers"] for a in live_accounts)
        avg_viewers = sum(a["viewers"] for a in live_accounts) // len(live_accounts)
        print(f"- 最高在线: {max_viewers}人")
        print(f"- 平均在线: {avg_viewers}人")

async def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    
    try:
        # 尝试导入数据库模块
        import asyncpg
        
        print("✅ asyncpg 模块可用")
        
        # 尝试连接（使用默认配置）
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='douyin',
                password='douyin123',
                database='douyin_monitor'
            )
            await conn.close()
            print("✅ 数据库连接成功")
        except Exception as e:
            print(f"⚠️  数据库连接失败: {e}")
            print("提示: 请先运行 docker-compose up -d 启动数据库服务")
            
    except ImportError:
        print("⚠️  asyncpg 模块未安装")
        print("提示: 运行 pip install asyncpg")

async def test_api_server():
    """测试API服务器"""
    print("\n测试API服务器...")
    
    try:
        import aiohttp
        
        # 测试本地API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8000/api/health', timeout=2) as response:
                    if response.status == 200:
                        print("✅ API服务器运行正常")
                    else:
                        print(f"⚠️  API服务器返回状态码: {response.status}")
        except Exception as e:
            print(f"⚠️  API服务器连接失败: {e}")
            print("提示: 请先启动API服务器 (python main.py)")
            
    except ImportError:
        print("⚠️  aiohttp 模块未安装")

def main():
    """主函数"""
    print("抖音监控系统 - 功能验证测试")
    print("=" * 50)
    
    # 运行测试
    loop = asyncio.get_event_loop()
    
    # 测试监控模拟
    loop.run_until_complete(test_monitor_simulation())
    
    # 测试数据库连接
    loop.run_until_complete(test_database_connection())
    
    # 测试API服务器
    loop.run_until_complete(test_api_server())
    
    print("\n" + "=" * 50)
    print("下一步:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 启动数据库: docker-compose up -d")
    print("3. 启动监控: python main.py")
    print("4. 访问API: http://localhost:8000")
    print("5. 访问Grafana: http://localhost:3000 (admin/admin123)")

if __name__ == "__main__":
    main()