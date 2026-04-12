#!/bin/bash

# 抖音监控系统重启脚本

set -e

echo "重启抖音监控系统..."

# 停止服务
echo "停止服务..."
docker-compose down

# 等待完全停止
sleep 5

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo "抖音监控系统已重启！"
echo ""
echo "访问以下服务："
echo "- 监控系统API: http://localhost:8000"
echo "- Grafana仪表板: http://localhost:3000"
echo "- InfluxDB UI: http://localhost:8086"