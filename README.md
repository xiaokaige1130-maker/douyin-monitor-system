# douyin-monitor-system

## 项目简介

这是一个面向抖音直播监控场景的系统仓库，主要目标是持续监控目标账号的开播状态、直播时长和直播间相关数据。

如果你以后翻到这个仓库，记住一句话就够了：

> 这是你做抖音直播监控和数据采集的系统仓库。

## 当前定位

- 抖音直播监控系统
- 直播开播 / 下播状态跟踪
- 直播间数据采集与统计
- 可继续扩展为告警、报表和可视化平台

## 当前能力

- 24 小时自动监控
- 开播状态检测
- 直播时长统计
- 直播间数据采集
- 多账号监控
- Docker 化部署
- REST API
- PostgreSQL / InfluxDB / Redis 数据存储
- Grafana 可视化
- 钉钉 / 微信 / 邮件通知

## 快速开始

```bash
git clone https://github.com/xiaokaige1130-maker/douyin-monitor-system.git
cd douyin-monitor-system
cp .env.example .env
./install.sh
./start.sh
```

默认访问：`http://localhost:8000`

## 当前状态

项目已经具备“系统级监控”的基本结构，但仍然依赖实际的抖音 Cookie、接口可用性和运行环境配置。

## 一句话记忆

> 这是你用来监控抖音直播数据的项目。
