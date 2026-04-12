#!/bin/bash

# 抖音监控系统启动脚本

set -e

echo "抖音监控系统启动中..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    echo "请先安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 创建必要的目录
mkdir -p logs data config

# 复制环境配置文件（如果不存在）
if [ ! -f .env ]; then
    echo "复制环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置您的设置"
    echo "然后再次运行 ./start.sh"
    exit 0
fi

# 检查Python依赖
echo "检查Python依赖..."
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "安装Python依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 启动Docker服务
echo "启动Docker服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 初始化数据库
echo "初始化数据库..."
sleep 5

# 运行数据库迁移（如果需要）
# 这里可以添加数据库迁移命令

# 启动监控系统
echo "启动监控系统..."
if [ "$1" = "background" ]; then
    echo "在后台运行监控系统..."
    nohup python main.py > logs/startup.log 2>&1 &
    echo "监控系统已在后台运行"
    echo "查看日志: tail -f logs/app_$(date +%Y-%m-%d).log"
else
    echo "在前台运行监控系统..."
    echo "按 Ctrl+C 停止"
    python main.py
fi

echo ""
echo "抖音监控系统已启动！"
echo ""
echo "访问以下服务："
echo "- 监控系统API: http://localhost:8000"
echo "- Grafana仪表板: http://localhost:3000 (admin/admin123)"
echo "- InfluxDB UI: http://localhost:8086 (admin/admin123)"
echo ""
echo "管理命令："
echo "- 停止服务: docker-compose down"
echo "- 查看日志: docker-compose logs -f"
echo "- 重启服务: docker-compose restart"
echo "- 更新代码后重启: ./restart.sh"