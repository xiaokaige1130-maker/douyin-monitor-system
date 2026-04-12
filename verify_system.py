#!/usr/bin/env python3
"""
系统验证脚本
验证抖音监控系统的核心功能
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python():
    """检查Python环境"""
    print("🔍 检查Python环境...")
    
    # Python版本
    version = sys.version_info
    print(f"  Python版本: {sys.version}")
    
    if version.major == 3 and version.minor >= 8:
        print("  ✅ Python版本符合要求 (3.8+)")
    else:
        print("  ❌ Python版本过低，需要3.8+")
        return False
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("  ✅ 运行在虚拟环境中")
    else:
        print("  ⚠️  未使用虚拟环境（建议使用）")
    
    return True

def check_docker():
    """检查Docker环境"""
    print("\n🔍 检查Docker环境...")
    
    try:
        # 检查Docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Docker已安装: {result.stdout.strip()}")
            
            # 检查Docker服务状态
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ Docker服务运行正常")
            else:
                print("  ❌ Docker服务异常")
                return False
        else:
            print("  ❌ Docker未安装")
            return False
            
    except FileNotFoundError:
        print("  ❌ Docker未安装")
        return False
    
    # 检查docker-compose
    try:
        # 尝试不同版本的命令
        for cmd in ['docker-compose', 'docker-compose-v2', 'docker compose']:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {cmd}: {result.stdout.strip()}")
                    return True
            except FileNotFoundError:
                continue
        
        print("  ❌ docker-compose未安装")
        return False
        
    except Exception as e:
        print(f"  ❌ 检查docker-compose时出错: {e}")
        return False

def check_files():
    """检查必要文件"""
    print("\n🔍 检查项目文件...")
    
    required_files = [
        'requirements.txt',
        'docker-compose.yml',
        'Dockerfile',
        'main.py',
        'start.sh',
        '.env.example'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (缺失)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n  ⚠️  缺失文件: {', '.join(missing_files)}")
        return False
    
    # 检查目录结构
    required_dirs = ['core', 'api', 'logs', 'data', 'config']
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"  ✅ 目录: {dir_name}/")
        else:
            print(f"  ⚠️  目录: {dir_name}/ (不存在，将自动创建)")
    
    return True

def check_python_modules():
    """检查Python模块"""
    print("\n🔍 检查Python模块...")
    
    # 核心模块
    core_modules = [
        'aiohttp',
        'asyncpg', 
        'sqlalchemy',
        'fastapi',
        'loguru',
        'schedule'
    ]
    
    missing_modules = []
    for module in core_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n  ⚠️  缺失模块: {', '.join(missing_modules)}")
        print(f"  运行: pip install {' '.join(missing_modules)}")
        return False
    
    return True

def check_system_resources():
    """检查系统资源"""
    print("\n🔍 检查系统资源...")
    
    try:
        import psutil
        
        # 内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"  内存总量: {memory_gb:.1f} GB")
        
        if memory_gb >= 4:
            print("  ✅ 内存充足 (≥4GB)")
        else:
            print("  ⚠️  内存可能不足 (建议≥4GB)")
        
        # 磁盘空间
        disk = psutil.disk_usage('/')
        disk_gb = disk.free / (1024**3)
        print(f"  磁盘可用空间: {disk_gb:.1f} GB")
        
        if disk_gb >= 10:
            print("  ✅ 磁盘空间充足")
        else:
            print("  ⚠️  磁盘空间可能不足")
        
        return True
        
    except ImportError:
        print("  ⚠️  无法检查系统资源 (psutil未安装)")
        return True

def create_test_config():
    """创建测试配置文件"""
    print("\n🔧 创建测试配置...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("  ✅ 已创建 .env 文件 (从 .env.example)")
            
            # 修改为测试配置
            with open('.env', 'r') as f:
                content = f.read()
            
            # 设置测试模式
            content = content.replace('LOG_LEVEL=INFO', 'LOG_LEVEL=DEBUG')
            content = content.replace('API_ENABLED=true', 'API_ENABLED=true')
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("  ✅ 已配置测试参数")
        else:
            print("  ❌ 找不到 .env.example 文件")
            return False
    else:
        print("  ✅ .env 文件已存在")
    
    return True

def run_simple_test():
    """运行简单测试"""
    print("\n🧪 运行简单测试...")
    
    try:
        # 测试导入核心模块
        print("  测试导入核心模块...")
        sys.path.insert(0, '.')
        
        # 测试配置模块
        try:
            from core.config import Config
            config = Config()
            print("  ✅ 配置模块正常")
        except Exception as e:
            print(f"  ❌ 配置模块错误: {e}")
            return False
        
        # 测试数据库模型
        try:
            from core.models import Base, MonitoredAccount
            print("  ✅ 数据模型正常")
        except Exception as e:
            print(f"  ❌ 数据模型错误: {e}")
            return False
        
        print("  ✅ 核心模块测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("抖音监控系统 - 环境验证")
    print("=" * 60)
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录: {script_dir}")
    
    # 运行检查
    checks = [
        ("Python环境", check_python),
        ("Docker环境", check_docker),
        ("项目文件", check_files),
        ("Python模块", check_python_modules),
        ("系统资源", check_system_resources),
        ("配置文件", create_test_config),
        ("核心功能", run_simple_test),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  检查出错: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有检查通过！系统可以正常运行。")
        print("\n下一步:")
        print("1. 编辑 .env 文件配置抖音Cookie")
        print("2. 启动服务: ./start.sh")
        print("3. 访问: http://localhost:8000")
    else:
        print(f"\n⚠️  有 {total-passed} 项检查未通过，请先解决问题。")
        
        if not any(r for n, r in results if n == "Docker环境"):
            print("\n💡 Docker问题解决:")
            print("  sudo apt-get install docker.io docker-compose")
            print("  sudo systemctl start docker")
            print("  sudo usermod -aG docker $USER")
            print("  然后重新登录")
        
        if not any(r for n, r in results if n == "Python模块"):
            print("\n💡 Python依赖问题解决:")
            print("  python3 -m venv venv")
            print("  source venv/bin/activate")
            print("  pip install -r requirements.txt")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()