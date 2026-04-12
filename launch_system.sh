#!/bin/bash
# 抖音监控系统启动脚本

set -e

echo "🎬 抖音监控系统启动"
echo "=========================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "目录: $(pwd)"
echo "=========================================="

# 检查环境
echo ""
echo "🔍 检查系统环境..."

# 检查Python环境
if [ ! -d "venv" ]; then
    echo "❌ Python虚拟环境不存在"
    echo "运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查数据库服务
echo "检查数据库服务..."
if ! docker-compose ps | grep -q "Up"; then
    echo "启动数据库服务..."
    docker-compose up -d postgres redis influxdb
    sleep 5
fi

# 显示服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

# 检查端口
echo ""
echo "🔌 检查网络端口:"
PORTS="5432 6379 8086 8000"
for port in $PORTS; do
    if nc -z localhost $port 2>/dev/null; then
        echo "  ✅ 端口 $port 已开放"
    else
        echo "  ⚠️  端口 $port 未开放"
    fi
done

# 检查配置文件
echo ""
echo "📝 检查配置文件..."
if [ -f ".env" ]; then
    echo "  ✅ .env 文件存在"
    if grep -q "DOUYIN_COOKIE=" .env; then
        COOKIE_LINE=$(grep "DOUYIN_COOKIE=" .env)
        if [[ "$COOKIE_LINE" != *"your_cookie_here"* ]] && [[ "$COOKIE_LINE" != *"# DOUYIN_COOKIE"* ]]; then
            COOKIE_VALUE=$(echo "$COOKIE_LINE" | cut -d'=' -f2-)
            echo "  ✅ 抖音Cookie已配置 (长度: ${#COOKIE_VALUE})"
            MODE="完整模式"
        else
            echo "  ⚠️  抖音Cookie未配置或使用默认值"
            MODE="演示模式"
        fi
    else
        echo "  ❌ 未找到抖音Cookie配置"
        MODE="演示模式"
    fi
else
    echo "  ❌ .env 文件不存在"
    MODE="演示模式"
fi

# 选择启动模式
echo ""
echo "🚀 启动选项:"
echo "  1. 完整模式 (需要配置抖音Cookie)"
echo "  2. 演示模式 (模拟数据)"
echo "  3. 仅启动API服务器"
echo "  4. 退出"

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "启动完整监控系统..."
        source venv/bin/activate
        python main.py
        ;;
    2)
        echo "启动演示模式..."
        source venv/bin/activate
        python start_demo.py
        ;;
    3)
        echo "启动API服务器..."
        source venv/bin/activate
        python start_simple_api.py
        ;;
    4)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择，使用演示模式"
        source venv/bin/activate
        python start_demo.py
        ;;
esac

# 显示访问信息
echo ""
echo "=========================================="
echo "🌐 访问信息"
echo "=========================================="
echo "API地址: http://localhost:8000"
echo "健康检查: http://localhost:8000/api/health"
echo "系统状态: http://localhost:8000/api/system/status"
echo ""
echo "运行模式: $MODE"
echo ""
echo "💡 提示:"
echo "  - 按 Ctrl+C 停止系统"
echo "  - 查看日志: tail -f logs/app.log"
echo "  - 配置Cookie后重启系统启用完整功能"
echo "=========================================="