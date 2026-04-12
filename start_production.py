#!/usr/bin/env python3
"""
抖音监控系统 - 生产环境启动脚本
"""

import asyncio
import sys
import os
import signal
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ProductionSystem:
    """生产环境系统"""
    
    def __init__(self):
        self.is_running = False
        self.start_time = None
        
    async def initialize(self):
        """初始化系统"""
        print("=" * 60)
        print("抖音监控系统 - 生产环境启动")
        print("=" * 60)
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查服务状态
        await self.check_services()
        
        # 检查配置
        await self.check_config()
        
        # 初始化应用
        await self.initialize_app()
        
    async def check_services(self):
        """检查服务状态"""
        print("🔍 检查系统服务...")
        
        import subprocess
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        
        services = {
            'postgres': False,
            'redis': False,
            'influxdb': False
        }
        
        for line in result.stdout.split('\n'):
            if 'postgres' in line and 'Up' in line:
                services['postgres'] = True
            if 'redis' in line and 'Up' in line:
                services['redis'] = True
            if 'influxdb' in line and 'Up' in line:
                services['influxdb'] = True
        
        for service, running in services.items():
            if running:
                print(f"  ✅ {service:10} 运行正常")
            else:
                print(f"  ❌ {service:10} 未运行")
        
        print()
        
    async def check_config(self):
        """检查配置"""
        print("🔧 检查系统配置...")
        
        from core.config import Config
        config = Config()
        
        # 检查抖音Cookie
        if not config.douyin_cookie:
            print("  ⚠️  抖音Cookie未配置 - 系统将以演示模式运行")
            print("  💡 请设置 DOUYIN_COOKIE 环境变量以启用完整功能")
        else:
            print("  ✅ 抖音Cookie已配置")
        
        # 显示配置
        print(f"  📊 监控配置:")
        print(f"     - 正常检查间隔: {config.check_interval_normal}分钟")
        print(f"     - 直播检查间隔: {config.check_interval_live}分钟")
        print(f"     - 最大并发检查: {config.max_concurrent_checks}")
        
        print(f"  🌐 API配置:")
        print(f"     - 主机: {config.api_host}")
        print(f"     - 端口: {config.api_port}")
        print(f"     - 启用: {config.api_enabled}")
        
        print()
        
    async def initialize_app(self):
        """初始化应用"""
        print("🚀 初始化监控应用...")
        
        try:
            from core.config import Config
            from core.database import Database
            from core.monitor import DouyinMonitor
            from core.scheduler import Scheduler
            
            # 创建配置
            self.config = Config()
            self.db = Database(self.config)
            self.monitor = DouyinMonitor(self.config, self.db)
            self.scheduler = Scheduler()
            
            # 连接数据库
            print("  🔗 连接数据库...")
            await self.db.connect()
            print("  ✅ 数据库连接成功")
            
            # 初始化监控器
            print("  🔧 初始化监控器...")
            await self.monitor.initialize()
            print("  ✅ 监控器初始化成功")
            
            # 设置信号处理
            self.setup_signal_handlers()
            
            print("  🎉 应用初始化完成")
            print()
            
            return True
            
        except Exception as e:
            print(f"  ❌ 应用初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_signal_handlers(self):
        """设置信号处理"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        print(f"\n📢 收到信号 {signum}，正在关闭系统...")
        self.is_running = False
    
    async def start_api_server(self):
        """启动API服务器"""
        if not self.config.api_enabled:
            print("  ⏭️  API服务器已禁用")
            return None
        
        print("  🌐 启动API服务器...")
        
        try:
            from api.server import start_api_server
            import threading
            
            # 在后台启动API服务器
            api_task = asyncio.create_task(start_api_server(self.config, self.db))
            
            print(f"  ✅ API服务器已启动: http://{self.config.api_host}:{self.config.api_port}")
            print(f"  📚 API文档: http://{self.config.api_host}:{self.config.api_port}/docs")
            
            return api_task
            
        except Exception as e:
            print(f"  ❌ 启动API服务器失败: {e}")
            return None
    
    async def start_monitoring(self):
        """开始监控"""
        print("👁️  开始监控任务...")
        
        # 添加定时任务
        await self.scheduler.add_job(
            self.monitor.check_all_accounts,
            minutes=1,  # 每分钟检查一次任务队列
            name="monitor_check"
        )
        
        # 添加数据清理任务
        await self.scheduler.add_job(
            self.cleanup_old_data,
            hour=3,
            minute=0,
            name="data_cleanup"
        )
        
        print("  ✅ 监控任务已调度")
        print()
        
        # 显示系统信息
        self.show_system_info()
        
    async def cleanup_old_data(self):
        """清理旧数据"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=self.config.data_retention_days)
            deleted = await self.db.cleanup_old_data(cutoff_date)
            print(f"🧹 清理了 {deleted} 条旧数据")
        except Exception as e:
            print(f"❌ 清理数据时出错: {e}")
    
    def show_system_info(self):
        """显示系统信息"""
        print("=" * 60)
        print("📊 系统运行信息")
        print("=" * 60)
        print(f"  启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  运行模式: {'演示模式' if not self.config.douyin_cookie else '完整模式'}")
        print(f"  API地址: http://{self.config.api_host}:{self.config.api_port}")
        print(f"  日志级别: {self.config.log_level}")
        print()
        print("💡 可用命令:")
        print("  - 查看API文档: 访问 http://localhost:8000/docs")
        print("  - 查看健康状态: curl http://localhost:8000/api/health")
        print("  - 添加监控账号: 通过API接口添加")
        print()
        print("⚠️  注意事项:")
        if not self.config.douyin_cookie:
            print("  - 系统运行在演示模式，需要配置DOUYIN_COOKIE启用完整功能")
        print("  - 按 Ctrl+C 停止系统")
        print("=" * 60)
        print()
    
    async def run(self):
        """运行主循环"""
        self.start_time = datetime.now()
        self.is_running = True
        
        # 启动API服务器
        api_task = await self.start_api_server()
        
        # 开始监控
        await self.start_monitoring()
        
        print("🔄 系统运行中...")
        
        # 主循环
        try:
            while self.is_running:
                # 执行调度任务
                await self.scheduler.run_pending()
                
                # 检查活跃直播
                await self.monitor.check_active_lives()
                
                # 短暂休眠
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            print("📢 任务被取消")
        except Exception as e:
            print(f"❌ 主循环出错: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """关闭系统"""
        print("\n🔧 正在关闭系统...")
        
        # 关闭监控器
        if hasattr(self, 'monitor'):
            await self.monitor.shutdown()
            print("  ✅ 监控器已关闭")
        
        # 关闭数据库连接
        if hasattr(self, 'db'):
            await self.db.disconnect()
            print("  ✅ 数据库连接已关闭")
        
        # 计算运行时间
        if self.start_time:
            run_time = datetime.now() - self.start_time
            hours = run_time.seconds // 3600
            minutes = (run_time.seconds % 3600) // 60
            seconds = run_time.seconds % 60
            print(f"  ⏱️  运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        print("👋 系统已关闭")
        print("=" * 60)

async def main():
    """主函数"""
    system = ProductionSystem()
    
    try:
        # 初始化系统
        await system.initialize()
        
        # 运行系统
        await system.run()
        
    except KeyboardInterrupt:
        print("\n📢 收到键盘中断信号")
    except Exception as e:
        print(f"\n❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if system.is_running:
            system.is_running = False

if __name__ == "__main__":
    # 使用虚拟环境
    asyncio.run(main())