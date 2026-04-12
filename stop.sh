#!/bin/bash

# 抖音监控系统停止脚本

echo "停止抖音监控系统..."

# 停止Docker服务
docker-compose down

# 停止Python进程
pkill -f "python main.py" || true

echo "抖音监控系统已停止！"

# 显示仍在运行的进程
echo ""
echo "检查仍在运行的进程："
ps aux | grep -E "(main\.py|python.*monitor)" | grep -v grep || echo "没有找到相关进程"