print("抖音监控系统 - 快速测试")
print("=" * 50)

# 检查Python环境
import sys
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")

# 检查必要模块
required_modules = ['asyncio', 'aiohttp', 'asyncpg', 'sqlalchemy', 'schedule']
print("\n检查依赖模块:")
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"❌ {module} (未安装)")

print("\n" + "=" * 50)
print("系统架构验证完成!")
print("\n部署步骤:")
print("1. 安装依赖: pip install -r requirements.txt")
print("2. 启动数据库: docker-compose up -d")
print("3. 复制配置文件: cp .env.example .env")
print("4. 编辑配置文件: vim .env")
print("5. 启动系统: ./start.sh")
print("\n访问地址:")
print("- API文档: http://localhost:8000/docs")
print("- Grafana: http://localhost:3000 (admin/admin123)")
print("- 监控面板: http://localhost:8000")