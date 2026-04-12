#!/bin/bash

# 抖音监控系统一键安装脚本

set -e

echo "========================================="
echo "  抖音监控系统一键安装脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    log_warn "建议使用root权限运行此脚本"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查系统
log_info "检查系统环境..."

# 检查操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    log_info "操作系统: $OS $VER"
else
    log_error "无法检测操作系统"
    exit 1
fi

# 检查Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    log_info "Docker已安装: $DOCKER_VERSION"
else
    log_error "Docker未安装"
    read -p "是否安装Docker? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "安装Docker..."
        
        if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
            apt-get update
            apt-get install -y docker.io docker-compose
        elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
            yum install -y docker docker-compose
            systemctl start docker
            systemctl enable docker
        else
            log_error "不支持的操作系统，请手动安装Docker"
            exit 1
        fi
    else
        log_error "需要Docker才能继续"
        exit 1
    fi
fi

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_info "Python已安装: $PYTHON_VERSION"
else
    log_error "Python3未安装"
    read -p "是否安装Python3? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "安装Python3..."
        
        if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
            apt-get install -y python3 python3-pip python3-venv
        elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
            yum install -y python3 python3-pip
        else
            log_error "不支持的操作系统，请手动安装Python3"
            exit 1
        fi
    else
        log_error "需要Python3才能继续"
        exit 1
    fi
fi

# 创建安装目录
INSTALL_DIR="/opt/douyin_monitor"
log_info "安装目录: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    log_warn "目录已存在: $INSTALL_DIR"
    read -p "是否覆盖? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "备份旧目录..."
        BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        log_info "已备份到: $BACKUP_DIR"
    else
        log_info "在现有目录继续安装..."
    fi
fi

# 创建目录结构
log_info "创建目录结构..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 复制文件（这里假设脚本在当前目录运行）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
    log_info "复制文件到安装目录..."
    cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/ 2>/dev/null || true
fi

# 设置文件权限
log_info "设置文件权限..."
chmod +x start.sh restart.sh stop.sh install.sh

# 创建必要目录
mkdir -p logs data config

# 配置环境文件
if [ ! -f .env ]; then
    log_info "创建环境配置文件..."
    if [ -f .env.example ]; then
        cp .env.example .env
        log_warn "请编辑 .env 文件配置您的设置:"
        log_warn "  vim $INSTALL_DIR/.env"
        log_warn "重要配置项:"
        log_warn "  - DOUYIN_COOKIE: 抖音Cookie（从浏览器获取）"
        log_warn "  - 通知配置: 钉钉/微信/邮件通知"
    else
        log_error "找不到 .env.example 文件"
        exit 1
    fi
else
    log_info "使用现有的 .env 文件"
fi

# 安装Python依赖
log_info "安装Python依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    log_error "找不到 requirements.txt 文件"
    exit 1
fi

# 启动Docker服务
log_info "启动Docker服务..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# 等待服务启动
log_info "等待服务启动（约60秒）..."
for i in {1..12}; do
    echo -n "."
    sleep 5
done
echo ""

# 检查服务状态
log_info "检查服务状态..."
if docker-compose ps | grep -q "Up"; then
    log_info "✅ 服务启动成功"
else
    log_error "❌ 服务启动失败"
    docker-compose logs --tail=20
    exit 1
fi

# 创建系统服务（可选）
log_info "创建系统服务..."
cat > /etc/systemd/system/douyin-monitor.service << EOF
[Unit]
Description=Douyin Monitor System
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh background
ExecStop=$INSTALL_DIR/stop.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

read -p "是否启用系统服务开机自启? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl daemon-reload
    systemctl enable douyin-monitor.service
    log_info "✅ 系统服务已启用"
fi

# 安装完成
echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "📊 系统信息:"
echo "  - 安装目录: $INSTALL_DIR"
echo "  - 配置文件: $INSTALL_DIR/.env"
echo "  - 日志目录: $INSTALL_DIR/logs/"
echo ""
echo "🌐 访问地址:"
echo "  - 监控面板: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - API文档: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "  - Grafana: http://$(hostname -I | awk '{print $1}'):3000"
echo "    - 用户名: admin"
echo "    - 密码: admin123"
echo ""
echo "⚙️  管理命令:"
echo "  - 启动: systemctl start douyin-monitor"
echo "  - 停止: systemctl stop douyin-monitor"
echo "  - 状态: systemctl status douyin-monitor"
echo "  - 日志: tail -f $INSTALL_DIR/logs/app_*.log"
echo ""
echo "📝 下一步:"
echo "  1. 编辑配置文件: vim $INSTALL_DIR/.env"
echo "  2. 添加监控账号:"
echo "     curl -X POST \"http://localhost:8000/api/accounts?douyin_id=目标ID&nickname=账号名\""
echo "  3. 重启服务: systemctl restart douyin-monitor"
echo ""
echo "💡 提示:"
echo "  - 首次使用需要配置抖音Cookie"
echo "  - 建议配置通知渠道接收告警"
echo "  - 定期检查日志和系统状态"
echo ""
echo "========================================="