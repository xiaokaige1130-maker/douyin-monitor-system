#!/usr/bin/env python3
"""
抖音Cookie自动获取工具
需要用户配合完成登录
"""

import os
import sys
import json
import time
from datetime import datetime
import subprocess

def print_step(step_num, title, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {title}")
    print(f"{'='*60}")
    print(description)
    print()

def setup_browser_environment():
    """设置浏览器环境"""
    print_step(1, "环境准备", "安装必要的浏览器自动化工具")
    
    print("检查系统环境...")
    
    # 检查Python模块
    required_modules = ['selenium', 'webdriver_manager']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n安装缺失模块: pip install {' '.join(missing_modules)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_modules, check=True)
            print("✅ 模块安装完成")
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False
    
    return True

def launch_douyin_login():
    """启动抖音登录流程"""
    print_step(2, "启动抖音登录", "自动打开抖音登录页面")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        print("启动Chrome浏览器...")
        
        # 配置Chrome选项
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 添加用户数据目录，避免每次登录
        user_data_dir = os.path.expanduser('~/.config/chrome-douyin')
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        print(f"用户数据目录: {user_data_dir}")
        
        # 启动浏览器
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ 浏览器启动成功")
        
        # 访问抖音登录页面
        print("打开抖音登录页面...")
        driver.get('https://www.douyin.com')
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ 抖音页面加载完成")
        print("\n📱 请手动完成以下操作:")
        print("  1. 找到页面上的二维码")
        print("  2. 打开手机抖音App")
        print("  3. 使用'扫一扫'功能扫描二维码")
        print("  4. 在手机上确认登录")
        print("\n登录成功后，脚本将自动获取Cookie")
        print("-" * 60)
        
        # 等待用户登录
        input("按Enter键继续（登录完成后）...")
        
        # 获取登录后的Cookie
        print("\n获取登录Cookie...")
        cookies = driver.get_cookies()
        
        # 格式化Cookie
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        
        print(f"✅ 获取到Cookie，长度: {len(cookie_str)} 字符")
        print(f"📋 包含 {len(cookies)} 个Cookie项")
        
        # 显示主要的Cookie项
        print("\n主要Cookie项:")
        douyin_cookies = ['passport_csrf_token', 'sid_tt', 'sessionid', 'odin_tt', 'ttwid']
        for cookie in cookies:
            if cookie['name'] in douyin_cookies:
                print(f"  🔹 {cookie['name']}: {cookie['value'][:30]}...")
        
        # 保存Cookie
        save_cookie(cookie_str, cookies)
        
        # 关闭浏览器
        driver.quit()
        print("✅ 浏览器已关闭")
        
        return cookie_str
        
    except Exception as e:
        print(f"❌ 登录流程出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_cookie(cookie_str, cookies_list):
    """保存Cookie到文件"""
    print_step(3, "保存Cookie", "将获取的Cookie保存到配置文件")
    
    # 保存原始Cookie
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cookie_file = f'douyin_cookie_{timestamp}.json'
    
    with open(cookie_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'cookie_string': cookie_str,
            'cookies': cookies_list
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cookie已保存到: {cookie_file}")
    
    # 更新.env配置文件
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
        
        # 更新或添加DOUYIN_COOKIE配置
        if 'DOUYIN_COOKIE=' in content:
            # 替换现有的
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                if line.strip().startswith('DOUYIN_COOKIE='):
                    updated_lines.append(f'DOUYIN_COOKIE={cookie_str}')
                else:
                    updated_lines.append(line)
            content = '\n'.join(updated_lines)
        else:
            # 添加到文件末尾
            content += f'\n# 抖音API配置\nDOUYIN_COOKIE={cookie_str}\n'
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ 配置文件已更新: {env_file}")
    else:
        print(f"⚠️  .env文件不存在，创建新文件")
        with open(env_file, 'w') as f:
            f.write(f'# 抖音监控系统配置\nDOUYIN_COOKIE={cookie_str}\n')
        print(f"✅ 创建配置文件: {env_file}")
    
    return cookie_file

def test_cookie(cookie_str):
    """测试Cookie有效性"""
    print_step(4, "测试Cookie", "验证Cookie是否有效")
    
    try:
        import requests
        
        print("测试抖音API访问...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': cookie_str,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # 尝试访问抖音API
        response = requests.get(
            'https://www.douyin.com/aweme/v1/web/user/profile/other/',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Cookie测试通过 (状态码: {response.status_code})")
            
            try:
                data = response.json()
                if data.get('status_code') == 0:
                    print("🎉 Cookie完全有效，可以访问抖音API")
                    return True
                else:
                    print(f"⚠️  API返回错误: {data.get('status_msg', '未知错误')}")
                    return False
            except:
                print("✅ 可以访问抖音，但API响应格式异常")
                return True
        else:
            print(f"❌ 请求失败 (状态码: {response.status_code})")
            return False
            
    except ImportError:
        print("⚠️  requests模块未安装，跳过API测试")
        return None
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

def show_next_steps(cookie_str, test_result):
    """显示下一步操作"""
    print_step(5, "完成配置", "启动完整监控系统")
    
    print("🎉 Cookie获取完成！")
    print(f"📏 Cookie长度: {len(cookie_str)} 字符")
    print(f"⏰ 获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if test_result is True:
        print("✅ Cookie验证通过，可以开始监控")
    elif test_result is False:
        print("⚠️  Cookie验证未通过，可能需要重新获取")
    else:
        print("🔍 Cookie有效性待验证")
    
    print("\n" + "="*60)
    print("🚀 启动完整监控系统")
    print("="*60)
    
    print("\n1. 停止当前演示系统:")
    print("   按 Ctrl+C 停止正在运行的监控系统")
    
    print("\n2. 启动完整监控系统:")
    print("   cd /home/huyankai/.openclaw/workspace/douyin_monitor")
    print("   ./start.sh")
    print("   或")
    print("   python main.py")
    
    print("\n3. 验证系统运行:")
    print("   curl http://localhost:8000/api/health")
    print("   curl http://localhost:8000/api/system/status")
    
    print("\n4. 添加监控账号:")
    print('   curl -X POST "http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名"')
    
    print("\n5. 开始监控:")
    print("   系统将自动开始24小时监控")
    print("   检测到直播时会:")
    print("   - 记录开播时间和时长")
    print("   - 采集在线人数等数据")
    print("   - 发送实时通知")
    print("   - 生成统计报告")
    
    print("\n" + "="*60)
    print("💡 提示: Cookie通常有效期为几天到几周")
    print("       失效时需要重新运行此脚本获取")
    print("="*60)

def main():
    """主函数"""
    print("🎬 抖音Cookie自动获取工具")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print("="*60)
    
    try:
        # 1. 环境准备
        if not setup_browser_environment():
            print("❌ 环境准备失败")
            return
        
        # 2. 启动登录流程
        cookie = launch_douyin_login()
        if not cookie:
            print("❌ Cookie获取失败")
            return
        
        # 3. 测试Cookie
        test_result = test_cookie(cookie)
        
        # 4. 显示下一步
        show_next_steps(cookie, test_result)
        
        # 5. 创建快速启动脚本
        create_quick_start_script()
        
    except KeyboardInterrupt:
        print("\n\n📢 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()

def create_quick_start_script():
    """创建快速启动脚本"""
    script_content = """#!/bin/bash
# 抖音监控系统快速启动脚本

echo "抖音监控系统快速启动"
echo "======================"

# 停止可能运行的旧进程
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# 启动数据库服务
echo "启动数据库服务..."
docker-compose up -d postgres redis influxdb

# 等待服务启动
sleep 5

# 启动监控系统
echo "启动监控系统..."
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
python main.py
"""

    script_file = "quick_start.sh"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_file, 0o755)
    print(f"\n📁 快速启动脚本已创建: {script_file}")
    print(f"   使用: ./{script_file}")

if __name__ == "__main__":
    main()