#!/bin/bash
# 抖音监控系统一键配置脚本
# 用法: ./configure_with_cookie.sh "你的抖音Cookie"

set -e

echo "🎬 抖音监控系统配置脚本"
echo "=========================================="

COOKIE="$1"

if [ -z "$COOKIE" ]; then
    echo "❌ 错误: 请提供抖音Cookie作为参数"
    echo "用法: $0 \"你的抖音Cookie\""
    echo ""
    echo "获取Cookie步骤:"
    echo "1. 访问 https://www.douyin.com"
    echo "2. 扫码登录"
    echo "3. 按F12打开开发者工具"
    echo "4. 切换到Network标签"
    echo "5. 刷新页面"
    echo "6. 复制任意请求的Cookie值"
    exit 1
fi

echo "🔧 检查当前目录..."
cd /home/huyankai/.openclaw/workspace/douyin_monitor
echo "   工作目录: $(pwd)"

echo ""
echo "📊 Cookie信息:"
echo "   长度: ${#COOKIE} 字符"
echo "   预览: ${COOKIE:0:80}..."

# 检查是否包含抖音关键字段
if [[ "$COOKIE" == *"passport_csrf_token"* ]] || [[ "$COOKIE" == *"sid_tt"* ]] || [[ "$COOKIE" == *"sessionid"* ]]; then
    echo "   ✅ 包含抖音Cookie关键字段"
else
    echo "   ⚠️  未检测到抖音关键字段，请确认Cookie正确"
    read -p "   是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📝 更新配置文件..."

# 备份现有配置
if [ -f .env ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_FILE"
    echo "   ✅ 配置文件已备份: $BACKUP_FILE"
fi

# 创建新的配置文件
cat > .env << EOF
# 抖音监控系统配置
# 生成时间: $(date)

# 数据库配置
DATABASE_URL=postgresql://douyin:douyin123@localhost:5432/douyin_monitor
REDIS_URL=redis://localhost:6379/0

# InfluxDB配置
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=douyin-token-123
INFLUXDB_ORG=douyin
INFLUXDB_BUCKET=douyin_data

# 监控配置
CHECK_INTERVAL_NORMAL=10      # 非开播期检查间隔（分钟）
CHECK_INTERVAL_LIVE=2         # 开播期检查间隔（分钟）
MAX_CONCURRENT_CHECKS=5       # 最大并发检查数

# 抖音API配置
DOUYIN_COOKIE=${COOKIE}

# 代理配置（可选）
# PROXY_ENABLED=false
# PROXY_URL=http://proxy:port

# 通知配置
NOTIFICATION_ENABLED=true
# 钉钉机器人Webhook
# DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
# 企业微信机器人Webhook
# WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
# 邮件配置
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_USERNAME=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
# EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com

# API配置
API_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 数据保留配置
DATA_RETENTION_DAYS=30

# 浏览器配置
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30

# 请求配置
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5
EOF

echo "   ✅ 配置文件已更新: .env"

# 创建Cookie备份
COOKIE_BACKUP="douyin_cookie_$(date +%Y%m%d_%H%M%S).txt"
echo "$COOKIE" > "$COOKIE_BACKUP"
echo "   ✅ Cookie备份已保存: $COOKIE_BACKUP"

echo ""
echo "🔍 验证配置..."
if grep -q "DOUYIN_COOKIE=" .env; then
    CONFIGURED_COOKIE=$(grep "DOUYIN_COOKIE=" .env | cut -d'=' -f2-)
    if [ "${#CONFIGURED_COOKIE}" -eq "${#COOKIE}" ]; then
        echo "   ✅ Cookie配置验证通过"
    else
        echo "   ⚠️  Cookie长度不匹配，请检查配置"
    fi
else
    echo "   ❌ Cookie配置未找到"
fi

echo ""
echo "🚀 下一步操作:"
echo "=========================================="
echo ""
echo "1. 停止当前运行的系统（如果正在运行）:"
echo "   按 Ctrl+C 停止所有相关进程"
echo ""
echo "2. 确保数据库服务运行:"
echo "   docker-compose up -d postgres redis influxdb"
echo ""
echo "3. 启动完整监控系统:"
echo "   ./start.sh"
echo "   或"
echo "   python main.py"
echo ""
echo "4. 验证系统运行:"
echo "   curl http://localhost:8000/api/health"
echo ""
echo "5. 添加监控账号:"
echo '   curl -X POST "http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名"'
echo ""
echo "6. 开始监控:"
echo "   系统将自动开始24小时监控"
echo ""
echo "💡 提示:"
echo "   - Cookie通常有效期为几天到几周"
echo "   - 失效时需要重新获取并更新配置"
echo "   - 监控多个账号需要每个账号独立的Cookie"
echo ""
echo "🎉 配置完成！现在可以启动完整监控系统了。"

# 检查数据库服务状态
echo ""
echo "🔧 检查数据库服务..."
if docker-compose ps | grep -q "Up"; then
    echo "   ✅ 数据库服务正在运行"
else
    echo "   ⚠️  数据库服务未运行，正在启动..."
    docker-compose up -d postgres redis influxdb
    sleep 5
    echo "   ✅ 数据库服务已启动"
fi

echo ""
echo "📋 快速启动命令:"
echo "   # 停止现有进程（如果需要）"
echo "   pkill -f \"python.*main.py\" 2>/dev/null || true"
echo ""
echo "   # 启动监控系统"
echo "   cd /home/huyankai/.openclaw/workspace/douyin_monitor"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "=========================================="