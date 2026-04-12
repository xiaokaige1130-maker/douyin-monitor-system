# 抖音监控系统 - 部署指南

## 系统概述

这是一个24小时全自动监控抖音同行开播时间、开播时长、直播间数据的系统。系统采用微服务架构，包含以下组件：

1. **监控核心** - Python应用，负责数据采集和调度
2. **PostgreSQL** - 主数据库，存储账号、直播会话等结构化数据
3. **Redis** - 缓存和队列服务
4. **InfluxDB** - 时间序列数据库，存储实时监控数据
5. **Grafana** - 数据可视化仪表板
6. **FastAPI** - RESTful API服务器

## 快速部署

### 步骤1: 环境准备

```bash
# 1. 安装Docker和Docker Compose
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 2. 克隆或复制项目文件到目标服务器
cd /opt
mkdir douyin_monitor
# 复制所有项目文件到此目录
```

### 步骤2: 配置文件

```bash
cd /opt/douyin_monitor

# 1. 复制环境配置文件
cp .env.example .env

# 2. 编辑配置文件
vim .env
```

主要配置项：
```bash
# 抖音API配置（关键）
DOUYIN_COOKIE=你的抖音Cookie  # 从浏览器获取
DOUYIN_TOKEN=你的抖音Token    # 可选

# 通知配置（可选但推荐）
DINGTALK_WEBHOOK=钉钉机器人Webhook
WECHAT_WEBHOOK=企业微信机器人Webhook

# 监控账号（启动后通过API添加）
# 无需在此配置，通过API动态添加
```

### 步骤3: 启动系统

```bash
# 1. 给脚本执行权限
chmod +x start.sh restart.sh stop.sh

# 2. 启动Docker服务
docker-compose up -d

# 3. 等待服务启动（约1-2分钟）
sleep 60

# 4. 检查服务状态
docker-compose ps

# 应该看到5个服务运行:
# - postgres
# - redis  
# - influxdb
# - grafana
# - monitor
```

### 步骤4: 安装Python依赖

```bash
# 1. 创建Python虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 步骤5: 启动监控系统

```bash
# 前台运行（测试用）
python main.py

# 或后台运行（生产环境）
nohup python main.py > logs/app.log 2>&1 &
```

## 验证部署

### 检查服务状态

```bash
# 1. 检查Docker服务
docker-compose ps

# 2. 检查API服务
curl http://localhost:8000/api/health

# 3. 检查Grafana
# 浏览器访问: http://服务器IP:3000
# 用户名: admin
# 密码: admin123
```

### 添加监控账号

```bash
# 通过API添加要监控的抖音账号
curl -X POST "http://localhost:8000/api/accounts?douyin_id=目标抖音ID&nickname=账号昵称"

# 示例:
curl -X POST "http://localhost:8000/api/accounts?douyin_id=douyin123&nickname=测试主播"
```

### 查看监控数据

```bash
# 1. 查看所有监控账号
curl http://localhost:8000/api/accounts

# 2. 查看活跃直播
curl http://localhost:8000/api/lives/active

# 3. 查看系统状态
curl http://localhost:8000/api/system/status
```

## 生产环境配置

### 性能优化

1. **调整监控频率**
   ```bash
   # 在 .env 文件中调整
   CHECK_INTERVAL_NORMAL=15      # 非开播期检查间隔（分钟）
   CHECK_INTERVAL_LIVE=1         # 开播期检查间隔（分钟）
   MAX_CONCURRENT_CHECKS=10      # 最大并发检查数
   ```

2. **数据库优化**
   ```bash
   # PostgreSQL配置调整
   # 编辑 docker-compose.yml 中的 postgres 服务
   environment:
     POSTGRES_SHARED_BUFFERS: 256MB
     POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
   ```

3. **使用代理IP**
   ```bash
   # 在 .env 中配置代理
   PROXY_ENABLED=true
   PROXY_URL=http://proxy-server:port
   ```

### 安全配置

1. **修改默认密码**
   ```bash
   # 修改 docker-compose.yml 中的密码
   POSTGRES_PASSWORD=强密码
   GF_SECURITY_ADMIN_PASSWORD=强密码
   DOCKER_INFLUXDB_INIT_PASSWORD=强密码
   ```

2. **配置防火墙**
   ```bash
   # 只开放必要端口
   sudo ufw allow 22/tcp      # SSH
   sudo ufw allow 8000/tcp    # API
   sudo ufw allow 3000/tcp    # Grafana
   sudo ufw enable
   ```

3. **使用HTTPS**
   ```nginx
   # 配置Nginx反向代理
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
       }
   }
   ```

## 监控和维护

### 日志管理

```bash
# 查看应用日志
tail -f logs/app_$(date +%Y-%m-%d).log

# 查看Docker服务日志
docker-compose logs -f monitor
docker-compose logs -f postgres

# 错误日志位置
logs/error.log
docker-compose logs --tail=100 | grep -i error
```

### 数据备份

```bash
# 1. PostgreSQL备份
docker-compose exec postgres pg_dump -U douyin douyin_monitor > backup_$(date +%Y%m%d).sql

# 2. InfluxDB备份
docker-compose exec influxdb influx backup /var/lib/influxdb2/backup

# 3. 配置文件备份
tar czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

### 系统监控

1. **资源监控**
   ```bash
   # CPU和内存使用
   docker stats
   
   # 磁盘空间
   df -h
   ```

2. **服务健康检查**
   ```bash
   # 自动健康检查脚本
   # 创建 /opt/douyin_monitor/health_check.sh
   # 定期检查服务状态并发送告警
   ```

## 故障排除

### 常见问题

1. **抖音API访问失败**
   ```
   症状: 无法获取直播数据
   解决: 
   - 检查DOUYIN_COOKIE是否有效
   - 降低请求频率
   - 使用代理IP
   ```

2. **数据库连接失败**
   ```
   症状: 应用无法启动，数据库连接错误
   解决:
   - 检查PostgreSQL是否运行: docker-compose ps postgres
   - 检查连接配置: .env 中的 DATABASE_URL
   - 重启数据库: docker-compose restart postgres
   ```

3. **内存不足**
   ```
   症状: 服务频繁重启，性能下降
   解决:
   - 增加服务器内存
   - 调整监控频率，减少并发
   - 清理旧数据
   ```

4. **监控账号不更新**
   ```
   症状: 账号状态不更新
   解决:
   - 检查账号是否被抖音限制
   - 检查网络连接
   - 查看应用日志中的错误信息
   ```

### 调试命令

```bash
# 进入容器调试
docker-compose exec monitor bash
docker-compose exec postgres psql -U douyin douyin_monitor

# 查看实时日志
docker-compose logs -f --tail=50

# 重启单个服务
docker-compose restart monitor

# 完全重置（慎用）
docker-compose down -v
docker-compose up -d
```

## 升级和更新

### 代码更新

```bash
# 1. 备份当前配置和数据
./stop.sh
cp .env .env.backup
docker-compose exec postgres pg_dump -U douyin douyin_monitor > backup.sql

# 2. 更新代码
git pull  # 或手动复制新文件

# 3. 恢复配置
cp .env.backup .env

# 4. 重启服务
./start.sh
```

### 数据迁移

```bash
# 如果有数据库结构变更
# 1. 创建迁移脚本
# 2. 备份数据
# 3. 执行迁移
docker-compose exec postgres psql -U douyin douyin_monitor -f migration.sql
```

## 扩展功能

### 添加新的数据源

1. 修改 `core/monitor.py` 中的 `_check_account_live_status` 方法
2. 添加新的数据采集逻辑
3. 更新数据模型（如果需要）

### 自定义通知渠道

1. 在 `core/notifier.py` 中添加新的通知方法
2. 更新配置管理
3. 在 `send_notification` 方法中调用新渠道

### 集成第三方服务

1. **数据导出到其他系统**
   ```python
   # 在数据采集后添加导出逻辑
   async def export_to_bi_system(self, data):
       # 导出到商业智能系统
       pass
   ```

2. **Webhook通知**
   ```python
   # 添加Webhook支持
   async def send_webhook(self, url, data):
       async with aiohttp.ClientSession() as session:
           await session.post(url, json=data)
   ```

## 技术支持

### 获取帮助

1. **查看文档**
   - README.md - 基本使用
   - API文档: http://localhost:8000/docs

2. **检查日志**
   ```bash
   grep -i error logs/app_*.log
   docker-compose logs | tail -100
   ```

3. **社区支持**
   - GitHub Issues
   - 技术论坛

### 紧急恢复

```bash
# 1. 停止所有服务
./stop.sh

# 2. 备份当前状态
cp -r data/ data_backup_$(date +%Y%m%d_%H%M%S)/
docker-compose exec postgres pg_dumpall -U douyin > full_backup.sql

# 3. 从备份恢复
# 根据备份文件恢复数据
```

---

**重要提示**: 本系统需要定期维护和更新，特别是抖音API接口可能发生变化，需要及时调整采集逻辑。