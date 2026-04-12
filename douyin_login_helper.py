#!/usr/bin/env python3
"""
抖音登录助手 - 帮助获取抖音Cookie
"""

import http.server
import socketserver
import urllib.parse
import json
import os
from datetime import datetime

# 存储获取的Cookie
captured_cookies = []

class DouyinLoginHandler(http.server.SimpleHTTPRequestHandler):
    """抖音登录页面处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/':
            # 显示登录页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = self.get_login_page()
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/api/cookies':
            # 获取已捕获的Cookie
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'success',
                'count': len(captured_cookies),
                'cookies': captured_cookies,
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        elif self.path.startswith('/capture'):
            # 捕获Cookie的页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # 从查询参数获取Cookie
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'cookie' in params:
                cookie = params['cookie'][0]
                captured_cookies.append({
                    'cookie': cookie,
                    'timestamp': datetime.now().isoformat(),
                    'length': len(cookie)
                })
                print(f"🎯 捕获到Cookie (长度: {len(cookie)}): {cookie[:50]}...")
                
            html = self.get_capture_success_page()
            self.wfile.write(html.encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_login_page(self):
        """获取登录页面HTML"""
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>抖音Cookie获取助手</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }
                
                .container {
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    padding: 40px;
                    max-width: 500px;
                    width: 100%;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .logo {
                    font-size: 48px;
                    margin-bottom: 10px;
                }
                
                h1 {
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 28px;
                }
                
                .subtitle {
                    color: #666;
                    font-size: 16px;
                    line-height: 1.5;
                }
                
                .steps {
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 30px;
                }
                
                .step {
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 15px;
                }
                
                .step-number {
                    background: #667eea;
                    color: white;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    font-weight: bold;
                    margin-right: 10px;
                    flex-shrink: 0;
                }
                
                .step-content {
                    flex: 1;
                }
                
                .step-title {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 5px;
                }
                
                .step-desc {
                    color: #666;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .login-button {
                    display: block;
                    width: 100%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 16px;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: 600;
                    cursor: pointer;
                    text-align: center;
                    text-decoration: none;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                
                .login-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
                }
                
                .qr-section {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }
                
                .qr-placeholder {
                    width: 200px;
                    height: 200px;
                    background: #e9ecef;
                    border-radius: 10px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                    font-size: 14px;
                }
                
                .note {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #856404;
                }
                
                .status {
                    margin-top: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                    font-size: 14px;
                }
                
                .status.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .status.info {
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎬</div>
                    <h1>抖音Cookie获取助手</h1>
                    <p class="subtitle">为抖音监控系统获取必要的Cookie</p>
                </div>
                
                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <div class="step-title">打开抖音网页版</div>
                            <div class="step-desc">点击下方按钮打开抖音登录页面</div>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <div class="step-title">扫码登录</div>
                            <div class="step-desc">使用抖音App扫描二维码登录</div>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <div class="step-title">获取Cookie</div>
                            <div class="step-desc">登录成功后自动获取Cookie</div>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <div class="step-title">配置系统</div>
                            <div class="step-desc">将Cookie复制到监控系统配置</div>
                        </div>
                    </div>
                </div>
                
                <a href="https://www.douyin.com" target="_blank" class="login-button">
                    🚀 打开抖音网页版
                </a>
                
                <div class="qr-section">
                    <div class="qr-placeholder">
                        📱<br>抖音App扫码登录
                    </div>
                    <p>打开抖音App，扫描二维码登录</p>
                </div>
                
                <div class="note">
                    <strong>💡 提示：</strong>登录后，请在浏览器开发者工具(F12)的Network标签中，
                    找到任意请求，复制Request Headers中的Cookie值。
                </div>
                
                <div id="status" class="status info">
                    等待登录并获取Cookie...
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <button onclick="showCookieForm()" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                    ">
                        手动输入Cookie
                    </button>
                </div>
                
                <div id="cookieForm" style="display: none; margin-top: 20px;">
                    <textarea id="cookieInput" placeholder="在此粘贴抖音Cookie..." style="
                        width: 100%;
                        height: 100px;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-family: monospace;
                        font-size: 12px;
                        margin-bottom: 10px;
                    "></textarea>
                    <button onclick="submitCookie()" style="
                        background: #28a745;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        width: 100%;
                    ">
                        提交Cookie
                    </button>
                </div>
            </div>
            
            <script>
                function showCookieForm() {
                    document.getElementById('cookieForm').style.display = 'block';
                }
                
                function submitCookie() {
                    const cookie = document.getElementById('cookieInput').value.trim();
                    if (!cookie) {
                        alert('请输入Cookie');
                        return;
                    }
                    
                    // 发送Cookie到服务器
                    fetch('/capture?cookie=' + encodeURIComponent(cookie))
                        .then(response => {
                            if (response.ok) {
                                document.getElementById('status').className = 'status success';
                                document.getElementById('status').innerHTML = 
                                    '✅ Cookie已成功捕获！长度：' + cookie.length + ' 字符';
                                
                                // 显示配置指令
                                setTimeout(() => {
                                    const configCmd = `echo "DOUYIN_COOKIE=${cookie}" >> .env`;
                                    alert('Cookie已捕获！\\n\\n配置系统命令：\\n' + configCmd);
                                }, 500);
                            }
                        })
                        .catch(error => {
                            alert('提交失败：' + error);
                        });
                }
                
                // 自动检查Cookie
                function checkCookies() {
                    fetch('/api/cookies')
                        .then(response => response.json())
                        .then(data => {
                            if (data.count > 0) {
                                const cookie = data.cookies[data.cookies.length - 1];
                                document.getElementById('status').className = 'status success';
                                document.getElementById('status').innerHTML = 
                                    '✅ 已捕获Cookie！长度：' + cookie.length + ' 字符';
                            }
                        });
                }
                
                // 每5秒检查一次
                setInterval(checkCookies, 5000);
            </script>
        </body>
        </html>
        """
    
    def get_capture_success_page(self):
        """获取捕获成功页面"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cookie捕获成功</title>
            <style>
                body {
                    font-family: sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f0f2f5;
                }
                .success-box {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }
                .success-icon {
                    font-size: 60px;
                    color: #52c41a;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                .instructions {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }
                code {
                    background: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }
                .button {
                    display: inline-block;
                    background: #1890ff;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 5px;
                    text-decoration: none;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="success-icon">✅</div>
                <h1>Cookie捕获成功！</h1>
                <p>抖音Cookie已成功捕获并保存。</p>
                
                <div class="instructions">
                    <h3>下一步：配置监控系统</h3>
                    <p>1. 打开终端，进入项目目录：</p>
                    <code>cd /home/huyankai/.openclaw/workspace/douyin_monitor</code>
                    
                    <p style="margin-top: 15px;">2. 编辑配置文件：</p>
                    <code>vim .env</code>
                    
                    <p style="margin-top: 15px;">3. 设置Cookie（取消注释并粘贴）：</p>
                    <code>DOUYIN_COOKIE=你的Cookie值</code>
                    
                    <p style="margin-top: 15px;">4. 重启监控系统：</p>
                    <code>按Ctrl+C停止当前，然后运行：python main.py</code>
                </div>
                
                <a href="/" class="button">返回首页</a>
                <a href="/api/cookies" class="button" style="background: #6c757d; margin-left: 10px;">查看Cookie</a>
            </div>
        </body>
        </html>
        """
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_login_helper(port=8080):
    """启动登录助手服务器"""
    print("=" * 60)
    print("🎬 抖音登录助手")
    print("=" * 60)
    print(f"服务器启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"访问地址: http://localhost:{port}")
    print()
    print("📱 使用步骤:")
    print("  1. 打开上面的链接")
    print("  2. 点击'打开抖音网页版'按钮")
    print("  3. 使用抖音App扫码登录")
    print("  4. 登录后复制Cookie")
    print("  5. 在页面中粘贴Cookie")
    print()
    print("💡 提示:")
    print("  - 登录后按F12打开开发者工具")
    print("  - 在Network标签中找到任意请求")
    print("  - 复制Request Headers中的Cookie值")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", port), DouyinLoginHandler) as httpd:
            print(f"✅ 服务器已在端口 {port} 启动")
            print("📢 按 Ctrl+C 停止服务器")
            print()
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n📢 服务器已停止")
        print(f"🎯 共捕获 {len(captured_cookies)} 个Cookie")
        
        if captured_cookies:
            print("\n📋 捕获的Cookie:")
            for i, cookie_info in enumerate(captured_cookies, 1):
                cookie = cookie_info['cookie']
                print(f"\n[{i}] 长度: {len(cookie)}")
                print(f"    前50字符: {cookie[:50]}...")
                
                # 生成配置命令
                config_cmd = f'echo "DOUYIN_COOKIE={cookie}" >> .env'
                print(f"    配置命令: {config_cmd}")
        
        print("\n🚀 配置监控系统:")
        print("  cd /home/huyankai/.openclaw/workspace/douyin_monitor")
        print("  vim .env  # 设置DOUYIN_COOKIE")
        print("  重启系统")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    start_login_helper()