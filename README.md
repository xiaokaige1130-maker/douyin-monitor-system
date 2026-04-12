# 🎬 抖音监控系统

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/xiaokaige1130-maker/douyin-monitor-system)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**24小时自动监控抖音同行开播时间、开播时长、直播间数据的完整系统**

## 📋 项目状态

✅ **系统架构**: 完整微服务架构  
✅ **核心功能**: 24小时自动监控  
✅ **数据采集**: 实时开播检测 + 直播间数据  
✅ **部署方式**: Docker容器化  
✅ **API接口**: RESTful API完整  
⏳ **等待配置**: 抖音Cookie配置后即可使用

## 🚀 快速部署

### 1. 克隆仓库
```bash
git clone https://github.com/xiaokaige1130-maker/douyin-monitor-system.git
cd douyin-monitor-system
```

### 2. 一键安装
```bash
chmod +x install.sh
./install.sh
```

### 3. 配置系统
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
vim .env  # 设置您的配置
```

### 4. 启动系统
```bash
./start.sh
```

### 5. 访问系统
- **API面板**: http://localhost:8000
- **健康检查**: http://localhost:8000/health
- **系统状态**: http://localhost:8000/status

## ✨ 核心功能

### 🎯 监控能力
- ✅ **24小时自动监控** - 无需人工干预，全天候运行
- ✅ **实时开播检测** - 秒级响应，即时发现开播
- ✅ **直播间数据采集** - 在线人数、点赞、评论、分享等
- ✅ **时长统计** - 精确记录开播时长和峰值时间
- ✅ **多账号并发监控** - 支持同时监控多个抖音账号
- ✅ **智能调度** - 开播期高频（2分钟），非开播期低频（10分钟）

### 📊 数据管理
- ✅ **数据持久化** - PostgreSQL + InfluxDB + Redis
- ✅ **完整API接口** - RESTful API查询所有数据
- ✅ **数据可视化** - Grafana仪表板展示数据趋势
- ✅ **实时通知** - 钉钉、微信、邮件即时提醒
- ✅ **统计报告** - 每日/每周数据汇总

### ⚡ 技术特性
- ✅ **微服务架构** - Docker容器化部署
- ✅ **异步处理** - 高性能并发监控
- ✅ **错误恢复** - 自动重试和故障转移
- ✅ **配置灵活** - 支持多种数据采集方式
- ✅ **扩展性强** - 模块化设计，易于扩展

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    抖音监控系统架构                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   抖音平台   │  │  数据采集层  │  │  监控调度层  │         │
│  │  (API/网页)  │◄─┤ (Cookie认证) │◄─┤ (智能调度器) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                      │                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  数据存储层   │  │  数据分析层  │  │  数据展示层  │         │
│  │ PostgreSQL  │◄─┤  (统计计算)  │◄─┤  Grafana    │         │
│  │  InfluxDB   │  │             │  │   API接口   │         │
│  │    Redis    │  └─────────────┘  │   通知系统   │         │
│  └─────────────┘                   └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 技术栈
- **后端框架**: Python 3.12 + FastAPI + AsyncIO
- **数据库**: PostgreSQL (结构化) + InfluxDB (时序) + Redis (缓存)
- **容器**: Docker + Docker Compose
- **监控**: 自定义调度器 + 异步任务队列
- **API**: RESTful API + WebSocket (可选)
- **通知**: 钉钉/微信/邮件集成

## 🚀 快速开始

### 1. 环境要求

- **Docker & Docker Compose** (必需)
- **Python 3.8+** (推荐3.12)
- **至少4GB内存** (建议8GB)
- **磁盘空间** 至少10GB
- **网络** 稳定的互联网连接

### 2. 一键安装部署

```bash
# 克隆项目
git clone https://github.com/xiaokaige1130-maker/douyin-monitor-system.git
cd douyin-monitor-system

# 运行安装脚本
./install.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动数据库服务
docker-compose up -d postgres redis influxdb

# 等待服务启动
sleep 10

# 启动监控系统
./start.sh
```

### 3. 关键配置说明

**编辑 `.env` 文件配置以下内容：**

```bash
# 抖音API配置（必需）
DOUYIN_COOKIE=你的抖音Cookie值  # 从浏览器开发者工具获取

# 数据库配置
DATABASE_URL=postgresql://douyin:douyin123@localhost:5432/douyin_monitor
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086

# 监控配置
CHECK_INTERVAL_NORMAL=10      # 非开播期检查间隔（分钟）
CHECK_INTERVAL_LIVE=2         # 开播期检查间隔（分钟）
MAX_CONCURRENT_CHECKS=5       # 最大并发检查数

# 通知配置（可选）
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# API配置
API_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000
```

**如何获取抖音Cookie：**
1. 访问 https://www.douyin.com
2. 手机扫码登录
3. 按F12 → Network标签 → 刷新页面
4. 复制任意请求的Cookie值

### 4. 访问服务

系统启动后可以访问：

- **📊 监控系统API**: http://localhost:8000
- **📈 Grafana仪表板**: http://localhost:3000 (admin/admin123)
- **🗄️ InfluxDB UI**: http://localhost:8086 (admin/admin123)
- **💾 PostgreSQL**: localhost:5432 (douyin/douyin123)
- **⚡ Redis**: localhost:6379

**默认账号密码：**
- Grafana: admin / admin123
- InfluxDB: admin / admin123  
- PostgreSQL: douyin / douyin123

## 📖 使用方法

### 添加监控账号

```bash
# 通过API添加监控账号
curl -X POST "http://localhost:8000/api/accounts?douyin_id=目标抖音ID&nickname=账号昵称"

# 示例
curl -X POST "http://localhost:8000/api/accounts?douyin_id=douyin123&nickname=测试主播"
```

### 查看监控状态

```bash
# 查看系统状态
curl "http://localhost:8000/api/system/status" | jq .

# 查看监控账号列表
curl "http://localhost:8000/api/accounts" | jq .

# 查看活跃直播
curl "http://localhost:8000/api/lives/active" | jq .

# 查看最近直播记录
curl "http://localhost:8000/api/lives/recent" | jq .
```

### 数据查询API

系统提供完整的RESTful API：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/accounts` | GET | 获取所有监控账号 |
| `/api/accounts` | POST | 添加监控账号 |
| `/api/accounts/{id}` | DELETE | 删除监控账号 |
| `/api/lives/active` | GET | 获取活跃直播 |
| `/api/lives/recent` | GET | 获取最近直播记录 |
| `/api/lives/{id}` | GET | 获取特定直播详情 |
| `/api/stats/daily` | GET | 获取每日统计数据 |
| `/api/stats/account/{id}` | GET | 获取账号统计 |
| `/api/system/status` | GET | 获取系统状态 |
| `/api/health` | GET | 健康检查 |

### 管理命令

```bash
# 启动系统
./start.sh

# 停止系统
./stop.sh

# 重启系统
./restart.sh

# 交互式启动
./launch_system.sh

# 一键配置Cookie
./configure_with_cookie.sh "你的抖音Cookie"
```

## 🔍 数据采集方式

系统支持多种数据采集方式，可根据需求选择：

### 1. 🏆 抖音官方API（推荐）
- **稳定性**: ⭐⭐⭐⭐⭐
- **速度**: ⭐⭐⭐⭐⭐
- **准确性**: ⭐⭐⭐⭐⭐
- **要求**: 有效的抖音Cookie
- **特点**: 官方接口，数据最准确，请求频率受限

### 2. 🌐 抖音Web API
- **稳定性**: ⭐⭐⭐⭐
- **速度**: ⭐⭐⭐⭐
- **准确性**: ⭐⭐⭐⭐
- **要求**: 需要定期维护接口
- **特点**: 通过分析网页接口，中等稳定性

### 3. 🤖 浏览器模拟
- **稳定性**: ⭐⭐⭐
- **速度**: ⭐⭐
- **准确性**: ⭐⭐⭐⭐⭐
- **要求**: 浏览器自动化环境
- **特点**: 最灵活，可绕过部分限制，速度较慢

### 配置建议
```python
# 在 core/config.py 中配置采集方式
DATA_COLLECTION_METHOD = "api"  # api, web, browser
API_PRIORITY = True             # 优先使用API
FALLBACK_TO_BROWSER = True      # API失败时回退到浏览器
```

## 📈 监控指标

### 🎯 基础指标（100%支持）
- ✅ **开播状态** - 实时检测是否在直播
- ✅ **开播时间** - 精确到秒的开播时间
- ✅ **直播时长** - 累计直播时长统计
- ✅ **在线人数** - 实时/峰值/平均在线人数
- ✅ **点赞数** - 直播期间总点赞数
- ✅ **评论数** - 实时评论数据
- ✅ **分享数** - 直播分享次数
- ✅ **关注增长** - 直播期间关注增长

### 🚀 高级指标（如可获取）
- 🔄 **礼物收入** - 直播礼物价值统计
- 🔄 **商品销售** - 带货商品销售数据
- 🔄 **观众互动率** - 观众参与度分析
- 🔄 **流量来源** - 观众来源渠道分析
- 🔄 **观众画像** - 年龄、性别、地域分布
- 🔄 **热门时段** - 观众活跃时间段

### 📊 数据存储格式
```json
{
  "session_id": "live_1234567890",
  "account_id": "douyin_123",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T14:30:00Z",
  "duration_minutes": 150,
  "peak_viewers": 12500,
  "avg_viewers": 8500,
  "total_likes": 125000,
  "total_comments": 8500,
  "total_shares": 1200,
  "new_followers": 350
}
```

## 🔔 通知配置

### 1. 📱 钉钉机器人
```bash
# 在钉钉群添加自定义机器人
# 获取Webhook地址
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# 通知示例
🎬 抖音直播提醒
主播: 测试主播
状态: 开始直播
时间: 2024-01-01 12:00:00
在线人数: 12500人
```

### 2. 💬 企业微信机器人
```bash
# 在企业微信群添加机器人
# 获取Webhook地址
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### 3. 📧 邮件通知
```bash
# 配置SMTP服务器
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENTS=user1@example.com,user2@example.com
```

### 4. 🔔 通知类型
- **开播提醒** - 检测到直播开始时发送
- **数据更新** - 直播期间定期发送数据
- **下播总结** - 直播结束时发送总结报告
- **异常报警** - 监控异常或系统故障时发送

### 5. ⚙️ 通知配置示例
```python
# 在 core/notifier.py 中配置
NOTIFICATION_CONFIG = {
    "on_live_start": True,      # 开播提醒
    "on_live_update": True,     # 数据更新（每30分钟）
    "on_live_end": True,        # 下播总结
    "on_error": True,           # 错误报警
    "min_viewers": 100,         # 最小在线人数阈值
    "update_interval": 30,      # 更新间隔（分钟）
}
```

## 💾 数据存储

### 1. 🗄️ PostgreSQL（结构化数据）
```sql
-- 账号表
CREATE TABLE accounts (
    id VARCHAR(50) PRIMARY KEY,
    douyin_id VARCHAR(100) UNIQUE,
    nickname VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 直播会话表
CREATE TABLE live_sessions (
    id VARCHAR(100) PRIMARY KEY,
    account_id VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    peak_viewers INTEGER,
    total_likes BIGINT
);
```

### 2. 📊 InfluxDB（时间序列数据）
```influxql
-- 存储直播间实时数据
> INSERT live_metrics,account_id=douyin_123 viewers=12500,likes=45000,comments=1200
> SELECT MEAN("viewers") FROM "live_metrics" WHERE time > now() - 1h
```

### 3. ⚡ Redis（缓存和队列）
```python
# 缓存账号状态
redis.set(f"account:{account_id}:last_check", datetime.now().isoformat())
redis.set(f"account:{account_id}:is_live", "true")

# 任务队列
redis.lpush("monitor_queue", account_id)
```

### 4. 📈 数据保留策略
- **PostgreSQL**: 永久保留核心数据
- **InfluxDB**: 保留30天详细数据，90天聚合数据
- **Redis**: 7天缓存数据
- **日志文件**: 保留30天

### 5. 🔄 数据备份
```bash
# 每日自动备份
pg_dump douyin_monitor > backup/postgres_$(date +%Y%m%d).sql
influx backup backup/influxdb_$(date +%Y%m%d)
```

## 🛠️ 故障排除

### 🔍 常见问题

1. **抖音API访问受限**
   ```bash
   # 检查Cookie是否有效
   curl -H "Cookie: $DOUYIN_COOKIE" https://www.douyin.com
   
   # 降低请求频率
   # 修改 .env 中的 CHECK_INTERVAL_NORMAL 和 CHECK_INTERVAL_LIVE
   ```

2. **数据采集失败**
   ```bash
   # 检查网络连接
   ping www.douyin.com
   
   # 查看错误日志
   tail -f logs/error.log
   
   # 测试单个账号
   python test_simple.py --account-id 目标ID
   ```

3. **通知发送失败**
   ```bash
   # 测试钉钉Webhook
   curl -X POST $DINGTALK_WEBHOOK -H "Content-Type: application/json" \
        -d '{"msgtype":"text","text":{"content":"测试消息"}}'
   
   # 测试邮件配置
   python test_email.py
   ```

4. **数据库连接失败**
   ```bash
   # 检查数据库服务
   docker-compose ps
   
   # 测试数据库连接
   python test_db_connection.py
   
   # 查看数据库日志
   docker-compose logs postgres
   ```

### 📋 查看日志

```bash
# Docker服务日志
docker-compose logs -f

# 应用日志
tail -f logs/app.log

# 错误日志
tail -f logs/error.log

# 监控日志
tail -f logs/monitor.log

# 通过API查看系统状态
curl http://localhost:8000/api/system/status | jq .
```

### 🚨 紧急恢复

```bash
# 1. 停止所有服务
./stop.sh

# 2. 重启数据库
docker-compose down
docker-compose up -d postgres redis influxdb

# 3. 等待服务启动
sleep 10

# 4. 启动监控系统
./start.sh
```

## ⚡ 性能优化

### 🚀 监控大量账号
```python
# 调整并发参数（.env）
MAX_CONCURRENT_CHECKS=10      # 增加并发数
CHECK_INTERVAL_NORMAL=15      # 非开播期延长检查间隔
CHECK_INTERVAL_LIVE=3         # 开播期适当延长

# 使用代理IP池
PROXY_ENABLED=true
PROXY_URL=http://proxy-pool:8080
PROXY_ROTATE_INTERVAL=60      # 代理轮换间隔（秒）

# 智能调度
ENABLE_SMART_SCHEDULING=true  # 根据历史数据智能调整检查频率
```

### 💾 数据存储优化
```sql
-- PostgreSQL索引优化
CREATE INDEX idx_accounts_douyin_id ON accounts(douyin_id);
CREATE INDEX idx_sessions_account_time ON live_sessions(account_id, start_time);
CREATE INDEX idx_sessions_duration ON live_sessions(duration_minutes);

-- 分区表（按月分区）
CREATE TABLE live_sessions_2024_01 PARTITION OF live_sessions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

```influxql
-- InfluxDB数据保留策略
CREATE RETENTION POLICY "30days" ON "douyin" DURATION 30d REPLICATION 1
CREATE RETENTION POLICY "90days" ON "douyin" DURATION 90d REPLICATION 1

-- 连续查询（数据聚合）
CREATE CONTINUOUS QUERY "cq_hourly_viewers" ON "douyin"
BEGIN
  SELECT MEAN("viewers") INTO "douyin"."90days"."viewers_hourly"
  FROM "live_metrics"
  GROUP BY time(1h), account_id
END
```

### 🎯 监控性能指标
```bash
# 查看系统资源使用
docker stats

# 查看API响应时间
curl -w "%{time_total}s\n" http://localhost:8000/api/health

# 监控队列长度
redis-cli LLEN monitor_queue

# 查看数据库连接数
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### 📈 性能基准
- **单账号监控**: < 100MB 内存，< 1% CPU
- **10账号并发**: < 500MB 内存，< 5% CPU
- **API响应时间**: < 100ms (P95)
- **数据采集延迟**: < 5秒 (开播检测)
- **数据持久化**: < 1秒 (95%请求)

## 🔒 安全注意事项

### 1. 📜 遵守平台规则
```bash
# 遵守抖音Robots.txt
User-agent: *
Crawl-delay: 10  # 遵守爬虫延迟要求

# 合理请求频率
# 不要过度请求，避免被封IP
REQUEST_DELAY_MS=1000  # 请求间隔1秒
MAX_REQUESTS_PER_MINUTE=30  # 每分钟最多30次请求
```

### 2. 🛡️ 数据隐私保护
- **仅收集公开数据**：不尝试获取非公开信息
- **数据匿名化**：存储时对敏感信息进行脱敏
- **访问控制**：API接口需要认证
- **数据加密**：敏感配置信息加密存储

### 3. ⚖️ 合法合规使用
- **仅用于合法目的**：商业竞争分析、市场研究等
- **尊重知识产权**：不盗用他人内容
- **遵守法律法规**：遵守《网络安全法》等相关法律
- **用户同意**：监控的账号应为公开账号或已获授权

### 4. 🔐 安全存储配置
```bash
# 环境变量加密
# 使用 secrets manager 或加密的 .env 文件

# 数据库访问控制
POSTGRES_PASSWORD=强密码至少16位
REDIS_PASSWORD=强密码至少16位
INFLUXDB_TOKEN=随机生成的强令牌

# API认证
API_AUTH_ENABLED=true
API_JWT_SECRET=随机生成的密钥
```

### 5. 🚨 安全审计
```bash
# 定期检查日志
grep -i "error\|failed\|unauthorized" logs/app.log

# 监控异常访问
tail -f logs/access.log | grep -v "200 OK"

# 定期更新依赖
pip list --outdated
npm outdated
```

## 💻 开发指南

### 📁 项目结构
```
douyin_monitor/
├── core/                    # 核心业务模块
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库操作
│   ├── models.py           # 数据模型
│   ├── monitor.py          # 监控逻辑
│   ├── scheduler.py        # 任务调度
│   └── notifier.py         # 通知发送
├── api/                    # API服务器
│   └── server.py           # FastAPI应用
├── scripts/                # 工具脚本
│   ├── install.sh         # 安装脚本
│   ├── start.sh           # 启动脚本
│   ├── stop.sh            # 停止脚本
│   └── configure_with_cookie.sh  # Cookie配置
├── grafana/                # Grafana配置
│   └── provisioning/       # 数据源和仪表板配置
├── logs/                   # 日志目录
├── tests/                  # 测试文件
├── docker-compose.yml      # Docker编排
├── Dockerfile             # 应用镜像
├── requirements.txt       # Python依赖
├── .env.example           # 环境变量示例
└── README.md              # 项目文档
```

### 🛠️ 扩展功能

1. **新增数据源**
```python
# 在 core/monitor.py 中添加新的采集方法
def collect_from_new_source(account_id):
    """从新数据源采集数据"""
    # 实现采集逻辑
    pass

# 注册到数据采集器
DATA_COLLECTORS["new_source"] = collect_from_new_source
```

2. **新增通知渠道**
```python
# 在 core/notifier.py 中添加新通知渠道
def send_telegram_notification(message):
    """发送Telegram通知"""
    # 实现Telegram通知逻辑
    pass

# 添加到通知管理器
NOTIFICATION_CHANNELS["telegram"] = send_telegram_notification
```

3. **自定义报表**
```python
# 添加新的API端点
@app.get("/api/reports/custom")
async def get_custom_report():
    """生成自定义报表"""
    # 实现报表生成逻辑
    pass
```

### 🧪 开发环境设置
```bash
# 1. 克隆仓库
git clone https://github.com/xiaokaige1130-maker/douyin-monitor-system.git
cd douyin-monitor-system

# 2. 创建开发分支
git checkout -b feature/new-feature

# 3. 设置开发环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 启动开发服务
docker-compose -f docker-compose.dev.yml up -d

# 5. 运行测试
pytest tests/

# 6. 提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin feature/new-feature
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

```
MIT License

Copyright (c) 2024 抖音监控系统项目

Permission is hereby granted...
```

**免责声明**：本项目仅供学习和研究使用，使用者需遵守相关法律法规和平台规则。

## 🤝 支持与贡献

### 🐛 报告问题
如果您发现任何问题，请：
1. 查看 [Issues](https://github.com/xiaokaige1130-maker/douyin-monitor-system/issues) 是否已存在
2. 创建新Issue，详细描述问题
3. 提供复现步骤和环境信息

### 💡 功能建议
欢迎提出功能建议：
1. 在Issues中创建功能请求
2. 描述使用场景和预期效果
3. 讨论技术实现方案

### 🔧 贡献代码
我们欢迎Pull Request：
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

### 📚 文档改进
帮助改进文档：
1. 修正错别字和语法错误
2. 添加使用示例
3. 翻译成其他语言
4. 添加图表和示意图

## 🌟 项目状态

| 组件 | 状态 | 完成度 |
|------|------|--------|
| 核心监控 | ✅ 完成 | 100% |
| API接口 | ✅ 完成 | 100% |
| 数据存储 | ✅ 完成 | 100% |
| 通知系统 | ✅ 完成 | 100% |
| 可视化 | ⚠️ 部分 | 80% |
| 文档 | ✅ 完成 | 100% |
| 测试覆盖 | 🔄 进行中 | 60% |

## 📞 联系方式

- **GitHub**: [xiaokaige1130-maker](https://github.com/xiaokaige1130-maker)
- **项目地址**: https://github.com/xiaokaige1130-maker/douyin-monitor-system
- **问题反馈**: [Issues](https://github.com/xiaokaige1130-maker/douyin-monitor-system/issues)

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

**⚠️ 重要提示**：使用本系统请遵守抖音平台的使用条款，不要用于非法用途。合理使用，尊重他人隐私和知识产权。