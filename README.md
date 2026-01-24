# 期货K线自动分析工具

基于 TradingAgents-CN 项目经验开发的期货K线自动分析工具，支持数据获取、技术指标计算、形态识别和可视化。

## 功能特性

### 数据获取
- 使用 akshare 获取期货历史数据
- 支持主力连续合约（rb888、au888 等）
- 自动数据清洗和标准化

### 技术指标
- **移动平均线**: MA5、MA10、MA20、MA60
- **MACD**: DIF、DEA、MACD柱状图
- **RSI**: 相对强弱指标
- **KDJ**: 随机指标
- **布林带**: 上轨、中轨、下轨

### K线形态识别
- **单根形态**: 十字星、锤子线、流星线、大阳线、大阴线等
- **双根形态**: 阳包阴、阴包阳、曙光初现、乌云盖顶
- **三根形态**: 早晨之星、黄昏之星、红三兵、三只乌鸦

### 交易信号
- 金叉/死叉检测（MA、MACD、KDJ）
- 超买/超卖检测（RSI）
- 布林带突破检测

### 分析报告
- 一句话综合分析报告
- 详细 JSON 报告文件

### 可视化
- 生成 klinecharts 兼容的数据格式
- 独立的 HTML 图表查看器
- 支持形态标注

### Web 图表应用 (klinecharts pro)
- 基于 klinecharts pro 的交互式 Web 图表
- 实时期货数据浏览
- 多周期 K 线图 (5分钟、15分钟、1小时、日线)
- 品种搜索功能
- RESTful API 接口

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- akshare - 期货数据获取
- pandas - 数据处理
- flask - Web 服务器
- pytest - 测试框架

## 使用方法

### 命令行使用

```bash
# 分析螺纹钢主力连续 (默认30天)
python main.py rb888

# 指定获取天数
python main.py rb888 -d 120

# 指定输出目录
python main.py rb888 -o my_output

# 不生成图表
python main.py rb888 --no-chart

# 不保存报告
python main.py rb888 --no-report
```

### Web 图表应用使用

启动 Web 服务器：

```bash
python chart_server.py
```

服务器将在 http://localhost:8080 启动，在浏览器中打开即可使用。

#### API 端点

**品种搜索**
```bash
# 获取所有品种
curl http://localhost:8080/api/symbols

# 搜索特定品种
curl http://localhost:8080/api/symbols?q=RB
```

**获取历史 K 线数据**
```bash
# 获取日线数据
curl "http://localhost:8080/api/history?symbol=RB2505&period=1d"

# 获取分钟数据
curl "http://localhost:8080/api/history?symbol=RB2505&period=5m"

# 指定时间范围
curl "http://localhost:8080/api/history?symbol=RB2505&period=1d&from=1704067200000&to=1735689600000"
```

#### 前端架构

- `static/index.html` - 主页面
- `static/css/chart.css` - 样式文件
- `static/js/chart.js` - AkshareDatafeed 数据适配器
- `static/js/app.js` - ChartApp 应用初始化

### 支持的期货品种

| 代码 | 名称 | 代码 | 名称 |
|------|------|------|------|
| rb888 | 螺纹钢 | au888 | 黄金 |
| hc888 | 热卷 | ag888 | 白银 |
| cu888 | 铜 | al888 | 铝 |
| zn888 | 锌 | ni888 | 镍 |
| sc888 | 原油 | fu888 | 燃料油 |
| a888 | 豆一 | m888 | 豆粕 |
| y888 | 豆油 | p888 | 棕榈油 |
| c888 | 玉米 | jd888 | 鸡蛋 |
| pp888 | PP | l888 | L |
| v888 | PVC | eg888 | 乙二醇 |
| ma888 | 甲醇 | ta888 | PTA |
| ru888 | 橡胶 | if888 | 沪深300 |

### Python API 使用

```python
from main import FuturesAnalyzer

# 创建分析器
analyzer = FuturesAnalyzer(output_dir="output")

# 执行分析
result = analyzer.analyze(
    symbol="rb888",
    days=120,
    save_chart=True,
    save_report=True
)

# 打印结果
analyzer.print_result(result)

# 获取一句话报告
print(result['one_line_report'])
```

## 输出文件

运行后会在输出目录生成以下文件：

```
output/
├── rb888_chart.html      # K线图HTML查看器（可直接在浏览器打开）
├── rb888_chart.json      # 图表数据JSON
└── rb888_report.json     # 分析报告JSON
```

## 模块说明

| 模块 | 功能 |
|------|------|
| `data_fetcher.py` | 数据获取和标准化 |
| `indicators.py` | 技术指标计算 |
| `pattern_recognizer.py` | K线形态识别 |
| `report_generator.py` | 分析报告生成 |
| `chart_visualizer.py` | 可视化数据生成 |
| `main.py` | 主程序入口 |
| `chart_server.py` | Flask Web 服务器 |
| `api/` | API 蓝图模块 |
| `api/symbols.py` | 品种搜索 API |
| `api/history.py` | 历史数据 API |
| `api/utils.py` | API 工具函数 |
| `services/cache.py` | 缓存服务 |
| `static/` | 前端静态文件 |
| `tests/` | 单元测试 |

## 测试

运行所有测试：

```bash
pytest tests/ -v
```

运行特定测试：

```bash
# 测试缓存服务
pytest tests/test_cache.py -v

# 测试 API 端点
pytest tests/test_symbols_api.py -v
pytest tests/test_history_api.py -v
```

## 分析报告示例

### 一句话报告
```
rb888价格3142.00（上涨0.58%）处于短期下跌，最新K线呈大阳线，建议观望或轻仓试空
```

### 详细报告
```json
{
  "symbol": "rb888",
  "latest_price": 3142.0,
  "price_change": 18.0,
  "trend": "短期下跌",
  "signals": {},
  "indicators": {
    "ma5": 3126.8,
    "ma10": 3144.2,
    "ma20": 3139.35,
    "rsi": 52.49,
    "macd_dif": 4.82,
    "macd_dea": 8.81
  }
}
```

## 注意事项

1. 本工具仅供学习和研究使用，不构成投资建议
2. 期货投资有风险，入市需谨慎
3. 建议结合其他分析方法综合判断
4. 数据来源：akshare（新浪财经、东方财富）
5. Web 服务器默认使用 8080 端口（避免与 macOS AirPlay 冲突）

## 项目结构

```
futures_backtest/
├── api/                    # API 蓝图模块
│   ├── __init__.py
│   ├── symbols.py          # 品种搜索 API
│   ├── history.py          # 历史数据 API
│   └── utils.py            # API 工具函数
├── services/               # 服务层
│   └── cache.py            # 缓存服务
├── static/                 # 前端静态文件
│   ├── index.html          # 主页面
│   ├── css/
│   │   └── chart.css       # 样式文件
│   └── js/
│       ├── chart.js        # Datafeed 类
│       └── app.js          # 应用初始化
├── tests/                  # 单元测试
│   ├── test_cache.py
│   ├── test_symbols_api.py
│   ├── test_history_api.py
│   └── test_utils.py
├── chart_server.py         # Flask 服务器
├── main.py                 # 主程序
└── requirements.txt        # 依赖列表
```

## 技术栈

### 后端
- Python 3.11+
- Flask - Web 框架
- akshare - 期货数据源
- pandas - 数据处理
- pytest - 测试框架

### 前端
- klinecharts pro - 专业 K 线图表库
- 原生 JavaScript (ES6+)
- CSS3 (Flexbox)

## 开发指南

### 添加新的 API 端点

1. 在 `api/` 目录创建新的蓝图文件
2. 在 `api/__init__.py` 注册蓝图
3. 在 `tests/` 添加对应测试
4. 运行测试验证功能

### 前端开发

1. 修改 `static/js/` 下的 JavaScript 文件
2. 修改 `static/css/` 下的样式文件
3. 刷新浏览器查看效果（无需构建）

## 参考项目

- [TradingAgents-CN](../TradingAgents-CN) - 指标计算逻辑参考
- [klinecharts](https://github.com/klinecharts/KLineChart) - 可视化库
- [akshare](https://github.com/akfamily/akshare) - 数据源

## License

MIT
