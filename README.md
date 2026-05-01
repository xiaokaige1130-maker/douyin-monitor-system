# 抖音同行直播监控系统

用于持续监控同行抖音直播运营数据，重点关注：

- 开播时间
- 下播时间和直播时长
- 当前/峰值/平均在线人数
- 当前/峰值/平均进店或看播人数口径
- 点赞、评论、分享
- 直播间商品快照（平台页面返回时记录）
- 同行账号排行、开播日历、近期直播复盘

## 当前定位

这是一个“同行直播运营数据采集与复盘工具”，不是单纯爬虫。它帮助你观察同行什么时候开播、播多久、直播间人气如何变化，从而反推自己的直播排班、话术节奏和运营策略。

## 关键能力

- 多同行账号监控
- 低频轮询和直播中高频采样
- 风险状态识别：登录失效、验证码、安全验证、频控
- 账号级冷却，避免失败后持续请求
- REST API 写入监控账号
- 活跃直播、近期直播、直播详情快照
- 运营总览、同行排行榜、开播日历
- Docker 化部署
- PostgreSQL / Redis / InfluxDB / Grafana 基础设施

## 快速开始

```bash
git clone https://github.com/xiaokaige1130-maker/douyin-monitor-system.git
cd douyin-monitor-system
cp .env.example .env
# 编辑 .env，填 DOUYIN_COOKIE（可选但建议）
docker-compose up -d
python main.py
```

API 默认地址：`http://localhost:8000`

## 添加同行账号

推荐优先填写 `live_url` 或 `sec_uid`，这样比只填抖音号更稳定。

```bash
curl -X POST "http://localhost:8000/api/accounts?douyin_id=competitor_001&nickname=同行A&live_url=https://www.douyin.com/user/SEC_UID&check_interval_minutes=10"
```

如果知道固定直播间 `room_id`：

```bash
curl -X POST "http://localhost:8000/api/accounts?douyin_id=competitor_002&nickname=同行B&live_room_id=123456789&check_interval_minutes=10"
```

## 常用接口

```bash
# 健康检查
curl http://localhost:8000/api/health

# 监控账号和风险状态
curl http://localhost:8000/api/accounts

# 当前正在直播的同行
curl http://localhost:8000/api/lives/active

# 最近直播记录
curl "http://localhost:8000/api/lives/recent?days=7&limit=50"

# 同行直播运营总览
curl "http://localhost:8000/api/operations/overview?days=7"

# 同行账号排行
curl "http://localhost:8000/api/operations/accounts/ranking?days=7&limit=50"

# 开播日历
curl "http://localhost:8000/api/operations/live-calendar?days=7&limit=200"
```

## 风控说明

系统只做低频访问、失败冷却、登录/验证状态识别和人工处理提示，不做验证码绕过，也不保证平台页面或接口长期稳定。出现 `verify_required`、`login_required`、`blocked` 时，账号会自动进入冷却，避免继续打请求。

建议：

- 使用专门监控账号，不使用主账号
- 单账号监控数量不要太多
- 非直播检查间隔建议 10 分钟以上
- 直播中检查间隔建议 2 分钟以上
- 出现验证后先人工处理，再清除冷却

清除冷却：

```bash
curl -X PATCH "http://localhost:8000/api/accounts/1?clear_cooldown=true"
```
