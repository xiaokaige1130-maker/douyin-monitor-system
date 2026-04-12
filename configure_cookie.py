#!/usr/bin/env python3
"""
抖音Cookie配置助手
"""

import os
import sys
import json
from datetime import datetime

def check_current_config():
    """检查当前配置"""
    print("🔍 检查当前配置...")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print("  ❌ .env 文件不存在")
        return None
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # 检查是否有抖音Cookie配置
    if "DOUYIN_COOKIE=" in content:
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith("DOUYIN_COOKIE="):
                if line.strip().startswith("DOUYIN_COOKIE=your_cookie_here") or "# DOUYIN_COOKIE=" in line:
                    print("  ⚠️  抖音Cookie已配置但被注释或使用默认值")
                    return "commented"
                else:
                    cookie_value = line.split('=', 1)[1].strip()
                    if cookie_value:
                        print(f"  ✅ 抖音Cookie已配置 (长度: {len(cookie_value)})")
                        return cookie_value
                    else:
                        print("  ⚠️  抖音Cookie配置为空")
                        return "empty"
    
    print("  ❌ 未找到抖音Cookie配置")
    return None

def configure_cookie_interactive():
    """交互式配置Cookie"""
    print("\n🎯 抖音Cookie配置")
    print("=" * 50)
    
    # 显示当前配置状态
    current = check_current_config()
    
    if current and current not in ["commented", "empty"]:
        print(f"\n📋 当前Cookie: {current[:50]}...")
        choice = input("\n是否要更新Cookie? (y/N): ").strip().lower()
        if choice != 'y':
            print("✅ 保持现有配置")
            return current
    
    print("\n📝 请粘贴你的抖音Cookie:")
    print("  1. 登录抖音网页版后，按F12打开开发者工具")
    print("  2. 切换到Network标签")
    print("  3. 刷新页面或点击任意链接")
    print("  4. 找到任意请求，查看Request Headers")
    print("  5. 复制Cookie字段的值")
    print("-" * 50)
    
    cookie = input("粘贴Cookie值 (直接按Enter跳过): ").strip()
    
    if not cookie:
        print("⏭️  跳过Cookie配置")
        return None
    
    # 验证Cookie格式
    if len(cookie) < 50:
        print(f"⚠️  Cookie长度较短 ({len(cookie)}字符)，可能不完整")
        confirm = input("是否继续? (y/N): ").strip().lower()
        if confirm != 'y':
            return None
    
    # 显示Cookie信息
    print(f"\n📊 Cookie信息:")
    print(f"  长度: {len(cookie)} 字符")
    print(f"  预览: {cookie[:80]}...")
    
    # 检查常见抖音Cookie字段
    douyin_keywords = ['passport_csrf_token', 'sid_tt', 'sessionid', 'odin_tt']
    found_keywords = [kw for kw in douyin_keywords if kw in cookie]
    
    if found_keywords:
        print(f"  ✅ 包含抖音标识: {', '.join(found_keywords)}")
    else:
        print("  ⚠️  未检测到明显的抖音Cookie标识")
        confirm = input("是否确定这是抖音Cookie? (y/N): ").strip().lower()
        if confirm != 'y':
            return None
    
    return cookie

def update_env_file(cookie):
    """更新.env文件"""
    print("\n🔧 更新配置文件...")
    
    env_file = ".env"
    
    # 读取现有内容
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        print("  ❌ .env 文件不存在，创建新文件")
        lines = []
    
    # 查找或添加DOUYIN_COOKIE配置
    cookie_line = f'DOUYIN_COOKIE={cookie}\n'
    cookie_found = False
    updated_lines = []
    
    for line in lines:
        if line.strip().startswith("DOUYIN_COOKIE=") or line.strip().startswith("# DOUYIN_COOKIE="):
            # 替换现有的Cookie配置
            updated_lines.append(cookie_line)
            cookie_found = True
        else:
            updated_lines.append(line)
    
    if not cookie_found:
        # 在文件末尾添加Cookie配置
        # 先找到合适的位置（在抖音API配置部分）
        inserted = False
        final_lines = []
        
        for line in updated_lines:
            final_lines.append(line)
            # 在抖音API配置注释后插入
            if "# 抖音API配置（可选）" in line and not inserted:
                final_lines.append("\n")
                final_lines.append(cookie_line)
                inserted = True
        
        if not inserted:
            # 如果没找到合适位置，添加到文件末尾
            final_lines.append("\n# 抖音API配置（可选）\n")
            final_lines.append(cookie_line)
        
        updated_lines = final_lines
    
    # 写入文件
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"  ✅ 配置文件已更新")
    print(f"  📁 文件: {os.path.abspath(env_file)}")
    
    return True

def test_cookie(cookie):
    """测试Cookie是否有效"""
    print("\n🧪 测试Cookie有效性...")
    
    try:
        import requests
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': cookie,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 尝试访问抖音主页
        print("  正在测试抖音API访问...")
        response = requests.get(
            'https://www.douyin.com',
            headers=headers,
            timeout=10,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            # 检查响应内容是否包含抖音标识
            content = response.text.lower()
            if 'douyin' in content or '抖音' in content or 'aweme' in content:
                print(f"  ✅ Cookie测试通过 (状态码: {response.status_code})")
                print(f"  📏 响应长度: {len(response.text)} 字符")
                return True
            else:
                print(f"  ⚠️  响应不包含抖音标识 (状态码: {response.status_code})")
                return False
        else:
            print(f"  ❌ 请求失败 (状态码: {response.status_code})")
            return False
            
    except ImportError:
        print("  ⚠️  requests模块未安装，跳过API测试")
        print("  安装: pip install requests")
        return None
    except Exception as e:
        print(f"  ❌ 测试过程中出错: {e}")
        return False

def show_next_steps(cookie, test_result):
    """显示下一步操作"""
    print("\n" + "=" * 50)
    print("🚀 配置完成！下一步操作")
    print("=" * 50)
    
    if cookie:
        print(f"📋 已配置Cookie:")
        print(f"   长度: {len(cookie)} 字符")
        print(f"   预览: {cookie[:60]}...")
        print()
    
    print("🔧 重启监控系统:")
    print("  1. 停止当前系统 (按Ctrl+C)")
    print("  2. 启动完整系统:")
    print()
    print("     cd /home/huyankai/.openclaw/workspace/douyin_monitor")
    print("     ./start.sh")
    print("     或")
    print("     python main.py")
    print()
    
    print("🌐 验证系统运行:")
    print("  curl http://localhost:8000/api/health")
    print("  curl http://localhost:8000/api/system/status")
    print()
    
    print("📊 添加监控账号:")
    print('  curl -X POST "http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名"')
    print()
    
    print("💡 系统功能:")
    print("  - 24小时自动监控")
    print("  - 实时数据采集")
    print("  - 开播即时通知")
    print("  - 完整数据可视化")
    print()
    
    if test_result is False:
        print("⚠️  注意: Cookie测试未通过，可能需要重新获取有效的Cookie")
        print("     请确保:")
        print("     1. Cookie是从登录后的抖音页面获取")
        print("     2. Cookie包含完整的登录凭证")
        print("     3. 账号未被限制访问")
    
    print("=" * 50)

def main():
    """主函数"""
    print("🎬 抖音监控系统 - Cookie配置助手")
    print("=" * 50)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目录: {os.getcwd()}")
    print()
    
    # 交互式获取Cookie
    cookie = configure_cookie_interactive()
    
    if not cookie:
        print("\n⏭️  未配置Cookie，系统将继续以演示模式运行")
        print("💡 提示: 随时可以重新运行此脚本配置Cookie")
        return
    
    # 更新配置文件
    if update_env_file(cookie):
        print(f"\n✅ Cookie已保存到配置文件")
        
        # 测试Cookie
        test_result = test_cookie(cookie)
        
        # 显示下一步
        show_next_steps(cookie, test_result)
        
        # 保存Cookie备份（可选）
        backup_file = f"cookie_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            f.write(f"# 抖音Cookie备份 - {datetime.now()}\n")
            f.write(f"DOUYIN_COOKIE={cookie}\n")
        print(f"📁 Cookie备份已保存到: {backup_file}")
        
    else:
        print("\n❌ 配置失败，请检查文件权限")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n📢 配置被用户中断")
    except Exception as e:
        print(f"\n❌ 配置过程中出错: {e}")
        import traceback
        traceback.print_exc()