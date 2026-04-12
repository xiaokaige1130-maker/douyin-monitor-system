#!/usr/bin/env python3
"""
简化版抖音Cookie获取工具
提供详细的手动获取指南
"""

import os
import sys
import json
from datetime import datetime

def print_header():
    """打印标题"""
    print("🎬 抖音Cookie获取指南")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目录: {os.getcwd()}")
    print("=" * 60)

def show_manual_steps():
    """显示手动获取步骤"""
    print("\n📱 手动获取抖音Cookie步骤:")
    print("=" * 60)
    
    steps = [
        {
            "num": 1,
            "title": "打开抖音网页版",
            "desc": "访问 https://www.douyin.com",
            "command": "xdg-open https://www.douyin.com  # 或直接在浏览器中打开"
        },
        {
            "num": 2,
            "title": "找到登录二维码",
            "desc": "在页面中找到登录二维码区域",
            "command": "等待页面加载完成，找到二维码"
        },
        {
            "num": 3,
            "title": "手机扫码登录",
            "desc": "打开手机抖音App，使用'扫一扫'功能",
            "command": "1. 打开抖音App\n2. 点击右上角搜索旁的'+'号\n3. 选择'扫一扫'\n4. 扫描网页上的二维码"
        },
        {
            "num": 4,
            "title": "确认登录",
            "desc": "在手机上确认登录",
            "command": "在手机抖音App上点击'确认登录'"
        },
        {
            "num": 5,
            "title": "打开开发者工具",
            "desc": "按F12打开浏览器开发者工具",
            "command": "在抖音网页版页面按 F12 键"
        },
        {
            "num": 6,
            "title": "切换到Network标签",
            "desc": "在开发者工具中切换到Network标签",
            "command": "点击'Network'或'网络'标签"
        },
        {
            "num": 7,
            "title": "刷新页面",
            "desc": "按F5刷新页面以捕获请求",
            "command": "按 F5 键刷新页面"
        },
        {
            "num": 8,
            "title": "找到请求并复制Cookie",
            "desc": "找到任意请求，复制Request Headers中的Cookie",
            "command": "1. 在Network标签中找到任意请求（如aweme/v1/...）\n2. 点击该请求\n3. 查看Headers标签\n4. 找到'Request Headers'部分\n5. 复制'Cookie'字段的值"
        }
    ]
    
    for step in steps:
        print(f"\n步骤 {step['num']}: {step['title']}")
        print(f"  描述: {step['desc']}")
        print(f"  操作: {step['command']}")
        print(f"  {'─'*50}")

def collect_cookie_interactive():
    """交互式收集Cookie"""
    print("\n" + "=" * 60)
    print("📝 请输入获取的抖音Cookie")
    print("=" * 60)
    
    print("\n请粘贴你的抖音Cookie（从浏览器开发者工具中复制）:")
    print("Cookie示例格式:")
    print("  passport_csrf_token=xxx; sid_tt=xxx; sessionid=xxx; odin_tt=xxx; ...")
    print("-" * 60)
    
    # 在非交互式环境中，我们无法使用input
    # 这里提供文件输入方式
    print("\n由于当前环境限制，请使用以下方式之一:")
    print("1. 编辑配置文件直接设置:")
    print("   vim .env")
    print("   找到 # DOUYIN_COOKIE=your_cookie_here")
    print("   取消注释并粘贴你的Cookie")
    print()
    print("2. 使用命令设置:")
    print("   echo 'DOUYIN_COOKIE=你的Cookie值' >> .env")
    print()
    print("3. 创建Cookie文件:")
    print("   echo '你的Cookie值' > douyin_cookie.txt")
    print("   然后运行: python3 -c \"cookie=open('douyin_cookie.txt').read().strip(); print(f'DOUYIN_COOKIE={cookie}')\" >> .env")
    
    return None

def update_env_file(cookie):
    """更新.env文件"""
    if not cookie:
        return False
    
    env_file = ".env"
    
    # 读取现有内容
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
    else:
        content = ""
    
    # 更新或添加DOUYIN_COOKIE配置
    lines = content.split('\n')
    updated_lines = []
    cookie_found = False
    
    for line in lines:
        if line.strip().startswith("DOUYIN_COOKIE=") or line.strip().startswith("# DOUYIN_COOKIE="):
            updated_lines.append(f"DOUYIN_COOKIE={cookie}")
            cookie_found = True
        else:
            updated_lines.append(line)
    
    if not cookie_found:
        # 在合适的位置添加
        inserted = False
        final_lines = []
        
        for line in updated_lines:
            final_lines.append(line)
            if "# 抖音API配置（可选）" in line and not inserted:
                final_lines.append(f"DOUYIN_COOKIE={cookie}")
                inserted = True
        
        if not inserted:
            final_lines.append(f"\n# 抖音API配置\nDOUYIN_COOKIE={cookie}")
        
        updated_lines = final_lines
    
    # 写入文件
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"\n✅ 配置文件已更新: {env_file}")
    return True

def create_cookie_file(cookie):
    """创建Cookie备份文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cookie_file = f"douyin_cookie_{timestamp}.txt"
    
    with open(cookie_file, 'w') as f:
        f.write(f"# 抖音Cookie备份 - {datetime.now()}\n")
        f.write(f"# 长度: {len(cookie)} 字符\n")
        f.write(f"{cookie}\n")
    
    print(f"📁 Cookie备份已保存: {cookie_file}")
    return cookie_file

def show_config_commands():
    """显示配置命令"""
    print("\n" + "=" * 60)
    print("🔧 快速配置命令")
    print("=" * 60)
    
    commands = [
        {
            "desc": "查看当前配置",
            "cmd": "grep -i cookie .env"
        },
        {
            "desc": "直接设置Cookie（替换YOUR_COOKIE）",
            "cmd": "sed -i 's/# DOUYIN_COOKIE=.*/DOUYIN_COOKIE=YOUR_COOKIE/' .env"
        },
        {
            "desc": "追加Cookie配置",
            "cmd": "echo 'DOUYIN_COOKIE=YOUR_COOKIE' >> .env"
        },
        {
            "desc": "创建新配置文件",
            "cmd": "cat > .env << 'EOF'\n# 抖音监控系统配置\nDOUYIN_COOKIE=YOUR_COOKIE\nEOF"
        }
    ]
    
    for cmd_info in commands:
        print(f"\n{cmd_info['desc']}:")
        print(f"  {cmd_info['cmd']}")

def show_next_steps():
    """显示下一步操作"""
    print("\n" + "=" * 60)
    print("🚀 完成配置后的操作")
    print("=" * 60)
    
    steps = [
        "1. 确保Cookie已正确配置到 .env 文件",
        "2. 停止当前演示系统（如果正在运行）",
        "3. 启动完整监控系统:",
        "   cd /home/huyankai/.openclaw/workspace/douyin_monitor",
        "   ./start.sh",
        "4. 验证系统运行:",
        "   curl http://localhost:8000/api/health",
        "5. 添加监控账号:",
        "   curl -X POST \"http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名\"",
        "6. 开始24小时自动监控"
    ]
    
    for step in steps:
        print(step)
    
    print("\n💡 系统功能预览:")
    print("  - 实时开播检测")
    print("  - 在线人数监控")
    print("  - 时长统计")
    print("  - 数据可视化")
    print("  - 实时通知")

def main():
    """主函数"""
    print_header()
    show_manual_steps()
    show_config_commands()
    show_next_steps()
    
    # 提供直接配置选项
    print("\n" + "=" * 60)
    print("🎯 立即配置")
    print("=" * 60)
    
    print("\n如果你已经有抖音Cookie，可以直接运行:")
    print("\n配置命令（替换YOUR_ACTUAL_COOKIE）:")
    print("cd /home/huyankai/.openclaw/workspace/douyin_monitor")
    print("cat > .env << 'EOF'")
    print("# 抖音监控系统配置")
    print("DATABASE_URL=postgresql://douyin:douyin123@localhost:5432/douyin_monitor")
    print("REDIS_URL=redis://localhost:6379/0")
    print("INFLUXDB_URL=http://localhost:8086")
    print("INFLUXDB_TOKEN=douyin-token-123")
    print("INFLUXDB_ORG=douyin")
    print("INFLUXDB_BUCKET=douyin_data")
    print("CHECK_INTERVAL_NORMAL=10")
    print("CHECK_INTERVAL_LIVE=2")
    print("MAX_CONCURRENT_CHECKS=5")
    print("DOUYIN_COOKIE=YOUR_ACTUAL_COOKIE")
    print("API_ENABLED=true")
    print("API_HOST=0.0.0.0")
    print("API_PORT=8000")
    print("LOG_LEVEL=INFO")
    print("EOF")
    
    print("\n然后启动系统:")
    print("./start.sh")

if __name__ == "__main__":
    main()