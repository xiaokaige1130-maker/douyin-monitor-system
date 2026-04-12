#!/usr/bin/env python3
"""
测试数据库连接
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_postgres():
    """测试PostgreSQL连接"""
    print("🔍 测试PostgreSQL连接...")
    
    try:
        import asyncpg
        
        # 连接参数
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'user': 'douyin',
            'password': 'douyin123',
            'database': 'douyin_monitor',
            'timeout': 10
        }
        
        # 尝试连接
        conn = await asyncpg.connect(**conn_params)
        
        # 测试查询
        result = await conn.fetchval('SELECT 1')
        print(f"  ✅ PostgreSQL连接成功，测试查询结果: {result}")
        
        # 检查表是否存在
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        if tables:
            print(f"  📊 数据库中有 {len(tables)} 张表")
            for table in tables[:5]:  # 显示前5张表
                print(f"     - {table['table_name']}")
        else:
            print("  ℹ️  数据库中没有表（正常，首次运行）")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ PostgreSQL连接失败: {e}")
        return False

async def test_redis():
    """测试Redis连接"""
    print("\n🔍 测试Redis连接...")
    
    try:
        from redis import asyncio as aioredis
        
        # 连接Redis
        redis = aioredis.from_url('redis://localhost:6379/0', decode_responses=True)
        
        # 测试PING
        result = await redis.ping()
        print(f"  ✅ Redis连接成功，PING响应: {result}")
        
        # 测试基本操作
        await redis.set('test_key', 'test_value')
        value = await redis.get('test_key')
        print(f"  🔑 键值测试: test_key = {value}")
        
        await redis.delete('test_key')
        await redis.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Redis连接失败: {e}")
        return False

async def test_influxdb():
    """测试InfluxDB连接"""
    print("\n🔍 测试InfluxDB连接...")
    
    try:
        from influxdb_client import InfluxDBClient
        
        # 连接InfluxDB
        client = InfluxDBClient(
            url="http://localhost:8086",
            token="douyin-token-123",
            org="douyin"
        )
        
        # 测试健康检查
        health = client.health()
        print(f"  ✅ InfluxDB连接成功，状态: {health.status}")
        print(f"  📊 版本: {health.version}")
        
        # 检查bucket
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets()
        
        if buckets and len(buckets.buckets) > 0:
            print(f"  📁 找到 {len(buckets.buckets)} 个bucket")
            for bucket in buckets.buckets[:3]:
                print(f"     - {bucket.name}")
        else:
            print("  ℹ️  没有找到bucket（正常，首次运行）")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"  ❌ InfluxDB连接失败: {e}")
        return False

async def test_database_models():
    """测试数据库模型"""
    print("\n🔍 测试数据库模型...")
    
    try:
        from core.database import Database
        from core.config import Config
        
        # 创建配置和数据库对象
        config = Config()
        db = Database(config)
        
        # 连接数据库
        await db.connect()
        print("  ✅ 数据库连接成功")
        
        # 测试获取监控账号（应该为空）
        accounts = await db.get_monitored_accounts()
        print(f"  👥 监控账号数量: {len(accounts)}")
        
        # 测试Redis缓存
        await db.set_cache('test_cache', {'message': 'Hello World'}, expire=10)
        cached = await db.get_cache('test_cache')
        print(f"  💾 Redis缓存测试: {cached}")
        
        # 断开连接
        await db.disconnect()
        print("  🔌 数据库连接已关闭")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 数据库模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_monitor_app():
    """测试监控应用"""
    print("\n🔍 测试监控应用...")
    
    try:
        from core.monitor import DouyinMonitor
        from core.config import Config
        from core.database import Database
        
        # 创建配置
        config = Config()
        
        # 修改配置为测试模式
        config.check_interval_normal = 1  # 1分钟
        config.check_interval_live = 1    # 1分钟
        config.max_concurrent_checks = 2  # 2个并发
        
        print(f"  ⚙️  配置加载成功:")
        print(f"     - 正常检查间隔: {config.check_interval_normal}分钟")
        print(f"     - 直播检查间隔: {config.check_interval_live}分钟")
        print(f"     - 最大并发检查: {config.max_concurrent_checks}")
        
        # 创建数据库和监控器
        db = Database(config)
        monitor = DouyinMonitor(config, db)
        
        # 初始化监控器
        await monitor.initialize()
        print("  ✅ 监控器初始化成功")
        
        # 测试关闭
        await monitor.shutdown()
        print("  🔌 监控器已关闭")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 监控应用测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("抖音监控系统 - 数据库连接测试")
    print("=" * 60)
    print()
    
    # 运行测试
    tests = [
        ("PostgreSQL", test_postgres),
        ("Redis", test_redis),
        ("InfluxDB", test_influxdb),
        ("数据库模型", test_database_models),
        ("监控应用", test_monitor_app),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"[{name}]")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ 测试出错: {e}")
            results.append((name, False))
        print()
    
    # 总结
    print("=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:15} {status}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有数据库测试通过！系统可以正常运行。")
    else:
        print(f"\n⚠️  有 {total-passed} 项测试未通过。")
    
    print("\n" + "=" * 60)
    print("💡 系统状态:")
    print(f"  - PostgreSQL: {'✅ 运行中' if passed > 0 else '❌ 未连接'}")
    print(f"  - Redis: {'✅ 运行中' if passed > 1 else '❌ 未连接'}")
    print(f"  - InfluxDB: {'✅ 运行中' if passed > 2 else '❌ 未连接'}")
    print(f"  - 应用连接: {'✅ 正常' if passed > 3 else '❌ 异常'}")
    print("\n🚀 下一步: 启动完整系统测试")
    print("=" * 60)

if __name__ == "__main__":
    # 使用虚拟环境中的Python
    asyncio.run(main())