# klinecharts pro 架构重构设计

**日期**: 2025-01-24
**作者**: Claude
**状态**: 设计完成，待实施

---

## 概述

将现有的基于 klinecharts 10.0 的静态 HTML 图表系统，重构为使用 klinecharts pro 新架构的现代化 Web 应用。核心改进包括：

1. **架构现代化** - 采用 Datafeed 接口模式，实现前后端数据层分离
2. **内建周期切换** - 使用 klinecharts pro 原生的 `periods` 配置
3. **akshare 集成** - 后端对接 akshare 获取期货数据
4. **Flask 后端** - 提供 RESTful API 支持

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器前端                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              KLineChartPro 组件                      │   │
│  │  - 内建周期切换 (periods: ['5m', '15m', '1h', '1d']) │   │
│  │  - 品种搜索框                                        │   │
│  │  - 技术指标面板                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↑↓                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         CustomDatafeed (Datafeed 接口)              │   │
│  │  - searchSymbols()     → GET  /api/symbols          │   │
│  │  - getHistoryKLineData() → GET /api/history         │   │
│  │  - subscribe()        → WS   /api/realtime          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↑↓
┌─────────────────────────────────────────────────────────────┐
│                    Flask 后端 (Python)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              路由层 (Flask Blueprints)              │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↑↓                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   服务层                             │   │
│  │  - ChartDataService: 数据缓存、格式转换              │   │
│  │  - IndicatorService: 指标计算                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↑↓                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   数据层                             │   │
│  │  - akshare: 外部 API 调用                            │   │
│  │  - 内存缓存: DataCache (5分钟TTL)                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
futures_backtest/
├── chart_server.py          # Flask 服务器入口 [新建]
├── api/
│   ├── __init__.py          # API 蓝图注册 [新建]
│   ├── symbols.py           # 品种搜索 API [新建]
│   └── history.py           # 历史数据 API [新建]
├── services/
│   ├── __init__.py          # [新建]
│   └── cache.py             # 缓存服务 [新建]
├── static/                  # [新建目录]
│   ├── index.html           # 主页面 [新建]
│   ├── js/
│   │   ├── chart.js         # Datafeed 实现 [新建]
│   │   └── app.js           # 应用初始化 [新建]
│   └── css/
│       └── chart.css        # 样式 [新建]
├── tests/                   # [新建目录]
│   └── test_api.py          # API 测试 [新建]
├── chart_visualizer.py      # 保留（用于静态导出）
├── data_fetcher.py          # 保留（复用）
├── indicators.py            # 保留（复用）
└── requirements.txt         # [新建]
```

---

## API 设计

### 1. 品种搜索 `/api/symbols`

**请求**: `GET /api/symbols?q={keyword}`

**响应**:
```json
[
  {
    "ticker": "rb2505",
    "name": "螺纹钢2505",
    "shortName": "rb2505",
    "exchange": "SHFE",
    "market": "futures",
    "priceCurrency": "CNY",
    "type": "future"
  }
]
```

**akshare 函数**: `future_search_symbol()`

---

### 2. 历史 K 线 `/api/history`

**请求**: `GET /api/history?symbol={code}&period={5m|15m|1h|1d}&from={ts}&to={ts}`

**响应**:
```json
[
  {
    "timestamp": 1737705600000,
    "open": 3200.0,
    "high": 3250.0,
    "low": 3180.0,
    "close": 3230.0,
    "volume": 123456.0
  }
]
```

**akshare 函数**: `future_zh_hist_sina()`

---

## 前端 Datafeed 接口

```javascript
class AkshareDatafeed {
    // 实现 Datafeed 接口
    async searchSymbols(search) { /* ... */ }
    async getHistoryKLineData(symbol, period, from, to) { /* ... */ }
    subscribe(symbol, period, callback) { /* TODO: WebSocket */ }
    unsubscribe(symbol, period) { /* TODO: WebSocket */ }
}
```

---

## 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 品种列表 | 1 小时 | 品种信息变化不频繁 |
| 历史日线 | 1 天 | 历史数据不变 |
| 历史分钟线 | 5 分钟 | 近期可能更新 |
| 实时行情 | 10 秒 | 需要保持新鲜度 |

---

## 错误处理

```python
class ApiError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        self.message = message
        self.status_code = status_code
        self.payload = payload
```

统一错误响应格式:
```json
{
  "error": "错误消息",
  "code": 400
}
```

---

## 周期配置

```javascript
const periods = [
    { multiplier: 5, timespan: 'minute', text: '5m' },
    { multiplier: 15, timespan: 'minute', text: '15m' },
    { multiplier: 1, timespan: 'hour', text: '1h' },
    { multiplier: 1, timespan: 'day', text: '1d' }
];
```

---

## 部署

```bash
# 安装依赖
pip install flask akshare

# 启动服务器
cd futures_backtest
python chart_server.py

# 浏览器访问
open http://localhost:5000
```

---

## 依赖

```
flask>=3.0.0
akshare>=1.12.0
pandas>=2.0.0
```

---

## 后续扩展

| 优先级 | 功能 | 说明 |
|-------|------|------|
| P0 | 基础功能 | 完成 Flask API + 前端 Datafeed |
| P1 | 实时数据 | 添加 WebSocket 支持 `/api/realtime` |
| P2 | 本地缓存 | SQLite/Redis 持久化缓存 |
| P3 | 多品种 | 支持同时查看多个品种 |
| P4 | 报告生成 | 整合现有 `report_generator.py` |

---

## 架构优势

1. **前后端分离** - Datafeed 接口使数据层完全可替换
2. **缓存优化** - 减少 akshare API 调用，提升性能
3. **内建周期切换** - 利用 klinecharts pro 原生功能
4. **易于扩展** - 模块化设计，便于添加新功能
5. **向后兼容** - 保留 `chart_visualizer.py` 用于静态导出
