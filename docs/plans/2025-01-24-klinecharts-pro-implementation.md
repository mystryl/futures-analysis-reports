# klinecharts pro 架构重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有的 klinecharts 10.0 静态 HTML 图表重构为 klinecharts pro + Flask API 架构

**架构:** 前端使用 KLineChartPro 组件 + 自定义 Datafeed 接口，后端使用 Flask 提供 RESTful API，数据层对接 akshare 获取期货数据

**Tech Stack:** Flask, akshare, klinecharts pro, JavaScript (ES6+)

---

## Task 1: 创建项目基础结构

**Files:**
- Create: `api/__init__.py`
- Create: `services/__init__.py`
- Create: `static/js/`
- Create: `static/css/`
- Create: `tests/`
- Create: `requirements.txt`
- Create: `chart_server.py`

**Step 1: 创建目录结构**

```bash
cd /Users/mystryl/Documents/Quant/futures_backtest
mkdir -p api services static/js static/css tests
```

**Step 2: 创建 requirements.txt**

```bash
cat > requirements.txt << 'EOF'
flask>=3.0.0
akshare>=1.12.0
pandas>=2.0.0
pytest>=7.4.0
EOF
```

**Step 3: 创建 API 模块初始化文件**

```bash
cat > api/__init__.py << 'EOF'
"""API 蓝图模块"""
from flask import Blueprint

# 将在后续任务中注册蓝图
EOF
```

**Step 4: 创建服务模块初始化文件**

```bash
cat > services/__init__.py << 'EOF'
"""服务层模块"""
# 将在后续任务中添加缓存服务等
EOF
```

**Step 5: 创建空测试文件**

```bash
cat > tests/__init__.py << 'EOF'
"""测试模块"""
EOF
```

**Step 6: 安装依赖**

```bash
pip install -r requirements.txt
```

**Step 7: 验证安装**

```bash
python -c "import flask; import akshare; print('依赖安装成功')"
```

**Step 8: 提交**

```bash
git add requirements.txt api/__init__.py services/__init__.py tests/__init__.py
git commit -m "feat: 创建项目基础结构和依赖配置"
```

---

## Task 2: 实现缓存服务

**Files:**
- Create: `services/cache.py`
- Test: `tests/test_cache.py`

**Step 1: 编写缓存服务测试**

```bash
cat > tests/test_cache.py << 'EOF'
"""缓存服务测试"""
import pytest
import time
from services.cache import DataCache

def test_cache_set_and_get():
    """测试缓存写入和读取"""
    cache = DataCache(ttl_seconds=1)

    cache.set('test', {'data': 'value'}, key='123')
    result = cache.get('test', key='123')

    assert result == {'data': 'value'}

def test_cache_expiration():
    """测试缓存过期"""
    cache = DataCache(ttl_seconds=1)

    cache.set('test', {'data': 'value'}, key='exp')
    time.sleep(1.1)  # 等待过期

    result = cache.get('test', key='exp')
    assert result is None

def test_cache_miss():
    """测试缓存未命中"""
    cache = DataCache()
    result = cache.get('nonexistent', key='miss')
    assert result is None

def test_cache_clear():
    """测试清空缓存"""
    cache = DataCache()
    cache.set('test', {'data': 'value'}, key='clear')
    cache.clear()

    result = cache.get('test', key='clear')
    assert result is None
EOF
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_cache.py -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'services.cache'

**Step 3: 实现缓存服务**

```bash
cat > services/cache.py << 'EOF'
"""数据缓存服务"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """内存数据缓存"""

    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存
        ttl_seconds: 缓存过期时间（秒），默认 5 分钟
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def _generate_key(self, prefix: str, **params) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, prefix: str, **params) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(prefix, **params)
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry['expires']:
                logger.debug(f"缓存命中: {key}")
                return entry['data']
            else:
                del self._cache[key]
        return None

    def set(self, prefix: str, data: Any, **params) -> None:
        """设置缓存"""
        key = self._generate_key(prefix, **params)
        self._cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.ttl)
        }
        logger.debug(f"缓存写入: {key}")

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def cleanup(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        expired = [k for k, v in self._cache.items() if now >= v['expires']]
        for key in expired:
            del self._cache[key]
        if expired:
            logger.info(f"清理 {len(expired)} 个过期缓存")


# 全局缓存实例
cache = DataCache(ttl_seconds=300)
EOF
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_cache.py -v
```

Expected: PASS (4 passed)

**Step 5: 提交**

```bash
git add services/cache.py tests/test_cache.py
git commit -m "feat: 实现内存缓存服务 DataCache"
```

---

## Task 3: 实现错误处理工具

**Files:**
- Create: `api/utils.py`

**Step 1: 创建错误处理工具模块**

```bash
cat > api/utils.py << 'EOF'
"""API 工具模块 - 错误处理和参数验证"""
from functools import wraps
from flask import jsonify
import logging

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """API 错误基类"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload


def handle_api_error(error):
    """统一错误响应格式"""
    response = {
        'error': error.message,
        'code': error.status_code
    }
    if error.payload:
        response.update(error.payload)
    logger.error(f"API Error: {error.message}")
    return jsonify(response), error.status_code


def validate_required(params, required_fields):
    """验证必需参数"""
    missing = [f for f in required_fields if f not in params or not params[f]]
    if missing:
        raise ApiError(f"缺少必需参数: {', '.join(missing)}", 400)


def handle_akshare_error(func):
    """处理 akshare 调用异常"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise ApiError(f"数据格式错误: {str(e)}", 400)
        except ConnectionError as e:
            raise ApiError("网络连接失败，请检查网络", 503)
        except Exception as e:
            logger.exception("akshare 调用异常")
            raise ApiError(f"数据获取失败: {str(e)}", 500)
    return wrapper
EOF
```

**Step 2: 创建错误处理测试**

```bash
cat > tests/test_utils.py << 'EOF'
"""API 工具测试"""
import pytest
from api.utils import ApiError, validate_required, handle_api_error


def test_api_error_creation():
    """测试 API 错误创建"""
    error = ApiError("测试错误", 404)
    assert error.message == "测试错误"
    assert error.status_code == 404


def test_validate_required_pass():
    """测试参数验证通过"""
    params = {'symbol': 'rb2505', 'period': '1d'}
    # 不应该抛出异常
    validate_required(params, ['symbol', 'period'])


def test_validate_required_fail():
    """测试参数验证失败"""
    params = {'symbol': 'rb2505'}
    with pytest.raises(ApiError) as exc_info:
        validate_required(params, ['symbol', 'period'])

    assert '缺少必需参数' in str(exc_info.value)


def test_handle_api_error():
    """测试错误处理响应"""
    error = ApiError("未找到", 404)
    response, status = handle_api_error(error)

    assert status == 404
    # response 是 Flask Response 对象
    import json
    data = json.loads(response.get_data(as_text=True))
    assert data['error'] == "未找到"
    assert data['code'] == 404
EOF
```

**Step 3: 运行测试**

```bash
pytest tests/test_utils.py -v
```

Expected: PASS (4 passed)

**Step 4: 提交**

```bash
git add api/utils.py tests/test_utils.py
git commit -m "feat: 实现 API 错误处理和参数验证工具"
```

---

## Task 4: 实现品种搜索 API

**Files:**
- Create: `api/symbols.py`
- Modify: `api/__init__.py`
- Test: `tests/test_symbols_api.py`

**Step 1: 编写 API 测试**

```bash
cat > tests/test_symbols_api.py << 'EOF'
"""品种搜索 API 测试"""
import pytest
from chart_server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_symbols_search_no_params(client):
    """测试无参数搜索（返回所有品种）"""
    response = client.get('/api/symbols')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_symbols_search_with_query(client):
    """测试带关键词搜索"""
    response = client.get('/api/symbols?q=rb')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # 验证返回的是螺纹钢相关品种
    if len(data) > 0:
        assert 'ticker' in data[0]
        assert 'name' in data[0]


def test_symbols_missing_required_param(client):
    """测试缺少必需参数（目前 symbols 没有必需参数）"""
    # 此测试仅为演示，实际 /api/symbols 不需要参数
    pass
EOF
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_symbols_api.py -v
```

Expected: FAIL - 路由不存在

**Step 3: 实现品种搜索 API**

```bash
cat > api/symbols.py << 'EOF'
"""品种搜索 API"""
from flask import Blueprint, request, jsonify
import akshare as ak
from api.utils import handle_akshare_error

symbols_bp = Blueprint('symbols', __name__)


@symbols_bp.route('/symbols', methods=['GET'])
@handle_akshare_error
def search_symbols():
    """
    搜索期货品种
    参数: q (可选) - 搜索关键词
    返回: SymbolInfo[] 数组
    """
    query = request.args.get('q', '').strip()

    # 使用 akshare 获取期货品种列表
    # 如果没有搜索关键词，获取主要期货品种
    try:
        if query:
            df = ak.futures_sina_list(sort="symbol")
        else:
            df = ak.futures_sina_list(sort="symbol")

        symbols = []
        for _, row in df.iterrows():
            symbol_str = str(row.get('symbol', ''))
            name_str = str(row.get('name', ''))

            # 如果有搜索关键词，过滤结果
            if query and query.lower() not in symbol_str.lower() and query.lower() not in name_str.lower():
                continue

            symbols.append({
                'ticker': symbol_str,
                'name': name_str,
                'shortName': symbol_str,
                'exchange': 'SHFE',  # 默认交易所，实际应根据品种判断
                'market': 'futures',
                'priceCurrency': 'CNY',
                'type': 'future'
            })

        return jsonify(symbols)

    except Exception as e:
        # 如果 akshare 调用失败，返回空数组
        return jsonify([])
EOF
```

**Step 4: 注册蓝图**

```bash
cat > api/__init__.py << 'EOF'
"""API 蓝图模块"""
from flask import Blueprint
from api.utils import handle_api_error

# 导入蓝图
from api.symbols import symbols_bp

# 注册错误处理器
def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(symbols_bp)

    # 注册全局错误处理器
    app.register_error_handler(ApiError, handle_api_error)
EOF
```

**Step 5: 创建基础 Flask 服务器**

```bash
cat > chart_server.py << 'EOF'
"""Flask 服务器入口"""
from flask import Flask, send_from_directory
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__, static_folder='static')

# 注册 API 蓝图
from api import register_blueprints
register_blueprints(app)

# 静态文件路由
@app.route('/')
def index():
    """主页面"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """静态文件服务"""
    return send_from_directory('static', path)


if __name__ == '__main__':
    logger.info("启动 Flask 服务器: http://localhost:5000")
    app.run(port=5000, debug=True)
EOF
```

**Step 6: 运行测试**

```bash
pytest tests/test_symbols_api.py -v
```

Expected: PASS

**Step 7: 提交**

```bash
git add api/symbols.py api/__init__.py chart_server.py tests/test_symbols_api.py
git commit -m "feat: 实现品种搜索 API /api/symbols"
```

---

## Task 5: 实现历史数据 API

**Files:**
- Create: `api/history.py`
- Modify: `api/__init__.py`
- Test: `tests/test_history_api.py`

**Step 1: 编写历史数据 API 测试**

```bash
cat > tests/test_history_api.py << 'EOF'
"""历史数据 API 测试"""
import pytest
from chart_server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_history_missing_symbol(client):
    """测试缺少 symbol 参数"""
    response = client.get('/api/history?period=1d')
    assert response.status_code == 400


def test_history_with_valid_params(client):
    """测试有效参数请求"""
    response = client.get('/api/history?symbol=rb2505&period=1d')
    # 可能返回 200 (成功) 或 500 (akshare 调用失败)
    # 但不应该是 400 (参数错误)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.get_json()
        assert isinstance(data, list)
EOF
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_history_api.py -v
```

Expected: FAIL - 路由不存在

**Step 3: 实现历史数据 API**

```bash
cat > api/history.py << 'EOF'
"""历史 K 线数据 API"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import pandas as pd
from services.cache import cache
from api.utils import handle_akshare_error, validate_required, ApiError

history_bp = Blueprint('history', __name__)


def _convert_to_kline_format(df):
    """转换 DataFrame 为 klinecharts 格式"""
    kline_data = []
    for _, row in df.iterrows():
        item = {
            'timestamp': int(row['timestamp']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume'])
        }
        kline_data.append(item)
    return kline_data


@history_bp.route('/history', methods=['GET'])
@handle_akshare_error
def get_history():
    """
    获取历史 K 线数据
    参数:
        - symbol: 品种代码 (如 "rb2505")
        - period: 周期 ("5m", "15m", "1h", "1d")
        - from: 开始时间戳 (毫秒)
        - to: 结束时间戳 (毫秒)
    返回: KLineData[] 数组
    """
    params = request.args

    # 参数验证
    validate_required(params, ['symbol'])

    symbol = params.get('symbol')
    period = params.get('period', '1d')
    from_ts = int(params.get('from', 0))
    to_ts = int(params.get('to', int(datetime.now().timestamp() * 1000)))

    # 周期映射
    period_map = {
        '5m': '5',
        '15m': '15',
        '1h': '60',
        '1d': '101'
    }

    if period not in period_map:
        raise ApiError(f"不支持的周期: {period}，支持的周期: {', '.join(period_map.keys())}", 400)

    # 尝试从缓存获取
    cache_key_params = {
        'symbol': symbol,
        'period': period,
        'from': from_ts,
        'to': to_ts
    }
    cached = cache.get('history', **cache_key_params)
    if cached:
        return jsonify(cached)

    # 调用 akshare 获取数据
    import akshare as ak
    ak_period = period_map[period]

    df = ak.future_zh_hist_sina(symbol=symbol, period=ak_period)

    # 数据处理
    df['timestamp'] = pd.to_datetime(df.index)
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    # 转换时间戳
    df['timestamp'] = df['timestamp'].apply(lambda x: int(x.timestamp() * 1000))

    # 过滤时间范围
    if from_ts > 0:
        df = df[df['timestamp'] >= from_ts]
    if to_ts > 0:
        df = df[df['timestamp'] <= to_ts]

    # 转换格式
    kline_data = _convert_to_kline_format(df)

    # 写入缓存
    cache.set('history', kline_data, **cache_key_params)

    return jsonify(kline_data)
EOF
```

**Step 4: 更新 API 初始化**

```bash
cat > api/__init__.py << 'EOF'
"""API 蓝图模块"""
from flask import Blueprint
from api.utils import handle_api_error, ApiError

# 导入蓝图
from api.symbols import symbols_bp
from api.history import history_bp

# 注册错误处理器
def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(symbols_bp)
    app.register_blueprint(history_bp)

    # 注册全局错误处理器
    app.register_error_handler(ApiError, handle_api_error)
EOF
```

**Step 5: 运行测试**

```bash
pytest tests/test_history_api.py -v
```

Expected: PASS

**Step 6: 手动测试 API**

```bash
# 启动服务器（后台运行）
python chart_server.py &
SERVER_PID=$!

# 测试 API
curl -s "http://localhost:5000/api/history?symbol=rb2505&period=1d" | head -c 200

# 停止服务器
kill $SERVER_PID
```

**Step 7: 提交**

```bash
git add api/history.py api/__init__.py tests/test_history_api.py
git commit -m "feat: 实现历史 K 线数据 API /api/history"
```

---

## Task 6: 创建前端 HTML 页面

**Files:**
- Create: `static/index.html`
- Create: `static/css/chart.css`

**Step 1: 创建 HTML 页面**

```bash
cat > static/index.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>期货 K 线图表</title>
    <link rel="stylesheet" href="css/chart.css">
</head>
<body>
    <div id="app">
        <!-- 顶部导航栏 -->
        <header class="header">
            <div class="header-left">
                <h1>📈 期货分析图表</h1>
                <span class="version">klinecharts pro</span>
            </div>
            <div class="header-right">
                <div class="status-indicator" id="status">
                    <span class="status-dot"></span>
                    <span class="status-text">连接中...</span>
                </div>
            </div>
        </header>

        <!-- 错误提示 -->
        <div id="chart-error" class="error-banner" style="display: none;"></div>

        <!-- 图表容器 -->
        <main class="chart-container">
            <div id="chart"></div>
        </main>

        <!-- 加载遮罩 -->
        <div id="loading" class="loading-overlay">
            <div class="spinner"></div>
            <p>正在加载数据...</p>
        </div>
    </div>

    <!-- klinecharts pro CDN -->
    <script src="https://cdn.jsdelivr.net/npm/klinecharts@9.8.8/dist/klinecharts.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@klinecharts/pro@9.8.8/dist/klinecharts-pro.umd.js"></script>
    <script src="js/chart.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
EOF
```

**Step 2: 创建 CSS 样式**

```bash
cat > static/css/chart.css << 'EOF'
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f23;
    color: #d9d9d9;
    min-height: 100vh;
}

/* 顶部导航 */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #1a1a2e;
    border-bottom: 1px solid #2a2a3e;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header h1 {
    font-size: 18px;
    color: #e94560;
}

.version {
    font-size: 12px;
    color: #888;
    background: #2a2a3e;
    padding: 2px 8px;
    border-radius: 4px;
}

/* 状态指示器 */
.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #888;
    animation: pulse 2s infinite;
}

.status-dot.online { background: #26a69a; }
.status-dot.error { background: #ef5350; }
.status-dot.offline { background: #888; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* 图表容器 */
.chart-container {
    width: 100%;
    height: calc(100vh - 50px);
}

#chart {
    width: 100%;
    height: 100%;
}

/* 错误横幅 */
.error-banner {
    background: rgba(239, 83, 80, 0.1);
    border: 1px solid #ef5350;
    color: #ef5350;
    padding: 12px 20px;
    text-align: center;
    font-size: 14px;
}

/* 加载遮罩 */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 15, 35, 0.9);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    transition: opacity 0.3s;
}

.loading-overlay.hidden {
    opacity: 0;
    pointer-events: none;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #2a2a3e;
    border-top-color: #e94560;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-overlay p {
    margin-top: 16px;
    color: #888;
    font-size: 14px;
}
EOF
```

**Step 3: 提交**

```bash
git add static/index.html static/css/chart.css
git commit -m "feat: 创建前端 HTML 页面和样式"
```

---

## Task 7: 实现前端 Datafeed 类

**Files:**
- Create: `static/js/chart.js`

**Step 1: 创建 Datafeed 实现**

```bash
cat > static/js/chart.js << 'EOF'
/**
 * Akshare Datafeed 实现
 * 实现 klinecharts pro 的 Datafeed 接口
 */
class AkshareDatafeed {
    constructor(apiBaseUrl = '/api') {
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * 搜索期货品种
     */
    async searchSymbols(search = '') {
        const url = `${this.apiBaseUrl}/symbols?q=${encodeURIComponent(search)}`;
        return await this._fetchWithErrorHandling(url);
    }

    /**
     * 获取历史 K 线数据
     */
    async getHistoryKLineData(symbol, period, from, to) {
        const params = new URLSearchParams({
            symbol: symbol.ticker,
            period: period.text,
            from: from.toString(),
            to: to.toString()
        });

        const url = `${this.apiBaseUrl}/history?${params}`;
        return await this._fetchWithErrorHandling(url);
    }

    /**
     * 订阅实时数据 (暂不实现)
     */
    subscribe(symbol, period, callback) {
        console.log('订阅实时数据:', symbol, period);
        // TODO: 后续可添加 WebSocket 支持
    }

    /**
     * 取消订阅
     */
    unsubscribe(symbol, period) {
        console.log('取消订阅:', symbol, period);
    }

    /**
     * 带错误处理的请求
     */
    async _fetchWithErrorHandling(url, options = {}) {
        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error('Datafeed 请求失败:', error);

            // 显示错误提示
            this._showError(
                error.message.includes('网络')
                    ? '网络连接失败，请检查网络'
                    : error.message || '数据加载失败'
            );

            throw error;
        }
    }

    /**
     * 显示错误消息
     */
    _showError(message) {
        const errorEl = document.getElementById('chart-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
    }
}
EOF
```

**Step 2: 提交**

```bash
git add static/js/chart.js
git commit -m "feat: 实现 AkshareDatafeed 类"
```

---

## Task 8: 实现应用初始化

**Files:**
- Create: `static/js/app.js`

**Step 1: 创建应用初始化代码**

```bash
cat > static/js/app.js << 'EOF'
/**
 * 图表应用主类
 */
class ChartApp {
    constructor() {
        this.chart = null;
        this.loadingEl = document.getElementById('loading');
        this.errorEl = document.getElementById('chart-error');
        this.statusEl = document.getElementById('status');
    }

    async init() {
        try {
            this._showLoading('正在初始化图表...');

            // 检查 klinecharts pro 是否加载
            if (typeof klinechartspro === 'undefined') {
                throw new Error('klinecharts pro 库未加载');
            }

            // 创建图表实例
            this.chart = new klinechartspro.KLineChartPro({
                container: document.getElementById('chart'),
                symbol: {
                    ticker: 'rb2505',
                    name: '螺纹钢2505',
                    shortName: 'rb2505',
                    exchange: 'SHFE',
                    market: 'futures',
                    priceCurrency: 'CNY'
                },
                period: { multiplier: 1, timespan: 'day', text: '1d' },
                periods: [
                    { multiplier: 5, timespan: 'minute', text: '5m' },
                    { multiplier: 15, timespan: 'minute', text: '15m' },
                    { multiplier: 1, timespan: 'hour', text: '1h' },
                    { multiplier: 1, timespan: 'day', text: '1d' }
                ],
                datafeed: new AkshareDatafeed('/api'),
                mainIndicators: ['MA', 'VOL'],
                locale: 'zh-CN',
                theme: 'dark',
                styles: {
                    layout: {
                        background: { type: 'solid', color: '#0f0f23' },
                        textColor: '#d9d9d9'
                    },
                    candle: {
                        bar: {
                            upColor: '#ef5350',      // 红涨
                            downColor: '#26a69a',    // 绿跌
                            noChangeColor: '#888888'
                        }
                    }
                }
            });

            this._updateStatus('online', '已连接');
            this._hideLoading();

            console.log('✅ 图表初始化成功');

        } catch (error) {
            console.error('❌ 初始化失败:', error);
            this._showError(error.message);
            this._updateStatus('error', '连接失败');
            this._hideLoading();
        }
    }

    _showLoading(message = '加载中...') {
        if (this.loadingEl) {
            this.loadingEl.querySelector('p').textContent = message;
            this.loadingEl.classList.remove('hidden');
        }
    }

    _hideLoading() {
        if (this.loadingEl) {
            this.loadingEl.classList.add('hidden');
        }
    }

    _showError(message) {
        if (this.errorEl) {
            this.errorEl.textContent = message;
            this.errorEl.style.display = 'block';
            setTimeout(() => {
                this.errorEl.style.display = 'none';
            }, 5000);
        }
    }

    _updateStatus(status, text) {
        if (this.statusEl) {
            const dot = this.statusEl.querySelector('.status-dot');
            const statusText = this.statusEl.querySelector('.status-text');

            dot.className = `status-dot ${status}`;
            statusText.textContent = text;
        }
    }
}

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    new ChartApp().init();
});
EOF
```

**Step 2: 提交**

```bash
git add static/js/app.js
git commit -m "feat: 实现图表应用初始化逻辑"
```

---

## Task 9: 端到端测试

**Files:**
- Modify: 无

**Step 1: 启动服务器**

```bash
python chart_server.py &
SERVER_PID=$!
echo "服务器 PID: $SERVER_PID"
sleep 3
```

**Step 2: 测试 API 端点**

```bash
# 测试品种搜索
echo "=== 测试品种搜索 ==="
curl -s "http://localhost:5000/api/symbols?q=rb" | head -c 500
echo ""

# 测试历史数据
echo "=== 测试历史数据 ==="
curl -s "http://localhost:5000/api/history?symbol=rb2505&period=1d" | head -c 500
echo ""
```

**Step 3: 打开浏览器测试**

```bash
# macOS
open http://localhost:5000

# Linux
# xdg-open http://localhost:5000

# Windows
# start http://localhost:5000
```

**Step 4: 验证功能**

在浏览器中验证：
1. 页面正常加载
2. 图表显示 K 线数据
3. 周期切换工作正常
4. 无控制台错误

**Step 5: 停止服务器**

```bash
kill $SERVER_PID
echo "服务器已停止"
```

**Step 6: 提交**

```bash
git add -A
git commit -m "test: 完成端到端测试验证"
```

---

## Task 10: 清理和文档

**Files:**
- Create: `README.md`

**Step 1: 创建使用说明**

```bash
cat > README.md << 'EOF'
# 期货 K 线图表 - klinecharts pro 版

基于 klinecharts pro 和 Flask 的期货 K 线图表应用。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python chart_server.py
```

### 3. 访问应用

在浏览器中打开: http://localhost:5000

## API 接口

### 品种搜索

\`\`\`
GET /api/symbols?q={关键词}
\`\`\`

### 历史数据

\`\`\`
GET /api/history?symbol={品种代码}&period={周期}&from={开始时间}&to={结束时间}
\`\`\`

支持的周期: 5m, 15m, 1h, 1d

## 项目结构

\`\`\`
futures_backtest/
├── chart_server.py          # Flask 服务器
├── api/                     # API 模块
├── services/                # 服务层
├── static/                  # 前端文件
├── tests/                   # 测试文件
└── requirements.txt         # 依赖
\`\`\`

## 运行测试

\`\`\`bash
pytest tests/ -v
\`\`\`
EOF
```

**Step 2: 运行所有测试**

```bash
pytest tests/ -v
```

**Step 3: 最终提交**

```bash
git add README.md
git commit -m "docs: 添加项目使用说明文档"
```

**Step 4: 创建总结标签**

```bash
git tag -a v1.0.0-klinecharts-pro -m "完成 klinecharts pro 架构重构"
git push origin v1.0.0-klinecharts-pro 2>/dev/null || echo "本地标签已创建"
```

---

## 实施完成检查清单

- [ ] 所有测试通过 (`pytest tests/ -v`)
- [ ] 服务器正常启动 (`python chart_server.py`)
- [ ] API 响应正常 (`curl /api/symbols`, `curl /api/history`)
- [ ] 浏览器页面加载正常
- [ ] 图表 K 线显示正常
- [ ] 周期切换功能正常
- [ ] 所有代码已提交

---

## 后续扩展

1. **WebSocket 实时数据** - 实现 `subscribe()` 方法
2. **持久化缓存** - 使用 Redis 替代内存缓存
3. **多品种对比** - 支持同时显示多个品种
4. **报告生成** - 整合现有 `report_generator.py`
